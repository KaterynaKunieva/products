import asyncio
import json
import logging
import os
import re
from collections import defaultdict
from typing import List, Dict, Set
import functools as ft
import click
from constants import STORE_INFO_PATH
from base_entities import CategoryInfo, ProductInfo, UserBuyRequest
from silpo_helper import silpo_shops, get_silpo_categories, get_silpo_products
from zakaz_helper import get_zakaz_categories, get_zakaz_products
from pydantic import parse_obj_as, parse_raw_as, parse_file_as
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
logging.basicConfig(level='INFO', handlers=[json_handler])


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
        product_key = product_title
        regexp_brand = product_brand if product_brand is not None else None
        regexp_amount = "(?<=\s)\d+(,?\d+|.?\d+)*[a-zа-яЇїІіЄєҐґ]+"
        regexp_percentage = "(?<=\s)\d+(,\d+|.\d+)*\s*%"
        regexp_number = "№\d*"
        regexp_symbols = "[®]+"
        regexp_quotes = "['\"‘’«»”„]"  # delete only symbols
        regexp_brackets = "[()\[\]{}]*"  # delete only symbols
        # regexp_quotes = "['\"‘’«»”„].*['\"‘’«»”„]" # delete all inside
        # regexp_brackets = "\(.*\)|\[.*\]|\{.*\}" # delete all inside

        brand = re.search(regexp_brand, product_key) if product_brand else None
        amount = re.search(regexp_amount, product_key)
        percentages = re.search(regexp_percentage, product_key)
        number = re.search(regexp_number, product_key)

        if brand is not None:
            brand = brand.group().strip()
            product_key = re.sub(brand, '', product_key)
        if amount is not None:
            amount = amount.group().strip()
            product_key = re.sub(amount, '', product_key)
        if percentages is not None:
            percentages = percentages.group().strip()
            product_key = re.sub(percentages, '', product_key)
        if number is not None:
            number = number.group().strip()
            product_key = re.sub(number, '', product_key)

        product_key = re.sub(regexp_symbols, '', product_key)
        product_key = re.sub(regexp_quotes, '', product_key)
        product_key = re.sub(regexp_brackets, '', product_key)
        product_key = re.sub(' {2,}', ' ', product_key)

        return product_key.lower().strip()
    except Exception as ex:
        logging.error(f'Failed to normalized {product_title}, {product_brand}', exc_info=ex)
        return product_title


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

        shop_location_list = get_shop_locations(shop_key) if not input_locations else list(filter(lambda shop: shop.location in input_locations, get_shop_locations(shop_key)))

        if shop_location_list:
            for shop_location in shop_location_list:
                shop_full_name = f"{shop_key}_{shop_location}"
                shop_dir = try_create_shop_dir(shop_key, shop_location)

                raw_category_file_path = os.path.join(shop_dir, f"raw_categories_info{'popular' if popular else ''}.json")
                categories_hierarchy_file_path = os.path.join(shop_dir,
                                                              f"categories_hierarchy{'popular' if popular else ''}.json")
                categories_cached = os.path.exists(raw_category_file_path) and os.stat(
                    raw_category_file_path).st_size > 5 and os.path.exists(categories_hierarchy_file_path)

                categories: List[CategoryInfo] = []
                if not categories_cached or force_reload:
                    categories = await get_zakaz_categories(shop_key, shop_location, popular) if shop_key in list(zakaz_shops.keys()) else await get_silpo_categories(shop_key, location=shop_location)
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

        shop_location_list = get_shop_locations(shop_key) if not input_locations else list(filter(lambda shop: shop.location in input_locations, get_shop_locations(shop_key)))

        if shop_location_list:
            for shop_location in shop_location_list:
                shop_full_name = f"{shop_key}_{shop_location}"
                shop_dir = try_create_shop_dir(shop_key, shop_location)

                raw_product_path = os.path.join(shop_dir, f"raw_products_info.json")
                products_cached = os.path.exists(raw_product_path) and os.stat(raw_product_path).st_size > 5
                category_products: Dict[str, List[ProductInfo]] = {}

                if not products_cached or force_reload:
                    category_products = await get_zakaz_products(shop_key, shop_location, page_count, product_count) if shop_key in list(zakaz_shops.keys()) else await get_silpo_products(shop_key, shop_location, page_count, product_count)
                else:
                    logging.info(f"Retrieving '{shop_full_name}' products from path: {raw_product_path}")
                    category_products = parse_file_as(Dict[str, List[ProductInfo]], raw_product_path)
                if category_products:
                    for category, products in category_products.items():
                        for product in products:
                            product: ProductInfo
                            product.normalized_title = normalize_title(product_title=product.title,
                                                   product_brand=product.producer.trademark)

                    print(f"Available products for '{shop_full_name}', categories count: {len(category_products)}")
                    if not products_cached or force_reload:
                        logging.info(f"Saving raw products to {raw_product_path}")

                        with open(raw_product_path, 'w+', **file_open_settings) as f:
                            json.dump(
                                {category_id: [product.dict() for product in product_list] for category_id, product_list in
                                 category_products.items()}, f, **json_write_settings)
                        product_categories: Dict[str, List[str]] = defaultdict(list)
                        for category_id, products in category_products.items():
                            products: List[ProductInfo]
                            path_to_category = os.path.join(shop_dir, category_id)
                            if not os.path.exists(path_to_category):
                                os.mkdir(path_to_category)

                            with open(os.path.join(path_to_category, 'normalized_products.json'), 'w+',
                                      **file_open_settings) as f:
                                json.dump({product.normalized_title: product.dict() for product in products}, f, **json_write_settings)

                            with open(os.path.join(path_to_category, 'normalized_products_list.json'), 'w+', **file_open_settings) as f:
                                json.dump(sorted([product.normalized_title for product in products]), f, **json_write_settings)

                            with open(os.path.join(path_to_category, 'products_list.json'), 'w+', **file_open_settings) as f:
                                json.dump(sorted([product.title for product in products]), f, **json_write_settings)

                            with open(os.path.join(path_to_category, 'brand_list.json'), 'w+', **file_open_settings) as f:
                                json.dump(list(
                                    set([product.producer.trademark for product in products if product.producer.trademark])), f,
                                          **json_write_settings)

                            brand_products: Dict[str, Set[str]] = defaultdict(set)
                            product_brands: Dict[str, Set[str]] = defaultdict(set)
                            for product in products:
                                # normalize
                                if product.producer.trademark:
                                    brand_products[product.producer.trademark].add(product.normalized_title)
                                    product_brands[product.normalized_title].add(product.producer.trademark)
                                product_categories[product.normalized_title].append(category_id)

                            with open(os.path.join(path_to_category, 'brand_products.json'), 'w+', **file_open_settings) as f:
                                json.dump({k: list(v) for k, v in brand_products.items()}, f, **json_write_settings)

                            with open(os.path.join(path_to_category, 'product_brands.json'), 'w+', **file_open_settings) as f:
                                json.dump({k: list(v) for k, v in product_brands.items()}, f, **json_write_settings)

                        with open(os.path.join(shop_dir, 'products_categories.json'), 'w+',
                                  **file_open_settings) as f:
                            json.dump(product_categories, f,
                                      **json_write_settings)
            else:
                logging.debug(f"No shop infos found for shop '{shop_key}', locations: {locations}'")


