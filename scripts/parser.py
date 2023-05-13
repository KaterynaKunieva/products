import asyncio
import json
import logging
import os
import re
from collections import defaultdict
from itertools import groupby
from typing import List, Dict, Set, Any, Tuple
import functools as ft
import click
from constants import STORE_INFO_PATH
from base_entities import CategoryInfo, ProductInfo, UserBuyRequest, BuyPreference, ProductsRequest, ProductsShop, \
    ShopLocationPreference, WeightInfo
from silpo_helper import silpo_shops, get_silpo_categories, get_silpo_products
from zakaz_helper import get_zakaz_categories, get_zakaz_products
from pydantic import parse_obj_as, parse_raw_as, parse_file_as, BaseModel
from zakaz_shops import zakaz_shops
from pathlib import Path

file_open_settings = {"encoding": 'utf-8'}
json_write_settings = {"ensure_ascii": False, "indent": 2}

curr_dir = os.path.dirname(__file__)
datat_dir = os.path.join(curr_dir, STORE_INFO_PATH)
Path(datat_dir).mkdir(parents=True, exist_ok=True)


def async_cmd(func):  # to do, write your function decorator
    @ft.wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


def try_create_shop_dir(shop: str, shop_location: str = None):
    shop_dir = os.path.join(datat_dir, shop, shop_location or "")
    Path(shop_dir).mkdir(parents=True, exist_ok=True)
    return shop_dir


json_handler = logging.StreamHandler()
logging.basicConfig(level='DEBUG', handlers=[json_handler])


@click.group()
def cli():
    pass


@cli.command()
def get_shops():
    print(f"Available shops: {', '.join(list(zakaz_shops.keys()))}")


def load_categories_from_file_or_cache(shop: str, is_popular: bool):
    pass


def normalize_title(product_title: str, product_brand: str = ""):
    try:
        product_key = product_title.lower()
        regexp_brand = product_brand.lower() if product_brand else ''
        regexp_amount = "(?<=\s)\d+(,?\d+|.?\d+)*[a-zа-яЇїІіЄєҐґ]+"
        regexp_percentage = "(?<=\s)\d+(,\d+|.\d+)*\s*%"
        regexp_number = "№\d*"
        regexp_symbols = "[®]+"
        regexp_quotes = "['\"‘’«»”„]"  # delete only symbols
        regexp_brackets = "[()\[\]{}]*"  # delete only symbols
        # regexp_quotes = "['\"‘’«»”„].*['\"‘’«»”„]" # delete all inside
        # regexp_brackets = "\(.*\)|\[.*\]|\{.*\}" # delete all inside

        amount = re.search(regexp_amount, product_key, flags=re.IGNORECASE)
        percentages = re.search(regexp_percentage, product_key, flags=re.IGNORECASE)
        number = re.search(regexp_number, product_key, flags=re.IGNORECASE)

        if amount is not None:
            amount = amount.group().strip()
            product_key = product_key.replace(amount, '')
        if percentages is not None:
            percentages = percentages.group().strip()
            product_key = product_key.replace(percentages, '')
        if number is not None:
            number = number.group().strip()
            product_key = product_key.replace(number, '')

        product_key = product_key.replace(regexp_brand, '')

        product_key = re.sub(regexp_symbols, '', product_key, flags=re.IGNORECASE)
        product_key = re.sub(regexp_quotes, '', product_key, flags=re.IGNORECASE)
        product_key = re.sub(regexp_brackets, '', product_key, flags=re.IGNORECASE)
        product_key = re.sub(' {2,}', ' ', product_key, flags=re.IGNORECASE)

        return product_key.strip()
    except Exception as ex:
        logging.error(f'Failed to normalized {product_title}, {product_brand}', exc_info=ex)
        return product_title


def normalize_weight(weight) -> WeightInfo:
    if not weight or weight == 0 or weight == "0":
        weight_value = 1
        weight_unit = ''
    else:
        weight_value = re.search("\d+(,?\d+|.?\d+)*", weight)
        weight_unit = re.search("[a-zа-яЇїІіЄєҐґ]+", weight)
        if weight_value:
            weight_value = weight_value.group()
            weight_value = weight_value.replace(',', '.')
            try:
                weight_value = float(weight_value)
            except Exception as ex:
                weight_value = eval(weight_value)
        else:
            weight_value = 1
        if weight_unit:
            weight_unit = weight_unit.group()
        else:
            weight_unit = ''
        if weight_unit == 'л':
            weight_value *= 1000
            weight_unit = 'мл'
        elif weight_unit == 'кг':
            weight_value *= 1000
            weight_unit = 'г'
    return WeightInfo(weight=weight_value, unit=weight_unit)


