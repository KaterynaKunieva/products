from typing import List, Dict
from pydantic import parse_file_as
from base_entities import CategoryInfo, ShopInfo, ProductInfo, UserBuyRequest
import os

from helpers import shop_infos
from service_base import ProductService


class FileBaseProductService(ProductService):
    def __init__(self, input_file_path: str):
        self.input_file_path = input_file_path

    def get_shops(self) -> List[ShopInfo]:
        return list(shop_infos.values())

    def get_categories(self, shop: ShopInfo) -> List[CategoryInfo]:
        categories_list: List[CategoryInfo] = []
        path_to_categories_file = os.path.join(self.input_file_path, shop.name, shop.location,
                                               'raw_categories_info.json')
        if os.path.isfile(path_to_categories_file):
            categories_list = parse_file_as(List[CategoryInfo], path_to_categories_file) # найдет ли эта запись только верхние категории?
        return categories_list

    def get_products(self, shop: ShopInfo, category: CategoryInfo = None) -> List[ProductInfo]:
        products_list: Dict[str, ProductInfo] = {}
        path_to_file_products = os.path.join(self.input_file_path, shop.name, category.slug, "normalized_products.json")
        if os.path.isfile(path_to_file_products):
            products_list = parse_file_as(Dict[str, ProductInfo], path_to_file_products)
        return list(products_list.values())

    def get_shop_locations(self, shop: ShopInfo) -> List[str]:
        shop_locations: List[str] = []
        for shop_key, shop_info_list in shop_infos.items():
            if shop_key == shop.name:
                for shop_info in shop_info_list:
                    shop_locations.append(shop_info.location)
        return shop_locations

        ##########

    def get_promotion_categories(self, shop: ShopInfo) -> List[CategoryInfo]:
        pass
        # это категории, в которых есть акционные товары?
        # или категория акций?

    def get_promotion_products(self, shop: ShopInfo, category: CategoryInfo = None) -> List[ProductInfo]:
        pass
        # может передать promotion_categories в get_products?

    def form_buy_list(self, buy_request: UserBuyRequest) -> List[ProductInfo]:
        buy_list: List[ProductInfo] = []
        # buy_list? що це має бути?
        return buy_list


test = FileBaseProductService(input_file_path=os.path.join(os.path.dirname(__file__), 'data'))
shops = test.get_shops()
locations = test.get_shop_locations(ShopInfo(id=48201070, title='novus'))
categories = test.get_categories(ShopInfo(id=48221130, title='таврія'))
print(shops)
print(locations)
print(categories)
