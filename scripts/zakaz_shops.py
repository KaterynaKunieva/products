# написала модель и функцию,
# взяла названия и айди с апи,
# вывела их в консоль, скопировала
# и вставила в переменную

from pydantic import BaseModel, parse_obj_as
from typing import Dict, List
from extensions import get_http_response
import asyncio

class Shop(BaseModel):
    name: str
    id: int

async def get_shops() -> List[Shop]:
    shops: Dict[str: str]
    shops_url = 'https://stores-api.zakaz.ua/stores'
    response = await get_http_response(shops_url, headers={"Accept-Language": "uk"})
    if response:
        shops: List[Shop] = parse_obj_as(List[Shop], response)
        shops_dict: Dict[str, str] = {}
        for i in shops:
            i = i.dict()
            shops_dict[i['name']] = i['id']
        for k, v in shops_dict.items():
            print(f'\t"{k.split(" ")[0].lower()}": ShopInfo(id={v}, location="{" ".join(k.split(" ")[1:])}"), ')
        return shops

    else:
        print(f"Failed to parse shops")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_shops())
    loop.close()


class ShopInfo(BaseModel):
    id: int
    location: str


zakaz_shops = {
    "novus skymall": ShopInfo(id=482010105),
    "novus рівне ": ShopInfo(id=48201022),
    "novus кільцева": ShopInfo(id=48201029),
    "novus осокор": ShopInfo(id=48201070),
    "metro григоренко ": ShopInfo(id=48215610),
    "metro теремки ": ShopInfo(id=48215611),
    "metro одеса ": ShopInfo(id=48215612),
    "metro харків гагаріна ": ShopInfo(id=48215613),
    "metro дніпро ": ShopInfo(id=48215614),
    "metro запоріжжя ": ShopInfo(id=48215618),
    "metro кривий ріг ": ShopInfo(id=48215620),
    "metro вінниця ": ShopInfo(id=48215621),
    "metro полтава ": ShopInfo(id=48215625),
    "metro івано-франківськ ": ShopInfo(id=48215627),
    "metro чернівці ": ShopInfo(id=48215628),
    "metro троєщина ": ShopInfo(id=48215633),
    "metro рівне ": ShopInfo(id=48215634),
    "metro львів ": ShopInfo(id=48215637),
    "metro житомир ": ShopInfo(id=48215639),
    "таврія в харків": ShopInfo(id=48221130),
    "таврія в одеса ": ShopInfo(id=482211449),
    "космос одеса ": ShopInfo(id=48225131),
    "космос київ ": ShopInfo(id=48225531),
    "восторг клочківська ": ShopInfo(id=48231001),
    "харків клочківська ": ShopInfo(id=482320001),
    "varus панікахи ": ShopInfo(id=48241001),
    "varus вишгородська": ShopInfo(id=48241094),
    "auchan петрівка": ShopInfo(id=48246401),
    "auchan кривий ріг ": ShopInfo(id=482464012),
    "auchan кільцева": ShopInfo(id=48246403),
    "auchan біличі ": ShopInfo(id=48246407),
    "auchan львів": ShopInfo(id=48246409),
    "auchan запоріжжя": ShopInfo(id=48246411),
    "auchan rive gauche": ShopInfo(id=48246414),
    "auchan либідська": ShopInfo(id=48246415),
    "auchan одеса": ShopInfo(id=48246416),
    "auchan чернігівська ": ShopInfo(id=48246418),
    "auchan глушкова": ShopInfo(id=48246423),
    "auchan сім'ї сосніних": ShopInfo(id=48246424),
    "auchan лугова": ShopInfo(id=48246425),
    "auchan дніпро": ShopInfo(id=48246429),
    "auchan житомир": ShopInfo(id=48246430),
    "auchan чернівці": ShopInfo(id=48246431),
    "winetime бажана ": ShopInfo(id=482550001),
    "столичний ": ShopInfo(id=48257001),
    "megamarket подол київ ": ShopInfo(id=482676003),
    "megamarket сурикова ": ShopInfo(id=48267601),
    "megamarket kosmopolit ": ShopInfo(id=48267602),
    "ultramarket подол київ ": ShopInfo(id=482776003),
    "ultramarket сурикова ": ShopInfo(id=48277601),
    "ultramarket kosmopolit ": ShopInfo(id=48277602),
    "ecomarket огієнка ": ShopInfo(id=482800030),
    "ecomarket житомир": ShopInfo(id=48280051),
    "ecomarket вінниця": ShopInfo(id=48280061),
    "ecomarket полтава": ShopInfo(id=48280083),
    "ecomarket закревського": ShopInfo(id=48280214),
    "ecomarket івано-франківськ": ShopInfo(id=48280328), 
}
