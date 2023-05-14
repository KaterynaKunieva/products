from typing import List, Dict

from base_entities import ProductInfo, CategoryInfo, ShopInfo, UserBuyRequest


class ShopScrapperService():
    async def get_categories(self, shop: str, location: str, popular: bool = False) -> List[CategoryInfo]:
        pass

    async def get_products(self, shop: str, location: str, page_count: int, per_page_product_count: int) -> Dict[
        str, List[ProductInfo]]:
        pass
    async def get_promotion_categories(self, shop: str, location: str) -> List[CategoryInfo]:
        pass

    async def get_promotion_products(self, shop: str, location: str, page_count: int, per_page_product_count: int) -> Dict[
        str, List[ProductInfo]]:
        pass

class ProductService():

    def get_shops(self) -> List[ShopInfo]:
        pass

    def get_categories(self, shop: ShopInfo) -> List[CategoryInfo]:
        pass

    def get_products(self, shop: ShopInfo, category: CategoryInfo = None) -> List[ProductInfo]:
        pass

    def get_shop_locations(self, shop: ShopInfo) -> List[str]:
        pass

    ##########
    def get_promotion_categories(self, shop: ShopInfo) -> List[CategoryInfo]:
        pass
        # это категории, в которых есть акционные товары?
        # или категория акций?

    def get_promotion_products(self, shop: ShopInfo, category: CategoryInfo = None) -> List[ProductInfo]:
        pass

    def form_buy_list(self, buy_request: UserBuyRequest) -> List[ProductInfo]:
        pass