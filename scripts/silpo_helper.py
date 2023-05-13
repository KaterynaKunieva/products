import asyncio
import logging
import re
from collections import namedtuple, defaultdict
from typing import List, Dict, Optional

from pydantic import parse_obj_as, BaseModel

from base_entities import CategoryInfo, ProductInfo, ShopInfo, ProducerInfo
from constants import BASE_silpo_UA_URL
from extensions import get_http_response, chunks, HttpMethod

silpo_shops = {
    "silpo": [ShopInfo(id=2043, title="silpo", location="default")]
}


class SilpotCategoryListReponse(BaseModel):
    id: int
    name: str
    slug: str
    iconPath: str
    parentId: Optional[int]


async def get_silpo_categories(shop: str, location: str) -> List[CategoryInfo]:
    shop_infos: List[ShopInfo] = list(filter(lambda x: x.location == location, silpo_shops.get(shop)))
    if shop_infos:
        shop_info = shop_infos[0]
        category_url = BASE_silpo_UA_URL
        response = await get_http_response(category_url, headers={"Accept-Language": "uk"}, payload={
            "method": "GetCategories",
            "data": {
                "merchantId": "1",
                "basketGuid": "",
                "deliveryType": "2",
                "filialId": shop_info.id
            }
        }, method=HttpMethod.Post)

        if response:
            category_response: List[SilpotCategoryListReponse] = parse_obj_as(List[SilpotCategoryListReponse],
                                                                              response.get("tree"))
            children_ids: Dict[int, List[int]] = defaultdict(list)
            category_infos: Dict[int, CategoryInfo] = {}

            for category in category_response:
                code = re.sub("-\d+$", "", category.slug)
                mapped = CategoryInfo(slug=code, id=category.id, title=category.name, image_url=category.iconPath)
                category_infos[category.id] = mapped
                if category.parentId is not None:
                    parent = category_infos.get(category.parentId)
                    if parent:
                        if parent.children is not None:
                            parent.children.append(mapped)
                        else:
                            parent.children = [mapped]
                    else:
                        children_ids[category.parentId].append(category.id)

                child_categories_ids = children_ids[category.id]

                for child_id in child_categories_ids:
                    mapped.children.append(category_infos.get(child_id))

            top_categories = list(
                map(lambda x: category_infos[x.id], filter(lambda x: x.parentId is None, category_response)))
            return top_categories
        else:
            logging.warning(f"Failed to parse categories of shop {shop}, location: {location}")
    else:
        logging.warning(f"Failed to find shop {shop}, location: {location}")


ProductListWithCategory = namedtuple('ProductListWithCategory', ['category', 'product_list'])

class ParameterInfo(BaseModel):
    key: str
    value: str
class ProductInfoSilpoResponse(BaseModel):
    name: str
    price: float
    slug: str
    unit: str
    parameters: Optional[List[ParameterInfo]]

async def get_silpo_products(shop: str, location: str, page_count: int, product_count: int) -> Dict[
    str, List[ProductInfo]]:
    shop_infos: List[ShopInfo] = list(filter(lambda x: x.location == location, silpo_shops.get(shop)))
    if not shop_infos:
        return {}

    shop_info = shop_infos[0]
    categories: List[CategoryInfo] = await get_silpo_categories(shop=shop, location=location)
    product_web_url = "https://shop.silpo.ua/product/"
    async def get_products(category: CategoryInfo):
        payload = {
            "method": "GetSimpleCatalogItems",
            "data": {
                "merchantId": 1,
                "basketGuid": "",
                "deliveryType": 2,
                "filialId": shop_info.id,
                "From": 1,
                "businessId": 1,
                "To": product_count * page_count,
                "ingredients": False,
                "categoryId": category.id,
                "sortBy": "popular-asc",
                "RangeFilters": {},
                "MultiFilters": {},
                "UniversalFilters": [],
                "CategoryFilter": [],
                "Promos": []
            }
        }

        product_url = BASE_silpo_UA_URL
        response = await get_http_response(product_url, headers={"Accept-Language": "uk"}, payload=payload,
                                           method=HttpMethod.Post)
        if response:
            shop_products: List[ProductInfoSilpoResponse] = parse_obj_as(List[ProductInfoSilpoResponse], response['items'])
            return ProductListWithCategory(category=category, product_list=[
                ProductInfo(title=product.name, category_id=category.id, price=product.price, weight=product.unit,slug=product.slug, web_url=product_web_url+product.slug, producer=ProducerInfo(trademark=list(filter(lambda x: x.key == "trademark", product.parameters))[0].value if product.parameters and list(filter(lambda x: x.key == "trademark", product.parameters)) else None))
                for product in shop_products
            ])
        else:
            logging.warning(f"Failed to parse products of category {category} of shop {shop}, location: {location}")
            return None

    results: Dict[str, List[ProductInfo]] = defaultdict(list)

    def get_categories(category: CategoryInfo):
        categories = []
        if category.children:
            for child in category.children:
                categories.extend(get_categories(child))
        else:
            categories.append(category)

        return categories

    scrape_args = []

    categories_ids = set()
    for category in categories:
        for cat in get_categories(category):
            if cat.id not in categories_ids:
                categories_ids.add(cat.id)
                scrape_args.append(cat)

    total_tasks = len(scrape_args)
    print(f"Total amount of scrape tasks: {total_tasks}")
    completed_tasks = 0
    for args in chunks(scrape_args, 30):
        for item in await asyncio.gather(
                *[asyncio.create_task(get_products(arg)) for arg in args]):
            item: ProductListWithCategory
            results[item.category.slug].extend(item.product_list)
            completed_tasks += 1
        print(f"Completed {round(completed_tasks / total_tasks * 100)}% of tasks")
        await asyncio.sleep(2.5)

    return results
