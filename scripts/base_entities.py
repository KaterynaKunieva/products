from typing import Optional, List, Dict, Any

from pydantic import BaseModel


class BaseCategoryInfo(BaseModel):
    id: str
    title: str
    count:  Optional[int]
    description: Optional[str]
    image_url: Optional[str]
    is_popular: Optional[bool]


class CategoryInfo(BaseCategoryInfo):
    children: Optional[List[BaseCategoryInfo]]


class BaseCustomCategoryHierarchy(BaseCategoryInfo):
    pass


class CustomCategoryHierarchy(BaseCategoryInfo):
    children: Dict[str, BaseCustomCategoryHierarchy]


class ProductInfo(BaseModel):
    title: str 
    category_id: str
    price: int
    currency: Optional[str]
    weight: Optional[int]
    unit: Optional[str]
    producer: Dict[str, Any]
    description: Optional[str]
