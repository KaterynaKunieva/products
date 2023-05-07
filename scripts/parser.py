import asyncio
import json
import logging
import os
import re
import click
from collections import defaultdict
from typing import List, Dict, Set
import functools as ft
from constants import STORE_INFO_PATH
from base_entities import CategoryInfo, ProductInfo
from zakaz_helper import get_zakaz_categories, get_zakaz_products
from pydantic import parse_obj_as, parse_raw_as, parse_file_as
from zakaz_shops import zakaz_shops

file_open_settings = {"encoding": 'utf-8'}
json_write_settings = {"ensure_ascii": False, "indent": 2}

curr_dir = os.path.dirname(__file__)
datat_dir = os.path.join(curr_dir, STORE_INFO_PATH)
if not os.path.exists(datat_dir):
    os.mkdir(datat_dir)


def async_cmd(func):  # to do, write your function decorator
    @ft.wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


def try_create_shop_dir(shop: str):
    shop_dir = os.path.join(datat_dir, shop)
    if not os.path.exists(shop_dir):
        os.mkdir(shop_dir)
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
    product_key = product_title
    regexp_brand = product_brand
    regexp_amount = "(?<=\s)\d+(,?\d+|.?\d+)*[a-zа-яЇїІіЄєҐґ]+"
    regexp_percentage = "(?<=\s)\d+(,\d+|.\d+)*\s*%"
    regexp_number = "№\d*"

    brand = re.search(regexp_brand, product_key)
    amount = re.search(regexp_amount, product_key)
    percentages = re.search(regexp_percentage, product_key)
    number = re.search(regexp_number, product_key)

    if brand is not None:
        brand = brand.group().strip()
        product_key = re.sub(brand, '', product_key)
        product_key = re.sub(' {2,}', ' ', product_key)
    if amount is not None:
        amount = amount.group().strip()
        product_key = re.sub(amount, '', product_key)
        product_key = re.sub(' {2,}', ' ', product_key)
    if percentages is not None:
        percentages = percentages.group().strip()
        product_key = re.sub(percentages, '', product_key)
        product_key = re.sub(' {2,}', ' ', product_key)
    if number is not None:
        number = number.group().strip()
        product_key = re.sub(number, '', product_key)
        product_key = re.sub(' {2,}', ' ', product_key)

    return product_key.lower().strip()


@cli.command()
@async_cmd
@click.option('--shop', default=None, type=str, help='list of shop categories.')
@click.option('--popular', default=False, type=bool, help='return popular categories or no.')
@click.option('--force_reload', default=False, type=bool, help='force data download no matter cache exists.')
async def parse_categories(shop, popular, force_reload):
    shop_list = list(zakaz_shops.keys()) if shop == "all" else [shop]

    for shop_key in shop_list:
        logging.info(f"Started scanning for {shop_key} categories, popular: {popular}")
        shop_dir = try_create_shop_dir(shop_key)

        raw_category_file_path = os.path.join(shop_dir, f"raw_categories_info{'popular' if popular else ''}.json")
        categories_hierarchy_file_path = os.path.join(shop_dir,
                                                      f"categories_hierarchy{'popular' if popular else ''}.json")
        categories_cached = os.path.exists(raw_category_file_path) and os.stat(
            raw_category_file_path).st_size > 5 and os.path.exists(categories_hierarchy_file_path)

        categories: List[CategoryInfo] = []
        if not categories_cached or force_reload:
            categories = await get_zakaz_categories(shop_key, popular)
        else:
            logging.info(f"Retrieving {shop_key} categories from path: {raw_category_file_path}")
            categories = parse_file_as(List[CategoryInfo], raw_category_file_path)
        if categories:
            print(f"Available categories for {shop_key}, count: {len(categories)}")
            if not categories_cached or force_reload:
                logging.info(f"Saving categories to {raw_category_file_path}")
                with open(raw_category_file_path, "w+", **file_open_settings) as f:
                    json.dump([category.dict() for category in categories], f, **json_write_settings)
                category_hierarchy = {category.id: category.dict() for category in categories}

                with open(categories_hierarchy_file_path, "w+", **file_open_settings) as f:
                    json.dump(category_hierarchy, f, **json_write_settings)


allowed_shops = list(zakaz_shops.keys())

