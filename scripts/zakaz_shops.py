from collections import defaultdict
from pydantic import BaseModel, parse_obj_as
from typing import Dict, List, Optional, Any
from extensions import get_http_response
import asyncio

from base_entities import ShopInfo, Shop

# zakaz_shops = {
#     "novus":
#     [ShopInfo(name='novus', id=482010105, location='skymall', title='novus skymall'), ShopInfo(name='novus', id=48201022, location='рівне drive', title='novus рівне drive'), ShopInfo(name='novus', id=48201029, location='кільцева', title='novus кільцева'), ShopInfo(name='novus', id=48201070, location='осокор', title='novus осокор')],
#     "metro":
#     [ShopInfo(name='metro', id=48215610, location='григоренко drive', title='metro григоренко drive'), ShopInfo(name='metro', id=48215611, location='теремки drive', title='metro теремки drive'), ShopInfo(name='metro', id=48215612, location='одеса drive', title='metro одеса drive'), ShopInfo(name='metro', id=48215613, location='харків гагаріна drive', title='metro харків гагаріна drive'), ShopInfo(name='metro', id=48215614, location='дніпро drive', title='metro дніпро drive'), ShopInfo(name='metro', id=48215618, location='запоріжжя drive', title='metro запоріжжя drive'), ShopInfo(name='metro', id=48215620, location='кривий ріг drive', title='metro кривий ріг drive'), ShopInfo(name='metro', id=48215621, location='вінниця drive', title='metro вінниця drive'), ShopInfo(name='metro', id=48215625, location='полтава drive', title='metro полтава drive'), ShopInfo(name='metro', id=48215627, location='івано-франківськ drive', title='metro івано-франківськ drive'), ShopInfo(name='metro', id=48215628, location='чернівці drive', title='metro чернівці drive'), ShopInfo(name='metro', id=48215633, location='троєщина drive', title='metro троєщина drive'), ShopInfo(name='metro', id=48215634, location='рівне drive', title='metro рівне drive'), ShopInfo(name='metro', id=48215637, location='львів drive', title='metro львів drive'), ShopInfo(name='metro', id=48215639, location='житомир drive', title='metro житомир drive')],
#     "таврія":
#     [ShopInfo(name='таврія', id=48221130, location='в харків', title='таврія в харків'), ShopInfo(name='таврія', id=482211449, location='в одеса drive', title='таврія в одеса drive')],
#     "космос":
#     [ShopInfo(name='космос', id=48225131, location='одеса drive', title='космос одеса drive'), ShopInfo(name='космос', id=48225531, location='київ drive', title='космос київ drive')],
#     "восторг":
#     [ShopInfo(name='восторг', id=48231001, location='клочківська drive', title='восторг клочківська drive')],
#     "харків":
#     [ShopInfo(name='харків', id=482320001, location='клочківська drive', title='харків клочківська drive')],
#     "varus":
#     [ShopInfo(name='varus', id=48241001, location='панікахи drive', title='varus панікахи drive'), ShopInfo(name='varus', id=48241094, location='вишгородська', title='varus вишгородська')],
#     "auchan":
#     [ShopInfo(name='auchan', id=48246401, location='петрівка', title='auchan петрівка'), ShopInfo(name='auchan', id=482464012, location='кривий ріг drive', title='auchan кривий ріг drive'), ShopInfo(name='auchan', id=48246403, location='кільцева', title='auchan кільцева'), ShopInfo(name='auchan', id=48246407, location='біличі drive', title='auchan біличі drive'), ShopInfo(name='auchan', id=48246409, location='львів', title='auchan львів'), ShopInfo(name='auchan', id=48246411, location='запоріжжя', title='auchan запоріжжя'), ShopInfo(name='auchan', id=48246414, location='rive gauche', title='auchan rive gauche'), ShopInfo(name='auchan', id=48246415, location='либідська', title='auchan либідська'), ShopInfo(name='auchan', id=48246416, location='одеса', title='auchan одеса'), ShopInfo(name='auchan', id=48246418, location='чернігівська drive', title='auchan чернігівська drive'), ShopInfo(name='auchan', id=48246423, location='глушкова', title='auchan глушкова'), ShopInfo(name='auchan', id=48246424, location="сім'ї сосніних", title="auchan сім'ї сосніних"), ShopInfo(name='auchan', id=48246425, location='лугова', title='auchan лугова'), ShopInfo(name='auchan', id=48246429, location='дніпро', title='auchan дніпро'), ShopInfo(name='auchan', id=48246430, location='житомир', title='auchan житомир'), ShopInfo(name='auchan', id=48246431, location='чернівці', title='auchan чернівці')],
#     "winetime":
#     [ShopInfo(name='winetime', id=482550001, location='бажана drive', title='winetime бажана drive')],
#     "столичний":
#     [ShopInfo(name='столичний', id=48257001, location='drive', title='столичний drive')],
#     "megamarket":
#     [ShopInfo(name='megamarket', id=482676003, location='подол київ drive', title='megamarket подол київ drive'), ShopInfo(name='megamarket', id=48267601, location='сурикова drive', title='megamarket сурикова drive'), ShopInfo(name='megamarket', id=48267602, location='kosmopolit drive', title='megamarket kosmopolit drive')],
#     "ultramarket":
#     [ShopInfo(name='ultramarket', id=482776003, location='подол київ drive', title='ultramarket подол київ drive'), ShopInfo(name='ultramarket', id=48277601, location='сурикова drive', title='ultramarket сурикова drive'), ShopInfo(name='ultramarket', id=48277602, location='kosmopolit drive', title='ultramarket kosmopolit drive')],
#     "екомаркет":
#     [ShopInfo(name='екомаркет', id=482800030, location='огієнка drive', title='екомаркет огієнка drive'), ShopInfo(name='екомаркет', id=48280051, location='житомир', title='екомаркет житомир'), ShopInfo(name='екомаркет', id=48280061, location='вінниця', title='екомаркет вінниця'), ShopInfo(name='екомаркет', id=48280083, location='полтава', title='екомаркет полтава'), ShopInfo(name='екомаркет', id=48280214, location='закревського', title='екомаркет закревського'), ShopInfo(name='екомаркет', id=48280328, location='івано-франківськ', title='екомаркет івано-франківськ')],
# }