shop_infos = {**zakaz_shops, **silpo_shops}

allowed_shops = list(shop_infos.keys())


def get_shop_locations(shop: str) -> List[str]:
    return [shopinfo.location for shopinfo in shop_infos.get(shop)]


@cli.command()
@async_cmd
@click.option('--shops', default="таврія", type=str, help='list of shop categories.')
@click.option('--locations', default="all", type=str, help='list of locations.')
@click.option('--popular', default=False, type=bool, help='return popular categories or no.')
@click.option('--force_reload', default=True, type=bool, help='force data download no matter cache exists.')
async def parse_categories(shops, locations, popular, force_reload):
    shop_list = list(zakaz_shops.keys()) if not shops or shops == "all" else shops.split(",")
    input_locations = locations.splt(",") if locations and locations != "all" else []

    for shop_key in shop_list:
        logging.info(f"Started scanning for {shop_key} categories, popular: {popular}")

        shop_location_list = get_shop_locations(shop_key) if not input_locations else list(
            filter(lambda shop: shop.location in input_locations, get_shop_locations(shop_key)))

        if shop_location_list:
            for shop_location in shop_location_list:
                shop_full_name = f"{shop_key}_{shop_location}"
                shop_dir = try_create_shop_dir(shop_key, shop_location)

                raw_category_file_path = os.path.join(shop_dir,
                                                      f"raw_categories_info{'popular' if popular else ''}.json")
                categories_hierarchy_file_path = os.path.join(shop_dir,
                                                              f"categories_hierarchy{'popular' if popular else ''}.json")
                categories_cached = os.path.exists(raw_category_file_path) and os.stat(
                    raw_category_file_path).st_size > 5 and os.path.exists(categories_hierarchy_file_path)

                categories: List[CategoryInfo] = []
                if not categories_cached or force_reload:
                    categories = await get_zakaz_categories(shop_key, shop_location, popular) if shop_key in list(
                        zakaz_shops.keys()) else await get_silpo_categories(shop_key, location=shop_location)
                else:
                    logging.info(f"Retrieving {shop_full_name} categories from path: {raw_category_file_path}")
                    categories = parse_file_as(List[CategoryInfo], raw_category_file_path)
                if categories:
                    print(f"Available categories for {shop_full_name}, count: {len(categories)}")
                    if not categories_cached or force_reload:
                        logging.info(f"Saving categories to {raw_category_file_path}")
                        with open(raw_category_file_path, "w+", **file_open_settings) as f:
                            json.dump([category.dict() for category in categories], f, **json_write_settings)
                        category_hierarchy = {category.slug: category.dict() for category in categories}

                        with open(categories_hierarchy_file_path, "w+", **file_open_settings) as f:
                            json.dump(category_hierarchy, f, **json_write_settings)
        else:
            logging.debug(f"No shop infos found for shop '{shop_key}', locations: {locations}'")