@cli.command()
@async_cmd
@click.option('--input_file_path', default="./user_buy_request_path.json", type=str, help='list of shops.')
# @click.option('--output_file_path', default="./output.json", type=str, help='list of shops.')
async def form_buy_list(input_file_path):
    # Read input_file_path file
    # Read all necessary information from data files

    # how to read preferences?

    # 1 - Form minimum cost buy list
    # 2 - User must input what product of found he wants?

    # Output buy card to output_file_path

    user_query = parse_file_as(UserBuyRequest, input_file_path)
    user_query = user_query.dict()
    print(user_query['buy_list'])

    base_path = os.path.join(os.path.dirname(__file__), STORE_INFO_PATH)   # path to data
    file_navigator = os.path.join('default', 'products_categories.json')
    file_product_info = "normalized_products.json"

    products_dict = defaultdict(list)

    for product in user_query['buy_list']:
        product_title = product["product_filter"]
        product_brand = product["brand_filter"]
        product_weight = product["weight_filter"]
        shop_name = product["shop_filter"]
        shop_location = product["location_filter"]
        print(f"Product: {product_title}")

        path_to_shop = os.path.join(base_path, shop_name)
        path_to_navigator = os.path.join(path_to_shop, file_navigator)

        # find category of product
        with open(path_to_navigator, 'r', **file_open_settings) as f:
            file_navigation = json.load(f)
            for product_key in list(file_navigation.keys()):
                if product_key.startswith(product_title):
                    path_to_category = file_navigation[product_key][0]
                    product_location = os.path.join(path_to_shop, 'default', path_to_category, file_product_info)
        with open(product_location, 'r', **file_open_settings) as p:
            file_info = json.load(p)
            for k in list(file_info.keys()):
                if k.startswith(product_title):
                    product_item = defaultdict(lambda: defaultdict(dict))
                    product_item[k] = file_info[k]
                    products_dict[shop_name].append(dict(product_item))

    with open('./output.json', 'w', **file_open_settings) as r:
        json.dump(products_dict, r, **json_write_settings)



    # preferences - how to calculate (card for each shop or card with different shops)
    # if type == by single:
    # get data from each shop
    # create list for each
    # create function to create list by characteristics?


    # if type == multiple
    # selecting products by user - in all cases by user,
    # but: if user select the most important characteristics - in all shops by it


if __name__ == '__main__':
    # form_buy_list()
    cli()
