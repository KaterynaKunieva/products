import logging
from typing import List

import aiohttp
from pydantic import parse_obj_as, parse_raw_as, parse_file_as

from base_entities import CategoryInfo, ProductInfo
from extensions import get_http_response
from zakaz_shops import shops, ShopInfo
from constants import BASE_ZAKAZ_UA_URL


async def get_categories(shop: str, popular: bool) -> List[CategoryInfo]:
    shop_info: ShopInfo = shops.get(shop)
    category_url = f"{BASE_ZAKAZ_UA_URL}/{shop_info.id}/categories{'popular' if popular else ''}"
    response = await get_http_response(category_url, headers={"Accept-Language": "uk"})
    if response:
        categories: List[CategoryInfo] = parse_obj_as(List[CategoryInfo], response)

        return categories
    else:
        logging.warning(f"Failed to parse categories of shop {shop}")


async def get_products(shop: str, product_count: int) -> List[ProductInfo]:

    # надо проверять чтоб колво не было больше чем всего?

    shop_info: ShopInfo = shops.get(shop)
    params = {'page': 1, 'per_page': product_count}
    categories = get_categories(shop=shop, popular=False)  # или параметр с категорией
    for category in categories:
        product_url = f"{BASE_ZAKAZ_UA_URL}/{shop_info.id}/categories/{category}/products/"
        response = await get_http_response(product_url, headers={"Accept-Language": "uk"}, params=params)

        if response:
            products: List[ProductInfo] = parse_obj_as(List[ProductInfo], response)
            return products

        else:
            logging.warning(f"Failed to parse products of category {category} of shop {shop}")

