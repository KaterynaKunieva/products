import asyncio
import logging
from collections import namedtuple, defaultdict
from typing import List, Dict, Optional

import datefinder
from pydantic import parse_obj_as, BaseModel

from base_entities import CategoryInfo, ProductInfo, PromoInfo
from constants import BASE_ZAKAZ_UA_URL
from extensions import get_http_response, chunks
from helpers import ShopScrapperService
from zakaz_shops import zakaz_shops, ShopInfo

ProductListWithCategory = namedtuple('ProductListWithCategory', ['category', 'product_list'])

class PromotionCategory(BaseModel):
    name: str
    value: Optional[str]
    query: Optional[str]
class PromotionCategoriesResponse(BaseModel):
    options: List[PromotionCategory]

class DiscounInfo(BaseModel):
    old_price: float
    due_date: Optional[str]
class PromoProductInfo(ProductInfo):
    discount: Optional[DiscounInfo]

class ZakazoShopScrapperService(ShopScrapperService):
    async def get_categories(self, shop: str, location: str, popular: bool = False) -> List[CategoryInfo]:
        shop_infos: List[ShopInfo] = list(filter(lambda x: x.location == location, zakaz_shops.get(shop)))
        if shop_infos:
            shop_info = shop_infos[0]
            category_url = f"{BASE_ZAKAZ_UA_URL}/{shop_info.id}/categories/{'popular' if popular else ''}"
            response = await get_http_response(category_url, headers={"Accept-Language": "uk"})
            if response:
                categories: List[CategoryInfo] = parse_obj_as(List[CategoryInfo], response)

                def set_slug(category_list: List[CategoryInfo]):
                    for category in category_list:
                        category.slug = category.slug or category.id
                        if category.children:
                            set_slug(category.children)

                set_slug(category_list=categories)
                return categories
            else:
                logging.warning(f"Failed to parse categories of shop {shop}, location: {location}")
        else:
            logging.warning(f"Failed to find shop {shop}, location: {location}")

    async def get_products(self, shop: str, location: str, page_count: int, per_page_product_count: int) -> Dict[
        str, List[ProductInfo]]:
        shop_infos: List[ShopInfo] = list(filter(lambda x: x.location == location, zakaz_shops.get(shop)))
        if not shop_infos:
            return {}

        shop_info = shop_infos[0]
        categories: List[CategoryInfo] = await self.get_categories(shop=shop, location=location, popular=False)

        async def get_page_products(page: int, category: CategoryInfo):
            params = {'page': page, 'per_page': str(per_page_product_count)}

            product_url = f"{BASE_ZAKAZ_UA_URL}/{shop_info.id}/categories/{category.id}/products/"
            response = await get_http_response(product_url, headers={"Accept-Language": "uk"}, params=params)
            if response:
                shop_products: List[ProductInfo] = parse_obj_as(List[ProductInfo], response['results'])
                for product in shop_products:
                    product.price /= 100
                return ProductListWithCategory(category=category, product_list=shop_products)
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
        categories_flat = list()
        for category in categories:
            for cat in get_categories(category):
                if cat.id not in categories_ids:
                    categories_ids.add(cat.id)
                    categories_flat.append(cat)

        for page in range(1, page_count + 1):
            for cat in list(categories_flat):
                scrape_args.append({"page": page, "category": cat})

        total_tasks = len(scrape_args)
        print(f"Total amount of scrape tasks: {total_tasks},  categories: {len(categories_flat)}")
        completed_tasks = 0
        for args in chunks(scrape_args, 10):
            for item in await asyncio.gather(
                    *[asyncio.create_task(get_page_products(arg.get("page"), arg.get("category"))) for arg in args]):
                item: ProductListWithCategory
                results[item.category.id].extend(item.product_list)
                completed_tasks += 1
            print(f"Completed {round(completed_tasks / total_tasks * 100)}% of tasks")
            await asyncio.sleep(2.5)

        return results

    async def get_promotion_categories(self, shop: str, location: str) -> List[CategoryInfo]:
        shop_infos: List[ShopInfo] = list(filter(lambda x: x.location == location, zakaz_shops.get(shop)))
        categories_keys = ['category_id',  "category-id"]
        if shop_infos:
            shop_info = shop_infos[0]
            category_url = f"{BASE_ZAKAZ_UA_URL}/{shop_info.id}/products/promotion/"
            response = await get_http_response(category_url, headers={"Accept-Language": "uk"})
            if response:
                categories: List[PromotionCategory] = PromotionCategoriesResponse.parse_obj(
                    list(filter(lambda r: r.get("key") in categories_keys or r.get("type") in categories_keys, response.get("filters")))[0]).options

                mapped_categories: List[CategoryInfo] = [CategoryInfo(id=category.value or category.query, title=category.name) for category in categories]
                def set_slug(category_list: List[CategoryInfo]):
                    for category in category_list:
                        category.slug = category.slug or category.id
                        if category.children:
                            set_slug(category.children)

                set_slug(category_list=mapped_categories)
                return mapped_categories
            else:
                logging.warning(f"Failed to parse categories of shop {shop}, location: {location}")
        else:
            logging.warning(f"Failed to find shop {shop}, location: {location}")

    async def get_promotion_products(self, shop: str, location: str, page_count: int, per_page_product_count: int) -> Dict[
        str, List[ProductInfo]]:
        shop_infos: List[ShopInfo] = list(filter(lambda x: x.location == location, zakaz_shops.get(shop)))
        if not shop_infos:
            return {}

        shop_info = shop_infos[0]
        categories: List[CategoryInfo] = await self.get_promotion_categories(shop=shop, location=location)

        async def get_page_products(category: CategoryInfo):
            params = {'category-id': category.id}

            product_url = f"{BASE_ZAKAZ_UA_URL}/{shop_info.id}/products/promotion/"
            response = await get_http_response(product_url, headers={"Accept-Language": "uk"}, params=params)
            if response:
                shop_products: List[PromoProductInfo] = parse_obj_as(List[PromoProductInfo], response['results'])
                mapped_products = []
                for product in shop_products:
                    product.price /= 100
                    old_price = product.discount.old_price / 100
                    due_date = list(datefinder.find_dates(product.discount.due_date))[0] if product.discount.due_date else None
                    mapped_product = ProductInfo.parse_obj(product.dict())

                    mapped_product.promotion = PromoInfo(stop_date=due_date, old_price=old_price)
                    mapped_products.append(mapped_product)

                return ProductListWithCategory(category=category, product_list=mapped_products)
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
        categories_flat = list()
        for category in categories:
            for cat in get_categories(category):
                if cat.id not in categories_ids:
                    categories_ids.add(cat.id)
                    categories_flat.append(cat)

        for cat in list(categories_flat):
            scrape_args.append({"category": cat})

        total_tasks = len(scrape_args)
        print(f"Total amount of scrape tasks: {total_tasks},  categories: {len(categories_flat)}")
        completed_tasks = 0
        for args in chunks(scrape_args, 15):
            for item in await asyncio.gather(
                    *[asyncio.create_task(get_page_products(arg.get("category"))) for arg in args]):
                item: ProductListWithCategory
                results[item.category.id].extend(item.product_list)
                completed_tasks += 1
            print(f"Completed {round(completed_tasks / total_tasks * 100)}% of tasks")
            await asyncio.sleep(2.5)

        return results

