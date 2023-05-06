import asyncio
import json
import logging
import os
from typing import List, Dict
import functools as ft
import click
from constants import STORE_INFO_PATH
from base_entities import CategoryInfo, ProductInfo
from helper import get_categories, get_products
from pydantic import parse_obj_as, parse_raw_as, parse_file_as
from zakaz_shops import shops

file_open_settings = {"encoding": 'utf-8'}
json_write_settings = {"ensure_ascii": False, "indent": 2}

curr_dir = os.path.dirname(__file__)
datat_dir = os.path.join(curr_dir, STORE_INFO_PATH)
if not os.path.exists(datat_dir):
    os.mkdir(datat_dir)


def async_cmd(func): #to do, write your function decorator
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
logging.basicConfig(level='DEBUG', handlers=[json_handler])


@click.group()
def cli():
    pass


@cli.command()
def get_shops():
    print(f"Available shops: {', '.join(list(shops.keys()))}")

def load_categories_from_file_or_cache(shop: str, is_popular: bool):
    pass
@cli.command()
@async_cmd
@click.option('--shop', default=None, type=str, help='list of shop categories.')
@click.option('--popular', default=False, type=bool, help='return popular categories or no.')
@click.option('--force_reload', default=False, type=bool, help='force data download no matter cache exists.')
async def parse_categories(shop, popular, force_reload):
    shop_list = list(shops.keys()) if shop == "all" else [shop]

    for shop_key in shop_list:
        logging.info(f"Started scanning for {shop_key} categories, popular: {popular}")
        shop_dir = try_create_shop_dir(shop_key)

        raw_category_file_path = os.path.join(shop_dir, f"raw_categories_info{'popular' if popular else ''}.json")
        categories_hierarchy_file_path = os.path.join(shop_dir, f"categories_hierarchy{'popular' if popular else ''}.json")
        categories_cached = os.path.exists(raw_category_file_path) and os.stat(
            raw_category_file_path).st_size > 5 and os.path.exists(categories_hierarchy_file_path)

        categories: List[CategoryInfo] = []
        if not categories_cached or force_reload:
            categories = await get_categories(shop_key, popular)
        else:
            logging.debug(f"Retrieving {shop_key} categories from path: {raw_category_file_path}")
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


@cli.command()
@async_cmd
@click.option('--shops', default="novus", type=str, help='list of shops.')
@click.option('--page_count', default=1, help='number of pages_count to scrape from shops.')
@click.option('--product_count', default=100, help='number of products to scrape from shops.')
async def parse_shop_products(shops, page_count, product_count):
    shop_list = list(shops.keys()) if shops == "all" else shops.split(",")

    for shop_key in shop_list:
        logging.info(f"Started scanning for {shop_key} products")
        shop_dir = try_create_shop_dir(shop_key)
        raw_product_path = os.path.join(shop_dir, f"raw_products_info.json")
        products_normalized_file_path = os.path.join(shop_dir, f"normalized_products_info.json")
        category_products: Dict[CategoryInfo, List[ProductInfo]] = await get_products(shop_key, page_count, product_count)
        print(len(category_products))



if __name__ == '__main__': #todo read - done
    parse_shop_products()