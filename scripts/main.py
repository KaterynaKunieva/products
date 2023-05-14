import asyncio
import json
import logging
import os
from collections import defaultdict
from typing import List, Dict, Set, Any, Tuple
import click
from constants import STORE_INFO_PATH
from base_entities import CategoryInfo, ProductInfo, UserBuyRequest, BuyPreference, ProductsRequest, \
    ShopLocationPreference, WeightInfo, ChequeShop, ChequeMulti, ProductsShop
from pydantic import parse_obj_as, parse_raw_as, parse_file_as, BaseModel
from parser import file_open_settings, json_write_settings, sort_products_by_price, async_cmd, cli


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
                                if buy_preference.brand_filter and product_item.producer.trademark \
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
            if product_request.products:
                sum_price += product_request.products[0].price
        with open(f'minimum_output_{shop}.json', 'w', **file_open_settings) as f:
            json.dump(
                ChequeShop(end_price=sum_price, buy_list=product_requests).dict(),
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
            json.dump(ChequeMulti(end_price=sum_price, buy_list=[ProductsShop(shop=shop, requests=product_requests) for shop, product_requests in final_result.items()]).dict(), f, **json_write_settings)


if __name__ == '__main__':
    cli()
