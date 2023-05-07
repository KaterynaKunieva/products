import asyncio
import logging
from collections import namedtuple, defaultdict
from typing import List, Dict, Optional

from pydantic import parse_obj_as, BaseModel

from base_entities import CategoryInfo, ProductInfo, ShopInfo
from constants import BASE_silpo_UA_URL
from extensions import get_http_response, chunks, HttpMethod

silpo_shops = {
    "silpo": [ShopInfo(id=2043, location="default")]
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
            category_response: List[SilpotCategoryListReponse] = parse_obj_as(List[SilpotCategoryListReponse], response.get("tree"))
            children_ids: Dict[int, List[int]] = defaultdict(list)
            category_infos: Dict[int, CategoryInfo] = {}

            for category in category_response:
                code = category.slug
                mapped = CategoryInfo(id=code, title=category.name, image_url=category.iconPath)
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

            top_categories = list(map(lambda x: category_infos[x.id], filter(lambda x: x.parentId is None, category_response)))
            return top_categories
        else:
            logging.warning(f"Failed to parse categories of shop {shop}, location: {location}")
    else:
        logging.warning(f"Failed to find shop {shop}, location: {location}")


ProductListWithCategory = namedtuple('ProductListWithCategory', ['category', 'product_list'])

async def get_silpo_products(shop: str, location: str, page_count:int, product_count: int) -> Dict[str, List[ProductInfo]]:
    shop_infos: List[ShopInfo] = list(filter(lambda x: x.location == location, silpo_shops.get(shop)))
    if not shop_infos:
        return {}

    shop_info = shop_infos[0]
    categories: List[CategoryInfo] = await get_silpo_categories(shop=shop, location=location)

    async def get_page_products(page: int, category: CategoryInfo):
        params = {
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


        product_url = f"{BASE_silpo_UA_URL}/{shop_info.id}/categories/{category.id}/products/"
        response = await get_http_response(product_url, headers={"Accept-Language": "uk"}, params=params)
        if response:
            shop_products: List[ProductInfo] = parse_obj_as(List[ProductInfo], response['results'])
            return ProductListWithCategory(category=category, product_list=shop_products)
        else:
            logging.warning(f"Failed to parse products of category {category} of shop {shop}, location: {location}")
            return None

    results: Dict[str, List[ProductInfo]] = defaultdict(list)
    scrape_args = [{"page": page, "category": category} for page in range(1, page_count) for category in categories]
    total_tasks = len(scrape_args)
    completed_tasks = 0
    for args in chunks(scrape_args, 50):
        for item in await asyncio.gather(*[asyncio.create_task(get_page_products(arg.get("page"), arg.get("category"))) for arg in args]):
            item: ProductListWithCategory
            results[item.category.id].extend(item.product_list)
            completed_tasks += 1
        print(f"Completed {round(completed_tasks/total_tasks * 100)}% of tasks")
        await asyncio.sleep(1)

    return results