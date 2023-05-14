import json
import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Set

import click
from pydantic import parse_file_as

from base_entities import CategoryInfo, ProductInfo
from constants import STORE_INFO_PATH
from extensions import async_cmd, json_serial
from helpers import parse_weight_info_with_validation, normalize_title, get_shop_locations, shop_infos, shop_parsers
from service_base import ShopScrapperService

file_open_settings = {"encoding": 'utf-8'}
json_write_settings = {"ensure_ascii": False, "indent": 2, "default":json_serial}

curr_dir = os.path.dirname(__file__)
datat_dir = os.path.join(curr_dir, STORE_INFO_PATH)
Path(datat_dir).mkdir(parents=True, exist_ok=True)

json_handler = logging.StreamHandler()
logging.basicConfig(level='INFO', handlers=[json_handler])

allowed_shops = list(shop_infos.keys())


def try_create_shop_dir(shop: str, shop_location: str = None):
    shop_dir = os.path.join(datat_dir, shop, shop_location or "")
    Path(shop_dir).mkdir(parents=True, exist_ok=True)
    return shop_dir


@click.group()
def cli():
    pass


@cli.command()
@async_cmd
@click.option('--shops', default="all", type=str, help='list of shop categories.')
@click.option('--locations', default="all", type=str, help='list of locations.')
@click.option('--promotions_only', default=False, type=bool, help='scrape only promotions or no?')
@click.option('--popular', default=False, type=bool, help='return popular categories or no.')
@click.option('--force_reload', default=True, type=bool, help='force data download no matter cache exists.')
async def parse_categories(shops, locations, promotions_only, popular, force_reload):
    shop_list = list(shop_infos.keys()) if not shops or shops == "all" else [shop.strip() for shop in shops.split(",")]
    input_locations = locations.splt(",") if locations and locations != "all" else []

    ###
    async def scrape_categories(shop_key: str, shop_location: str, promotion: bool = False):
        scrapper: ShopScrapperService = shop_parsers[shop_key]
        output_file_prefix = "promotion_" if promotion else ""
        promotion_str = "promotion" if promotion else "common"
        shop_full_name = f"{shop_key}_{shop_location}"

        logging.info(f"Started scrapping {shop_full_name} {promotion_str} categories, popular: {popular}")

        shop_dir = try_create_shop_dir(shop_key, shop_location)

        raw_category_file_path = os.path.join(shop_dir,
                                              f"{output_file_prefix}raw_categories_info{'popular' if popular else ''}.json")
        categories_hierarchy_file_path = os.path.join(shop_dir,
                                                      f"{output_file_prefix}categories_hierarchy{'popular' if popular else ''}.json")

        categories_cached = os.path.exists(raw_category_file_path) and os.path.exists(categories_hierarchy_file_path)

        categories: List[CategoryInfo] = []
        if not categories_cached or force_reload:
            categories = await scrapper.get_categories(shop_key, shop_location, popular) if not promotion \
                else await scrapper.get_promotion_categories(shop_key, shop_location)
        else:
            logging.info(f"Retrieving {shop_full_name} {promotion_str} categories from path: {raw_category_file_path}")
            categories = parse_file_as(List[CategoryInfo], raw_category_file_path)
        if categories:
            logging.info(f"Available {promotion_str} categories for {shop_full_name}, count: {len(categories)}")
            if not categories_cached or force_reload:
                logging.info(
                    f"Saving {promotion_str} categories to {raw_category_file_path} and {categories_hierarchy_file_path}")

                with open(raw_category_file_path, "w+", **file_open_settings) as f:
                    json.dump([category.dict() for category in categories], f, **json_write_settings)

                category_hierarchy = {category.slug: category.dict() for category in categories}

                with open(categories_hierarchy_file_path, "w+", **file_open_settings) as f:
                    json.dump(category_hierarchy, f, **json_write_settings)

    ###
    for shop_key in shop_list:
        shop_location_list = get_shop_locations(shop_key) if not input_locations else list(
            filter(lambda shop: shop.location in input_locations, get_shop_locations(shop_key)))

        if shop_location_list:
            for shop_location in shop_location_list:
                if not promotions_only:
                    await scrape_categories(shop_key, shop_location, False)
                await scrape_categories(shop_key, shop_location, True)
        else:
            logging.debug(f"No shop infos found for shop '{shop_key}', locations: {locations}'")


