from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel


class BaseCategoryInfo(BaseModel):
    id: str
    title: str
    description: Optional[str]
    image_url: Optional[str]
    is_popular: Optional[bool]


class CategoryInfo(BaseCategoryInfo):
    children: Optional[List[BaseCategoryInfo]]


class BaseCustomCategoryHierarchy(BaseCategoryInfo):
    pass


class CustomCategoryHierarchy(BaseCategoryInfo):
    children: Dict[str, BaseCustomCategoryHierarchy]


class ProducerInfo(BaseModel):
    trademark: Optional[str]
    trademark_slug: Optional[str]

class ProductInfo(BaseModel):
    code: Optional[str]
    title: str 
    category_id: str
    price: int
    currency: Optional[str]
    weight: Optional[int]
    unit: Optional[str]
    producer: ProducerInfo
    description: Optional[str]

class ShopLocationPreference(str, Enum):
    SingleShop = "single_shop",
    MultiShop = "multi_shop"
class BuyPreference(BaseModel):
    product_filter: Optional[str]
    brand_filter: Optional[str]
    weight_filter: Optional[str]
    shop_filter: Optional[str]
class UserBuyRequest(BaseModel):
    buy_list: List[BuyPreference]
    buy_location_preference: ShopLocationPreference = ShopLocationPreference.SingleShop


class Shop(BaseModel):
    name: str
    id: int


class ShopInfo(BaseModel):
    id: int
    location: Optional[str]
