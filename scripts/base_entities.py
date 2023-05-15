from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel
from datetime import datetime, date

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
    Unknown = "unknown"
    Mass = "mass"
    Capacity = "capacity"
    Length = "length"
    Quantity = "quantity"

class SizeInfo(BaseModel):
    value: float
    unit: str
    type: SizeInfoType
    class Config:
        use_enum_values = True

class PromoInfo(BaseModel):
    title: Optional[str]
    old_price: Optional[float]
    start_date: Optional[datetime]
    stop_date: Optional[datetime]
    description: Optional[str]

class ProductInfo(BaseModel):
    normalized_title: Optional[str]
    title: str 
    category_id: Optional[str]
    price: Optional[float]
    unit: Optional[str]
    weight: Optional[str]
    bundle: Optional[int]
    volume: Optional[float]
    weight_info: Optional[SizeInfo]
    producer: ProducerInfo
    description: Optional[str]
    slug: Optional[str]
    web_url: Optional[str]
    promotion: Optional[PromoInfo]


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

class ProductBuyInfo(BaseModel):
    product: ProductInfo
    quantity: int
    end_price: float

class ProductsRequest(BaseModel):
    request: Optional[BuyPreference]
    product_buy_infos: Optional[List[ProductBuyInfo]]

class ChequeShop(BaseModel):
    buy_list: List[ProductsRequest]
    end_price: int

class ProductsShopRequest(BaseModel):
    shop: str
    product_request: Optional[ProductsRequest]

class ChequeMulti(BaseModel):
    buy_list: List[ProductsShopRequest]
    end_price: int
