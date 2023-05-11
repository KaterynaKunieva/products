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


class ProductInfo(BaseModel):
    normalized_title: Optional[str]
    title: str 
    category_id: str
    price: float
    weight: Optional[str]
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
    weight_filter: Optional[str]
    shop_filter: Optional[List[str]]


class UserBuyRequest(BaseModel):
    buy_list: List[BuyPreference]
    buy_location_preference: ShopLocationPreference = ShopLocationPreference.IsolateShopsCheck


class Shop(BaseModel):
    name: str
    id: int


class ShopInfo(BaseModel):
    id: int
    location: Optional[str] = "default"


class ProductsRequest(BaseModel):
    request: Optional[BuyPreference]
    products: Optional[List[ProductInfo]]


class ProductsShop(BaseModel):
    shop: str
    requests: Optional[List[ProductsRequest]]
