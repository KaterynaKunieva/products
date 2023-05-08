from collections import defaultdict
from pydantic import BaseModel, parse_obj_as
from typing import Dict, List, Optional, Any
from extensions import get_http_response
import asyncio

from base_entities import ShopInfo, Shop

zakaz_shops = {
    "novus": [ShopInfo(id=48201070)],
    "metro": [ShopInfo(id=48215611)],
    'таврія': [ShopInfo(id=48221130)],
    'космос': [ShopInfo(id=48225131)],
    'восторг': [ShopInfo(id=48231001)],
    'харків': [ShopInfo(id=482320001)],
    "varus": [ShopInfo(id=48241001)],
    "auchan": [ShopInfo(id=48246401)],
    'winetime': [ShopInfo(id=482550001)],
    'столичний': [ShopInfo(id=48257001)],
    "megamarket": [ShopInfo(id=48267602)],
    "ultramarket": [ShopInfo(id=48277601)],
    'екомаркет': [ShopInfo(id=482800030)]
}

# zakaz_shops = {'novus': [ShopInfo(id=482010105, location='SkyMall'), ShopInfo(id=48201022, location='Рівне'),
#                ShopInfo(id=48201029, location='Кільцева'), ShopInfo(id=48201070, location='Осокор')],
#      'metro': [ShopInfo(id=48215610, location='Григоренко'), ShopInfo(id=48215611, location='Теремки'),
#                ShopInfo(id=48215612, location='Одеса'), ShopInfo(id=48215613, location='ХаркіГагаріна'),
#                ShopInfo(id=48215614, location='Дніпро'), ShopInfo(id=48215618, location='Запоріжжя'),
#                ShopInfo(id=48215620, location='Кривий Ріг'), ShopInfo(id=48215621, location='Вінниця'),
#                ShopInfo(id=48215625, location='Полтава'),
#                ShopInfo(id=48215627, location='Івано-Франківськ'),
#                ShopInfo(id=48215628, location='Чернівці'), ShopInfo(id=48215633, location='Троєщина'),
#                ShopInfo(id=48215634, location='Рівне'), ShopInfo(id=48215637, location='Львів'),
#                ShopInfo(id=48215639, location='Житомир')],
#      'таврія': [ShopInfo(id=48221130, location='Харків'), ShopInfo(id=482211449, location='Одеса')],
#      'космос': [ShopInfo(id=48225131, location='Одеса'), ShopInfo(id=48225531, location='Київ')],
#      'восторг': [ShopInfo(id=48231001, location='Клочківська')],
#      'харків': [ShopInfo(id=482320001, location='Клочківська')],
#      'varus': [ShopInfo(id=48241001, location='Панікахи'), ShopInfo(id=48241094, location='Вишгородська')],
#      'auchan': [ShopInfo(id=48246401, location='Петрівка'), ShopInfo(id=482464012, location='Кривий Ріг'),
#                 ShopInfo(id=48246403, location='Кільцева'), ShopInfo(id=48246407, location='Біличі'),
#                 ShopInfo(id=48246409, location='Львів'), ShopInfo(id=48246411, location='Запоріжжя'),
#                 ShopInfo(id=48246414, location='Rive Gauche'), ShopInfo(id=48246415, location='Либідська'),
#                 ShopInfo(id=48246416, location='Одеса'), ShopInfo(id=48246418, location='Чернігівська'),
#                 ShopInfo(id=48246423, location='Глушкова'), ShopInfo(id=48246424, location="Сім'ї Сосніних"),
#                 ShopInfo(id=48246425, location='Лугова'), ShopInfo(id=48246429, location='Дніпро'),
#                 ShopInfo(id=48246430, location='Житомир'), ShopInfo(id=48246431, location='Чернівці')],
#      'winetime': [ShopInfo(id=482550001, location='Бажана')],
#      'столичний': [ShopInfo(id=48257001, location='DRIVE')],
#      'megamarket': [ShopInfo(id=482676003, location='Подол Київ'),
#                     ShopInfo(id=48267601, location='Сурикова'),
#                     ShopInfo(id=48267602, location='Kosmopolit')],
#      'ultramarket': [ShopInfo(id=482776003, location='Подол Київ'),
#                      ShopInfo(id=48277601, location='Сурикова'),
#                      ShopInfo(id=48277602, location='Kosmopolit')],
#      'екомаркет': [ShopInfo(id=482800030, location='Огієнка'), ShopInfo(id=48280051, location='Житомир'),
#                    ShopInfo(id=48280061, location='Вінниця'), ShopInfo(id=48280083, location='Полтава'),
#                    ShopInfo(id=48280214, location='Закревського'), ShopInfo(id=48280328, location='Івано-Франківськ')]}

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
            shops_dict[code].append(ShopInfo(id=i['id'], location=" ".join(i['name'].split(" ")[1:])))
        print(shops_dict)
        return shops

    else:
        print(f"Failed to parse shops")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_shops())
    loop.close()
