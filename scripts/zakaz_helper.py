import asyncio
import logging
from collections import namedtuple, defaultdict
from typing import List, Dict
import json

import aiohttp
from pydantic import parse_obj_as, parse_raw_as, parse_file_as

from base_entities import CategoryInfo, ProductInfo
from extensions import get_http_response, chunks
from zakaz_shops import zakaz_shops, ShopInfo
from constants import BASE_ZAKAZ_UA_URL


async def get_zakaz_categories(shop: str, popular: bool) -> List[CategoryInfo]:
    shop_info: ShopInfo = zakaz_shops.get(shop)
    category_url = f"{BASE_ZAKAZ_UA_URL}/{shop_info.id}/categories/{'popular' if popular else ''}"
    response = await get_http_response(category_url, headers={"Accept-Language": "uk"})
    if response:
        categories: List[CategoryInfo] = parse_obj_as(List[CategoryInfo], response)

        return categories
    else:
        logging.warning(f"Failed to parse categories of shop {shop}")


ProductListWithCategory = namedtuple('ProductListWithCategory', ['category', 'product_list'])

async def get_zakaz_products(shop: str, page_count: int, product_count: int) -> Dict[str, List[ProductInfo]]:
    shop_info: ShopInfo = zakaz_shops.get(shop)
    if not shop_info:
        return {}

    categories: List[CategoryInfo] = await get_zakaz_categories(shop=shop, popular=False)

    async def get_page_products(page: int, category: CategoryInfo):
        params = {'page': page, 'per_page': str(product_count)}


        product_url = f"{BASE_ZAKAZ_UA_URL}/{shop_info.id}/categories/{category.id}/products/"
        response = await get_http_response(product_url, headers={"Accept-Language": "uk"}, params=params)
        if response:
            shop_products: List[ProductInfo] = parse_obj_as(List[ProductInfo], response['results'])
            return ProductListWithCategory(category=category, product_list=shop_products)
        else:
            logging.warning(f"Failed to parse products of category {category} of shop {shop}")
            return None

    results: Dict[str, List[ProductInfo]] = defaultdict(list)
    scrape_args = [{"page": page, "category": category} for page in range(1, page_count) for category in categories]
    total_tasks = len(scrape_args)
    completed_tasks = 0
    for args in chunks(scrape_args, 50):
        for item in await asyncio.gather(*[asyncio.create_task(get_page_products(arg.get("page"), arg.get("category"))) for arg in args]):
            item : ProductListWithCategory
            results[item.category.id].extend(item.product_list)
            completed_tasks += 1
        print(f"Completed {round(completed_tasks/total_tasks * 100)}% of tasks")
        await asyncio.sleep(1)

    return results