@cli.command()
@async_cmd
@click.option('--shops', default="NOVUS SkyMall", type=str, help='list of shops.')
@click.option('--page_count', default=5, help='number of pages_count to scrape from shops.')
@click.option('--product_count', default=100, help='number of products to scrape from shops.')
@click.option('--force_reload', default=True, help='force data download no matter cache exists.')
async def parse_shop_products(shops, page_count, product_count, force_reload):
    shop_list = []
    if shops == "all":
        shop_list = allowed_shops
    else:
        for shop_key in shops.split(","):
            if shop_key not in allowed_shops:
                for allowed_shop in allowed_shops:
                    if allowed_shop.startswith(shop_key):
                        shop_list.append(allowed_shop)
            else:
                shop_list.append(shop_key)

    for shop_key in shop_list:
        logging.info(f"Started scanning for {shop_key} products")

        shop_dir = try_create_shop_dir(shop_key)
        raw_product_path = os.path.join(shop_dir, f"raw_products_info.json")
        products_cached = os.path.exists(raw_product_path) and os.stat(raw_product_path).st_size > 5
        category_products: Dict[str, List[ProductInfo]] = {}
        if not products_cached or force_reload:
            category_products = await get_zakaz_products(shop_key, page_count, product_count)
        else:
            logging.info(f"Retrieving {shop_key} products from path: {raw_product_path}")
            category_products = parse_file_as(Dict[str, List[ProductInfo]], raw_product_path)
        if category_products:
            for category, products in category_products.items():
                for product in products:
                    product: ProductInfo
                    product.code = normalize_title(product_title=product.title,
                                                   product_brand=product.producer.trademark)

            print(f"Available products for {shop_key}, categories count: {len(category_products)}")
            if not products_cached or force_reload:
                logging.info(f"Saving raw products to {raw_product_path}")

                with open(raw_product_path, 'w+', **file_open_settings) as f:
                    json.dump(
                        {category_id: [product.dict() for product in product_list] for category_id, product_list in
                         category_products.items()}, f, **json_write_settings)

                for category_id, products in category_products.items():
                    products: List[ProductInfo]
                    path_to_category = os.path.join(shop_dir, category_id)
                    if not os.path.exists(path_to_category):
                        os.mkdir(path_to_category)

                    with open(os.path.join(path_to_category, 'normalized_products.json'), 'w+',
                              **file_open_settings) as f:
                        json.dump({product.code: product.dict() for product in products}, f, **json_write_settings)

                    with open(os.path.join(path_to_category, 'normalized_products_list.json'), 'w+', **file_open_settings) as f:
                        json.dump(sorted([product.code for product in products]), f, **json_write_settings)

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
                            brand_products[product.producer.trademark].add(product.code)
                            product_brands[product.code].add(product.producer.trademark)

                    with open(os.path.join(path_to_category, 'brand_products.json'), 'w+', **file_open_settings) as f:
                        json.dump({k: list(v) for k, v in brand_products.items()}, f, **json_write_settings)

                    with open(os.path.join(path_to_category, 'product_brands.json'), 'w+', **file_open_settings) as f:
                        json.dump({k: list(v) for k, v in product_brands.items()}, f, **json_write_settings)


@cli.command()
@async_cmd
@click.option('--input_file_path', default="./user_buy_request_path.json", type=str, help='list of shops.')
@click.option('--output_file_path', default="./output.json", type=str, help='list of shops.')
async def form_buy_list(input_file_path):

    # Read input input_file_path file
    # Read all necessary information from data files
    # Form minimum cost buy list
    # Output buy card to output_file_path
    
        user_products = click.prompt('Введіть список продуктів')
        user_shops = click.prompt('Введіть магазини, в яких шукати')
        user_searchtype = click.confirm('Формувати чек по кожному магазину?')

        user_query = {
            'Products': user_products.split(' '), 
            'Shops': user_shops.split(' '), 
            'TypeSearch': user_searchtype
        }

        click.echo(f'Було одержано такі вводні: \n\tПродукти: {user_products}\n\tМагазини: {user_shops}, \n\tТип пошуку: {user_searchtype}\n')
        if click.confirm('Вірно? '): 
            click.echo('Починаю аналіз...')

if __name__ == '__main__':
    cli()
