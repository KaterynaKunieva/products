from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel


class BaseCategoryInfo(BaseModel):
    id: Optional[str]
    title: str
    description: Optional[str]
    image_url: Optional[str]
    is_popular: Optional[bool]
    slug: Optional[str]


class CategoryInfo(BaseCategoryInfo):
    children: Optional[List["CategoryInfo"]]


class ProducerInfo(BaseModel):
    trademark: Optional[str]
    trademark_slug: Optional[str]

class SizeInfoType(str, Enum):
    Mass = "mass"
    Capacity = "capacity"
    Quantity = "quantity"

class SizeInfo(BaseModel):
    value: float
    unit: str
    type: SizeInfoType
    class Config:
        use_enum_values = True

class ProductInfo(BaseModel):
    normalized_title: Optional[str]
    title: str 
    category_id: str
    price: float
    unit: Optional[str]
    weight: Optional[str]
    bundle: Optional[int]
    volume: Optional[float]
    weight_info: Optional[SizeInfo]
    producer: ProducerInfo
    description: Optional[str]
    slug: Optional[str]
    web_url: Optional[str]


class ShopLocationPreference(str, Enum):
    IsolateShopsCheck = "isolate_shops_check",
    MultiShopCheck = "multi_shop_check"


class BuyPreference(BaseModel):
    title_filter: Optional[str]
    brand_filter: Optional[List[str]]
    weight_filter: Optional[str] #100мг, 1кг, 500мл, 1л, 1шт
    shop_filter: Optional[List[str]]

    def __eq__(self, othr):
        return (isinstance(othr, type(self))
                and (self.title_filter, frozenset(self.brand_filter) if self.brand_filter else frozenset(), self.weight_filter, frozenset(self.shop_filter) if self.shop_filter else frozenset()) ==
                (othr.title_filter,  frozenset(othr.brand_filter) if othr.brand_filter else frozenset(), othr.weight_filter, frozenset(othr.shop_filter) if othr.shop_filter else frozenset()))
    def __hash__(self):
        return hash((self.title_filter, frozenset(self.brand_filter) if self.brand_filter else frozenset(), self.weight_filter, frozenset(self.shop_filter) if self.shop_filter else frozenset()))


class UserBuyRequest(BaseModel):
    buy_list: List[BuyPreference]
    buy_location_preference: ShopLocationPreference = ShopLocationPreference.IsolateShopsCheck


class Shop(BaseModel):
    name: Optional[str]
    id: int


class ShopInfo(Shop):
    id: int
    location: Optional[str] = "default"
    title: Optional[str]


class ProductsRequest(BaseModel):
    request: Optional[BuyPreference]
    products: Optional[List[ProductInfo]]


class ProductsShop(BaseModel):
    shop: str
    requests: Optional[List[ProductsRequest]]


class ChequeShop(BaseModel):
    buy_list: List[ProductsRequest]
    end_price: int


class ChequeMulti(BaseModel):
    buy_list: List[ProductsShop]
    end_price: int