@cli.command()
@async_cmd
@click.option('--shops', default="silpo", type=str, help='list of shops.')
@click.option('--locations', default="all", type=str, help='list of locations.')
@click.option('--page_count', default=1, help='number of pages_count to scrape from shops.')
@click.option('--product_count', default=100, help='number of products to scrape from shops.')
@click.option('--force_reload', default=True, help='force data download no matter cache exists.')
async def parse_shop_products(shops, locations, page_count, product_count, force_reload):
    shop_list = []
    if not shops or shops == "all":
        shop_list = allowed_shops
    else:
        for shop_key in shops.split(","):
            shop_list.append(shop_key)

    input_locations = locations.splt(",") if locations and locations != "all" else []
    for shop_key in shop_list:
        shop_key: str
        logging.info(f"Started scanning for {shop_key} products")

        shop_location_list = get_shop_locations(shop_key) if not input_locations else list(
            filter(lambda shop: shop.location in input_locations, get_shop_locations(shop_key)))

        if shop_location_list:
            for shop_location in shop_location_list:
                shop_full_name = f"{shop_key}_{shop_location}"
                shop_dir = try_create_shop_dir(shop_key, shop_location)

                raw_product_path = os.path.join(shop_dir, f"raw_products_info.json")
                products_cached = os.path.exists(raw_product_path) and os.stat(raw_product_path).st_size > 5
                category_products: Dict[str, List[ProductInfo]] = {}

                if not products_cached or force_reload:
                    category_products = await get_zakaz_products(shop_key, shop_location, page_count,
                                                                 product_count) if shop_key in list(
                        zakaz_shops.keys()) else await get_silpo_products(shop_key, shop_location, page_count,
                                                                          product_count)
                else:
                    logging.info(f"Retrieving '{shop_full_name}' products from path: {raw_product_path}")
                    category_products = parse_file_as(Dict[str, List[ProductInfo]], raw_product_path)
                if category_products:
                    for category, products in category_products.items():
                        for product in products:
                            product: ProductInfo
                            product.normalized_title = normalize_title(product_title=product.title,
                                                                       product_brand=product.producer.trademark)
                            product.weight_info = normalize_weight(product.weight)
                    print(f"Available products for '{shop_full_name}', categories count: {len(category_products)}")
                    if not products_cached or force_reload:
                        logging.info(f"Saving raw products to {raw_product_path}")

                        with open(raw_product_path, 'w+', **file_open_settings) as f:
                            json.dump(
                                {category_id: [product.dict() for product in product_list] for category_id, product_list
                                 in
                                 category_products.items()}, f, **json_write_settings)
                        product_categories: Dict[str, List[str]] = defaultdict(list)
                        for category_id, products in category_products.items():
                            products: List[ProductInfo]
                            path_to_category = os.path.join(shop_dir, category_id)
                            if not os.path.exists(path_to_category):
                                os.mkdir(path_to_category)

                            with open(os.path.join(path_to_category, 'normalized_products.json'), 'w+',
                                      **file_open_settings) as f:
                                json.dump({product.normalized_title: product.dict() for product in products}, f,
                                          **json_write_settings)

                            with open(os.path.join(path_to_category, 'normalized_products_list.json'), 'w+',
                                      **file_open_settings) as f:
                                json.dump(sorted([product.normalized_title for product in products]), f,
                                          **json_write_settings)

                            with open(os.path.join(path_to_category, 'products_list.json'), 'w+',
                                      **file_open_settings) as f:
                                json.dump(sorted([product.title for product in products]), f, **json_write_settings)

                            with open(os.path.join(path_to_category, 'brand_list.json'), 'w+',
                                      **file_open_settings) as f:
                                json.dump(list(
                                    set([product.producer.trademark for product in products if
                                         product.producer.trademark])), f,
                                    **json_write_settings)

                            brand_products: Dict[str, Set[str]] = defaultdict(set)
                            product_brands: Dict[str, Set[str]] = defaultdict(set)
                            for product in products:
                                # normalize
                                if product.producer.trademark:
                                    brand_products[product.producer.trademark].add(product.normalized_title)
                                    product_brands[product.normalized_title].add(product.producer.trademark)
                                product_categories[product.normalized_title].append(category_id)

                            with open(os.path.join(path_to_category, 'brand_products.json'), 'w+',
                                      **file_open_settings) as f:
                                json.dump({k: list(v) for k, v in brand_products.items()}, f, **json_write_settings)

                            with open(os.path.join(path_to_category, 'product_brands.json'), 'w+',
                                      **file_open_settings) as f:
                                json.dump({k: list(v) for k, v in product_brands.items()}, f, **json_write_settings)

                        with open(os.path.join(shop_dir, 'products_categories.json'), 'w+',
                                  **file_open_settings) as f:
                            json.dump(product_categories, f,
                                      **json_write_settings)
            else:
                logging.debug(f"No shop infos found for shop '{shop_key}', locations: {locations}'")


def sort_products_by_price(
        product_element: ProductInfo) -> float:  # create function that accepts weight:str argument and returns WeigtInfo and using this new function in function sort_products_by_price(that is below)
    try:
        weight = product_element.weight_info.weight
        price = product_element.price
        return price / weight
    except Exception as ex:
        logging.error("Sorting of product by price failed", exc_info=ex)
    return 0