zakaz_shops = {
    "novus": [ShopInfo(name='novus', id=482010105, title='novus')],
    "metro": [ShopInfo(name='metro', id=48215610, title='metro')],
    "таврія": [ShopInfo(name='таврія', id=48221130,title='таврія')],
    "космос": [ShopInfo(name='космос', id=48225131, title='космос')],
    "восторг": [ShopInfo(name='восторг', id=48231001, title='восторг')],
    "харків": [ShopInfo(name='харків', id=482320001,title='харків клочківська drive')],
    "varus":[ShopInfo(name='varus', id=48241001, title='varus')],
    "auchan": [ShopInfo(name='auchan', id=48246401, title='auchan')],
    "winetime": [ShopInfo(name='winetime', id=482550001,title='winetime')],
    "столичний": [ShopInfo(name='столичний', id=48257001, title='столичний')],
    "megamarket": [ShopInfo(name='megamarket', id=482676003, title='megamarket')],
    "ultramarket":[ShopInfo(name='ultramarket', id=482776003, title='ultramarket')],
    "екомаркет": [ShopInfo(name='екомаркет', id=482800030, title='екомаркет')]
}



async def get_shops() -> List[Shop]:
    shops: Dict[str: str]
    shops_url = 'https://stores-api.zakaz.ua/stores'
    response = await get_http_response(shops_url, headers={"Accept-Language": "uk"})
    if response:
        shops: List[Shop] = parse_obj_as(List[Shop], response)
        shops_dict: Dict[str, List[Any]] = defaultdict(list)
        for i in shops:
            i = i.dict()
            code = i['name'].split(" ")[0].lower()
            shops_dict[code].append(ShopInfo(id=i['id'], name=i['name'].split(' ')[0].lower(), title=i['name'].lower(), location=" ".join(i['name'].split(" ")[1:]).lower()))
        for k, v in shops_dict.items():
            print(f'"{k}": ')
            print(v, sep=", ", end=', \n')
        return shops

    else:
        print(f"Failed to parse shops")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_shops())
    loop.close()
