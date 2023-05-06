from pydantic import BaseModel


class ShopInfo(BaseModel):
    id: int

zakaz_shops = {
    "metro": ShopInfo(id=48215611),
    "novus_osokor": ShopInfo(id=48201070),
    "ekomarket": ShopInfo(id=48280214),
    "tavria": ShopInfo(id=48221130),
    "megamarket": ShopInfo(id=48267602),
    "varus": ShopInfo(id=48241001),
    "ultramarket": ShopInfo(id=48277601),
    "auchan": ShopInfo(id=48246401)
}

# id ссылается на определенный магазин физический (адрес), а не всю сеть
# /stores/
# 482010105 - NOVUS SkyMall
# 48201022 - NOVUS Rivne DRIVE
# 48201029 - NOVUS Kil'tseva
# 48201070 - NOVUS Osokor
# ....
