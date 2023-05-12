import asyncio
import json
import logging
import os
import re
from collections import defaultdict
from itertools import groupby
from typing import List, Dict, Set, Any
import functools as ft
import click
from constants import STORE_INFO_PATH
from base_entities import CategoryInfo, ProductInfo, UserBuyRequest, BuyPreference, ProductsRequest, ProductsShop, \
    ShopLocationPreference
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


def sort_products_by_price(product_element: ProductInfo) -> float:
    if product_element.weight is None or product_element.weight == 0 or product_element.weight == "0":
        weight = 1
    else:
        weight = re.search("\d+(,?\d+|.?\d+)*", product_element.weight)
        weight_unit = re.search("[a-zа-яЇїІіЄєҐґ]+", product_element.weight)
        if weight:
            weight = weight.group()
            weight = float(weight.replace(',', '.'))
        else:
            weight = 1
        if weight_unit:
            weight_unit = weight_unit.group()
        else:
            weight_unit = ''
        if weight_unit == 'л':
            weight *= 1000
        elif weight_unit == 'кг':
            weight *= 1000
    price = product_element.price
    # if product_element["found_in_shop"] == 'silpo' else product_element.price/ 100
    return price / weight

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
    end_price = 0

    #1. dont write to output file for each buy_list, do it in the end when all buy_lists are resolved
    #2. read files using parse_file_as
    #3. Algo:
    """
        find minimum buy list for each shop
        write it to file per each shop
        additionally, if user_query.buy_location_preference == 'multi_shop_check' form one more output file with minimum buy list across all shops Dict[str, List[ProductInfo]] 
    """
    for buy_preference in buy_list:
        print('Started buy_preference')
        paths_to_shops = []
        paths_to_navigators = []
        for shop in buy_preference.shop_filter:
            products_in_request: List[ProductsRequest] = []
            print('Started shop in buy_preference')
            products = []
            path_to_shop = os.path.join(base_path, shop)
            path_to_navigator = os.path.join(path_to_shop, file_navigator)

            paths_to_shops.append(path_to_shop)
            paths_to_navigators.append(path_to_navigator)

            # find category of buy_preference
            file_navigation = parse_file_as(Dict[str, List[str]], path_to_navigator)
            if file_navigation:
                print('Stored file_navigation')
            for product_key in list(file_navigation.keys()):
                if buy_preference.title_filter in product_key.split(" "):
                    print('Found request in file_navigation')
                    path_to_category = file_navigation[product_key][0]      #take first category
                    product_location = os.path.join(path_to_shop, 'default', path_to_category, file_product_info)

                    # find buy_preference in category
                    file_info: Dict[str, ProductInfo] = parse_file_as(Dict[str, ProductInfo], product_location)
                    if file_info:
                        print('Stored file_info')

                    for title_key, product_item in list(file_info.items()):
                        product_item: ProductInfo
                        if buy_preference.title_filter in title_key.split(" "):
                            print('Found request in product_location')
                            # задані і бренд, і вага
                            if buy_preference.brand_filter == product_item.producer.trademark \
                                    and buy_preference.weight_filter == product_item.weight \
                                    and product_item not in products:
                                products.append(product_item)
                            # заданий бренд (не задана вага)
                            elif buy_preference.brand_filter == product_item.producer.trademark \
                                    and product_item not in products:
                                products.append(product_item)
                            # задана вага (не заданий бренд)
                            elif buy_preference.weight_filter == product_item.weight and product_item not in products:
                                products.append(product_item)
                            # не задані ні бренд, ні вага
                            elif product_item not in products:
                                products.append(product_item)
            products_in_request.append(ProductsRequest(request=buy_preference, products=products))
            user_basket[shop].extend(products_in_request)

    for shop, product_requests in user_basket.items():
        with open(f'output_{shop}.json', 'w', **file_open_settings) as f:
            json.dump([product_request.dict() for product_request in product_requests], f, **json_write_settings)

    for shop, product_requests in user_basket.items():
        for product_request in product_requests:
            product_request.products.sort(key=sort_products_by_price)
            product_request.products = product_request.products[:1]

        with open(f'minimum_output_{shop}.json', 'w', **file_open_settings) as f:
            json.dump([product_request.dict() for product_request in product_requests], f, **json_write_settings)

    # if user_query.buy_location_preference == ShopLocationPreference.MultiShopCheck:
    #     final_minimum_shop_product_requests:  Dict[str, List[ProductsRequest]] = defaultdict(list)
    #
    #     for shop, product_requests in user_basket.items():
    #         for  product_request in product_requests:



    #1)Iterate

                    # надо щоб назва магазину була ключем і реквест ключем (тоді він не має бути діктом-об'єктом)






                    # for shop, products_in_shop in user_basket.items():
                    #     # print(shop)
                    #     for user_query_title, products_for_query in products_in_shop.items():
                    #         products_for_query.sort(key=sort_products_by_price)
                    #
                    #         # printing
                    #         print(user_query_title, " ", type(products_for_query))
                    #         for prod in products_for_query:
                    #             print(f'\t{prod["title"]} - {prod["weight"]} - '
                    #                   f'{prod["price"] if prod["found_in_shop"] == "silpo" else prod["price"] / 100}')

                            # надо сохранять в селектед первую запись по запросу
                            # if user_query_title not in list(selected_products[shop].keys()):
                            #     print(f'{shop} - {user_query_title}')
                            #     selected_products[shop][user_query_title] = products_for_query[0]
                            #     і додати енд прайс в массив? по каждому магазину

                # if user_query.buy_location_preference == 'multi_shop_check':
                #     user_basket: Dict[str, List] = defaultdict(list)
                #     for title_key, product_info in file_info.items():
                #         product_item: Dict[str, Any] = {
                #             'user_query': buy_preference.title_filter, #use named tuple
                #             'found_in_shop': buy_preference.shop_filter,
                #             **product_info
                #         }
                #         if buy_preference.title_filter in title_key \
                #                 and product_item not in user_basket[buy_preference.title_filter]:
                #             user_basket[buy_preference.title_filter].append(product_item)
                #
                #     for user_query_title, products in user_basket.items():
                #         products.sort(key=sort_products_by_price)
                #         for product_item in products:
                #             if user_query_title not in list(selected_products.keys()):
                #                 end_price += product_item["price"] if product_item["found_in_shop"] == "silpo" else product_item["price"] / 100
                #                 selected_products[user_query_title] = product_item
                #     with open('./output.json', 'w', **file_open_settings) as r:
                #         json.dump(selected_products, r, **json_write_settings)


    # selected_products: Dict[str, Dict[str, ProductInfo]] = defaultdict(defaultdict)

    # for shop in shop_infos:
    #     for product_key in :
    #         #find minimum for shop and output
    #
    # if buy_preference == "across_shops":
    #     #one more iteration to find min products across all shops
    # print(end_price)

if __name__ == '__main__':
    cli()
