from pydantic import BaseModel


class ShopInfo(BaseModel):
    id: int

shops = {
    "metro": ShopInfo(id=48215611),
    "novus": ShopInfo(id=48201070),
    "ekomarket": ShopInfo(id=48280214),
    "tavria": ShopInfo(id=48221130),
    "megamarket": ShopInfo(id=48267602),
    "varus": ShopInfo(id=48241001),
    "ultramarket": ShopInfo(id=48277601),
    "auchan": ShopInfo(id=48246401)
}