@cli.command()
@async_cmd
@click.option('--shops', default="silpo", type=str, help='list of shops.')
@click.option('--locations', default="all", type=str, help='list of locations.')
@click.option('--promotions_only', default=False, type=bool, help='scrape only promotions or no?')
@click.option('--page_count', default=1, help='number of pages_count to scrape from shops.')
@click.option('--per_page_product_count', default=100, help='number of products to scrape from shops.')
@click.option('--force_reload', default=True, help='force data download no matter cache exists.')
async def parse_shop_products(shops, locations, promotions_only, page_count, per_page_product_count, force_reload):
    shop_list: List[str] = []
    if not shops or shops == "all":
        shop_list = allowed_shops
    else:
        for shop_key in shops.split(","):
            shop_list.append(shop_key.strip())

    input_locations = locations.splt(",") if locations and locations != "all" else []

    ###
    async def scrape_products(shop_key: str, shop_location: str, promotion: bool = False):
        scrapper: ShopScrapperService = shop_parsers[shop_key]
        output_file_prefix = "promotion_" if promotion else ""
        promotion_str = "promotion" if promotion else "common"

        shop_full_name = f"{shop_key}_{shop_location}"

        logging.info(f"Started scrapping {shop_full_name} {promotion_str} products")

        shop_dir = try_create_shop_dir(shop_key, shop_location)

        raw_product_path = os.path.join(shop_dir, f"{output_file_prefix}raw_products_info.json")
        products_cached = os.path.exists(raw_product_path) and os.stat(raw_product_path).st_size > 5
        category_products: Dict[str, List[ProductInfo]] = {}

        if not products_cached or force_reload:
            category_products = await scrapper.get_products(shop_key, shop_location, page_count, per_page_product_count) if not promotion else await scrapper.get_promotion_products(shop_key, shop_location, page_count, per_page_product_count)
        else:
            logging.info(f"Retrieving '{shop_full_name}' {promotion_str} products from path: {raw_product_path}")
            category_products = parse_file_as(Dict[str, List[ProductInfo]], raw_product_path)
        if category_products:
            for category, products in category_products.items():
                for product in products:
                    product: ProductInfo
                    product.normalized_title = normalize_title(product_title=product.title,
                                                               product_brand=product.producer.trademark)
                    product.weight_info = parse_weight_info_with_validation(product)

            print(
                f"Available {promotion_str} products for '{shop_full_name}', categories count: {len(category_products)}")
            if not products_cached or force_reload:
                logging.info(f"Saving raw {promotion_str} products to {raw_product_path}")

                with open(raw_product_path, 'w+', **file_open_settings) as f:
                    json.dump(
                        {category_id: [product.dict() for product in product_list] for category_id, product_list
                         in
                         category_products.items()}, f, **json_write_settings)
                product_categories: Dict[str, List[str]] = defaultdict(list)
                logging.info(f"Saving {promotion_str} products per each category folder....")

                for category_id, products in category_products.items():
                    products: List[ProductInfo]
                    path_to_category = os.path.join(shop_dir, category_id)
                    if not os.path.exists(path_to_category):
                        os.mkdir(path_to_category)

                    with open(os.path.join(path_to_category, f'{output_file_prefix}normalized_products.json'), 'w+',
                              **file_open_settings) as f:
                        json.dump({product.normalized_title: product.dict() for product in products}, f,
                                  **json_write_settings)

                    with open(os.path.join(path_to_category, f'{output_file_prefix}normalized_products_list.json'),
                              'w+',
                              **file_open_settings) as f:
                        json.dump(sorted([product.normalized_title for product in products]), f,
                                  **json_write_settings)

                    with open(os.path.join(path_to_category, f'{output_file_prefix}products_list.json'), 'w+',
                              **file_open_settings) as f:
                        json.dump(sorted([product.title for product in products]), f, **json_write_settings)

                    with open(os.path.join(path_to_category, f'{output_file_prefix}brand_list.json'), 'w+',
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

                    with open(os.path.join(path_to_category, f'{output_file_prefix}brand_products.json'), 'w+',
                              **file_open_settings) as f:
                        json.dump({k: list(v) for k, v in brand_products.items()}, f, **json_write_settings)

                    with open(os.path.join(path_to_category, f'{output_file_prefix}product_brands.json'), 'w+',
                              **file_open_settings) as f:
                        json.dump({k: list(v) for k, v in product_brands.items()}, f, **json_write_settings)

                with open(os.path.join(shop_dir, f'{output_file_prefix}products_categories.json'), 'w+',
                          **file_open_settings) as f:
                    json.dump(product_categories, f,
                              **json_write_settings)

    ###
    for shop_key in shop_list:
        shop_location_list = get_shop_locations(shop_key) if not input_locations else list(
            filter(lambda shop: shop.location in input_locations, get_shop_locations(shop_key)))

        if shop_location_list:
            for shop_location in shop_location_list:
                if not promotions_only:
                    await scrape_products(shop_key, shop_location, False)
                await scrape_products(shop_key, shop_location, True)
        else:
            logging.debug(f"No shop infos found for shop '{shop_key}', locations: {locations}'")


if __name__ == '__main__':
    parse_shop_products()
