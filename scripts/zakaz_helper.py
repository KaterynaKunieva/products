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


async def get_zakaz_categories(shop: str, location: str, popular: bool = False) -> List[CategoryInfo]:
    shop_infos: List[ShopInfo] = list(filter(lambda x: x.location == location, zakaz_shops.get(shop)))
    if shop_infos:
        shop_info = shop_infos[0]
        category_url = f"{BASE_ZAKAZ_UA_URL}/{shop_info.id}/categories/{'popular' if popular else ''}"
        response = await get_http_response(category_url, headers={"Accept-Language": "uk"})
        if response:
            categories: List[CategoryInfo] = parse_obj_as(List[CategoryInfo], response)
            for category in categories:
                category.slug = category.slug or category.id
            return categories
        else:
            logging.warning(f"Failed to parse categories of shop {shop}, location: {location}")
    else:
        logging.warning(f"Failed to find shop {shop}, location: {location}")


ProductListWithCategory = namedtuple('ProductListWithCategory', ['category', 'product_list'])

async def get_zakaz_products(shop: str, location: str, page_count: int, product_count: int) -> Dict[str, List[ProductInfo]]:
    shop_infos: List[ShopInfo] = list(filter(lambda x: x.location == location, zakaz_shops.get(shop)))
    if not shop_infos:
        return {}

    shop_info = shop_infos[0]
    categories: List[CategoryInfo] = await get_zakaz_categories(shop=shop, location=location, popular=False)

    async def get_page_products(page: int, category: CategoryInfo):
        params = {'page': page, 'per_page': str(product_count)}


        product_url = f"{BASE_ZAKAZ_UA_URL}/{shop_info.id}/categories/{category.id}/products/"
        response = await get_http_response(product_url, headers={"Accept-Language": "uk"}, params=params)
        if response:
            shop_products: List[ProductInfo] = parse_obj_as(List[ProductInfo], response['results'])
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
    for args in chunks(scrape_args, 15):
        for item in await asyncio.gather(*[asyncio.create_task(get_page_products(arg.get("page"), arg.get("category"))) for arg in args]):
            item: ProductListWithCategory
            results[item.category.id].extend(item.product_list)
            completed_tasks += 1
        print(f"Completed {round(completed_tasks/total_tasks * 100)}% of tasks")
        await asyncio.sleep(2.5)

    return results

