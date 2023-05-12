from typing import List

from scripts.base_entities import CategoryInfo, ShopInfo, ProductInfo


class ProductService():
    def get_shops(self) -> List[ShopInfo]:
        pass

    def get_categories(self, shop: ShopInfo, parent_category: CategoryInfo = None) -> List[CategoryInfo]:
        pass

    def get_products(self, shop: ShopInfo, category: CategoryInfo = None) -> List[ProductInfo]:
        pass

    def get_shop_locations(self, shop: ShopInfo) -> List[str]:
        pass

    ##########
    def get_promotion_categories(self, shop: ShopInfo, parent_category: CategoryInfo = None)  -> List[CategoryInfo]:
        pass

    def get_promotion_products(self, shop: ShopInfo, category: CategoryInfo = None) -> List[ProductInfo]:
        pass

    def form_buy_list(self, buy_request: BuyRequest) -> List[ProductInfo]:
        pass


class FileBaseProductService(ProductService):
    def __init__(self, input_file_path: str):
        self.input_file_path = input_file_path

    def get_shops(self) -> List[ShopInfo]:
        pass

    def get_categories(self, shop: ShopInfo, parent_category: CategoryInfo = None) -> List[CategoryInfo]:
        pass

    def get_products(self, shop: ShopInfo, category: CategoryInfo = None) -> List[ProductInfo]:
        pass

    def get_shop_locations(self, shop: ShopInfo) -> List[str]:
        pass

    ##########
    def get_promotion_categories(self, shop: ShopInfo, parent_category: CategoryInfo = None) -> List[CategoryInfo]:
        pass

    def get_promotion_products(self, shop: ShopInfo, category: CategoryInfo = None) -> List[ProductInfo]:
        pass

    def form_buy_list(self, buy_request: BuyRequest) -> List[ProductInfo]:
        pass