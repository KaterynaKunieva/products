import logging
import re
from typing import List, Dict

from base_entities import ProductInfo, SizeInfo, SizeInfoType, CategoryInfo
from service_base import ShopScrapperService
from zakaz_helper import ZakazoShopScrapperService
from silpo_helper import silpo_shops, SilpoShopScrapperService
from zakaz_shops import zakaz_shops

shop_infos = {**zakaz_shops, **silpo_shops}
shop_parsers: Dict[str, ShopScrapperService] = {**{shop: ZakazoShopScrapperService() for shop in zakaz_shops.keys()}, **{shop: SilpoShopScrapperService() for shop in silpo_shops.keys()}}

capacity_measures = ["л", "мл"]
mass_measures = ["кг", "г"]

def normalize_title(product_title: str, product_brand: str = ""):
    try:
        product_key = product_title.lower()
        regexp_brand = product_brand.lower() if product_brand else ''
        regexp_amount = "(?<=\s)\d+(,?\d+|.?\d+)*[a-zа-яЇїІіЄєҐґ]+"
        regexp_percentage = "(?<=\s)\d+(,\d+|.\d+)*\s*%"
        regexp_number = "№\d*"
        regexp_symbols = "[®]+"
        regexp_quotes = "['\"‘’«»”„]"  # delete only symbols
        regexp_brackets = "[()\[\]{}]*"  # delete only symbols
        # regexp_quotes = "['\"‘’«»”„].*['\"‘’«»”„]" # delete all inside
        # regexp_brackets = "\(.*\)|\[.*\]|\{.*\}" # delete all inside

        amount = re.search(regexp_amount, product_key, flags=re.IGNORECASE)
        percentages = re.search(regexp_percentage, product_key, flags=re.IGNORECASE)
        number = re.search(regexp_number, product_key, flags=re.IGNORECASE)

        if amount is not None:
            amount = amount.group().strip()
            product_key = product_key.replace(amount, '')
        if percentages is not None:
            percentages = percentages.group().strip()
            product_key = product_key.replace(percentages, '')
        if number is not None:
            number = number.group().strip()
            product_key = product_key.replace(number, '')

        product_key = product_key.replace(regexp_brand, '')

        product_key = re.sub(regexp_symbols, '', product_key, flags=re.IGNORECASE)
        product_key = re.sub(regexp_quotes, '', product_key, flags=re.IGNORECASE)
        product_key = re.sub(regexp_brackets, '', product_key, flags=re.IGNORECASE)
        product_key = re.sub(' {2,}', ' ', product_key, flags=re.IGNORECASE)

        return product_key.strip()
    except Exception as ex:
        logging.error(f'Failed to normalized {product_title}, {product_brand}', exc_info=ex)
        return product_title


def parse_weight_info(amount: str) -> SizeInfo:
    regexp_num = '\d+(,?\d+|.?\d+)*'
    regexp_unit = '[a-zа-яЇїІіЄєҐґ]+'
    if not amount:
        value = 1
        unit = ''
    else:
        value = re.search(regexp_num, amount)
        unit = re.search(regexp_unit, amount)
        if value:
            value = value.group()
            value = value.replace(',', '.')
            try:
                value = float(value)
            except Exception as ex:
                value = eval(value)
        else:
            value = 1

        if unit:
            unit = unit.group()
        else:
            unit = ''
    type = SizeInfoType.Quantity
    if unit in capacity_measures:
        type = SizeInfoType.Capacity
    elif unit in mass_measures:
        type = SizeInfoType.Mass

    return SizeInfo(value=value, unit=unit,
                    type=type)


def parse_weight_info_with_validation(product_info: ProductInfo) -> SizeInfo:
    weight_info = product_info.weight_info
    if not weight_info:
        weight_info = parse_weight_info(product_info.weight or product_info.unit or product_info.volume)

    weight_value, weight_unit, type = weight_info.value, weight_info.unit, weight_info.type
    title, volume, weight = product_info.title, product_info.volume, product_info.weight

    # if weight and volume:
    #     if weight_value == volume:
    #         # delete weight
    #         return volume
    #     else:
    #         if weight_value + weight_unit in title:
    #             return weight
    #         elif weight_value in title:
    #             return weight
    #         elif volume in title: # add check units after volume in title
    #             return volume
    #         else:
    #             return min(weight_value, volume)# (brutto bigger)
    #
    # elif weight:
    #     if weight_value + weight_unit in title:# а також між величиною і одиницею виміру може бути пробіл
    #         return weight
    #     elif weight_value in title:
    #         return weight
    # elif volume:
    #     if volume in title:  # add check units after volume in title
    #         return volume
    # else:
    #     regexp_amount = "(?<=\s)\d+(,?\d+|.?\d+)*[a-zа-яЇїІіЄєҐґ]+"
    #     amount = re.search(regexp_amount, title)
    #     if amount:
    #         return amount.group()

    return SizeInfo(value=weight_value, unit=weight_unit, type=type)


def normalize_weight_info(weight_info: SizeInfo) -> SizeInfo:
    weight_value, weight_unit = weight_info.value, weight_info.unit
    if weight_unit == 'л':
        weight_value *= 1000
        weight_unit = 'мл'
    elif weight_unit == 'кг':
        weight_value *= 1000
        weight_unit = 'г'
    return SizeInfo(value=weight_value, unit=weight_unit, type=weight_info.type)


def sort_products_by_price(product_element: ProductInfo, min_size: str) -> float:
    try:
        normalized_weight_info = normalize_weight_info(product_element.weight_info)
        min_size_weight_info: SizeInfo = normalize_weight_info(parse_weight_info(min_size)) if min_size else None

        unit_quantity = normalized_weight_info.value
        price = product_element.price
        bundle = product_element.bundle
        if bundle:
            #coeff =  math.ceil(min_size_weight_info.value / min_size_weight_info.value) if min_size_weight_info else 1
            coeff = 1
            return (price * coeff) / (unit_quantity * bundle) #end price for this setup of products, which suites our min size if it is specified
        else:
            #coeff =  math.ceil(min_size_weight_info.value / min_size_weight_info.value) if min_size_weight_info else 1
            coeff = 1
            return (price * coeff) / unit_quantity #end price for this setup of products, which suites our min size if it is specified
    except Exception as ex:
        logging.error("Sorting of product by price failed", exc_info=ex)
    return 0


# def find_filters():
#     regexp_filters = '(\"filters\": \[(\s(.*\s))*\]){1}'

def get_shop_locations(shop: str) -> List[str]:
    return [shopinfo.location for shopinfo in shop_infos.get(shop)]
