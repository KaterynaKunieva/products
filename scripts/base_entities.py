from typing import Optional, List, Dict

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
    category_id: str
    country: str