@cli.command()
@async_cmd
@click.option('--input_file_path', default="./user_buy_request_path.json", type=str, help='list of shops.')
# @click.option('--output_file_path', default="./output.json", type=str, help='list of shops.')
async def form_buy_list(input_file_path):
    user_query: UserBuyRequest = parse_file_as(UserBuyRequest, input_file_path)
    if user_query:
        print('Stored user_query')
    buy_list: List[BuyPreference] = user_query.buy_list
    base_path = os.path.join(os.path.dirname(__file__), STORE_INFO_PATH)  # path to data
    file_navigator = os.path.join('default', 'products_categories.json')
    file_product_info = "normalized_products.json"

    user_basket: Dict[str, List[ProductsRequest]] = defaultdict(list)

    for buy_preference in buy_list:
        paths_to_shops = []
        paths_to_navigators = []
        for shop in buy_preference.shop_filter:
            products_in_request: List[ProductsRequest] = []
            print(f'Started scanning shop {shop} for buy_preference')
            products = []
            path_to_shop = os.path.join(base_path, shop)
            path_to_navigator = os.path.join(path_to_shop, file_navigator)

            paths_to_shops.append(path_to_shop)
            paths_to_navigators.append(path_to_navigator)
            examined_categories = set()

            # find category of buy_preference
            file_navigation = parse_file_as(Dict[str, List[str]], path_to_navigator)
            for product_key in list(file_navigation.keys()):
                for path_to_category in file_navigation[product_key]:
                    if buy_preference.title_filter + " " in product_key and path_to_category not in examined_categories:
                        logging.debug(f"Scanning products of category {path_to_category}")
                        examined_categories.add(path_to_category)
                        product_location = os.path.join(path_to_shop, 'default', path_to_category, file_product_info)

                        # find buy_preference in category
                        file_info: Dict[str, ProductInfo] = parse_file_as(Dict[str, ProductInfo], product_location)
                        for title_key, product_item in list(file_info.items()):
                            product_item: ProductInfo
                            if buy_preference.title_filter + " " in title_key:
                                if (buy_preference.brand_filter is None
                                    or buy_preference.brand_filter == ""
                                    or product_item.producer.trademark is None
                                    or product_item.producer.trademark == "") \
                                        and product_item not in products:
                                    products.append(product_item)
                                else:
                                    for brand in buy_preference.brand_filter:
                                        if brand in product_item.producer.trademark and product_item not in products:
                                            products.append(product_item)
            products_in_request.append(ProductsRequest(request=buy_preference, products=products))
            user_basket[shop].extend(products_in_request)

    logging.info("Saving results...")
    for shop, product_requests in user_basket.items():
        with open(f'output_{shop}.json', 'w', **file_open_settings) as f:
            json.dump([product_request.dict() for product_request in product_requests], f, **json_write_settings)

    for shop, product_requests in user_basket.items():
        sum_price = 0
        for product_request in product_requests:
            product_request.products.sort(key=sort_products_by_price)
            product_request.products = product_request.products[:1]
            try:
                sum_price += product_request.products[0].price
            except Exception as exc:
                print(f'{len(product_request.products)} in {shop}')

        with open(f'minimum_output_{shop}.json', 'w', **file_open_settings) as f:
            json.dump(
                {"buy_list": [product_request.dict() for product_request in product_requests], "sum_price": sum_price},
                f, **json_write_settings)

    buy_preferences: Dict[BuyPreference, Tuple[str, ProductInfo]] = {}
    if user_query.buy_location_preference == ShopLocationPreference.MultiShopCheck:
        for shop, product_requests in user_basket.items():
            for product_request in product_requests:
                product_request: ProductsRequest
                if product_request.products:
                    if product_request.request in buy_preferences:
                        existing_product_info: ProductInfo = buy_preferences.get(product_request.request)[1]
                        if sort_products_by_price(existing_product_info) > sort_products_by_price(
                                product_request.products[0]):
                            buy_preferences[product_request.request] = (shop, product_request.products[0])
                    else:
                        buy_preferences[product_request.request] = (shop, product_request.products[0])

        final_result: Dict[str, List[ProductsRequest]] = defaultdict(list)
        sum_price = 0
        for buy_preference, info in buy_preferences.items():
            final_result[info[0]].append(ProductsRequest(request=buy_preference, products=[info[1]]))
            sum_price += info[1].price

        with open(f'multi_shop_output.json', 'w', **file_open_settings) as f:
            json.dump({"buy_list": {shop: [product_request.dict() for product_request in product_requests] for
                                    shop, product_requests in final_result.items()},
                       "sum_price": sum_price}, f, **json_write_settings)


if __name__ == '__main__':
    cli()
