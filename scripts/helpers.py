import logging
import math
import os
import re
from typing import List

from base_entities import ProductInfo, SizeInfo, SizeInfoType
from silpo_helper import silpo_shops
from zakaz_shops import zakaz_shops

capacity_measures = ["л", "мл"]
mass_measures = ["кг", "г"]

shop_infos = {**zakaz_shops, **silpo_shops}


def normalize_title(product_title: str, product_brand: str = ""):
    try:
        product_key = product_title.lower()
        if product_brand:
            regexp_brand = product_brand.lower()
        else:
            rb_first_letter = "(?<=\s)([A-ZА-ЯЇІЄҐ]"
            rb_word = rb_first_letter + "[A-ZА-Яa-zа-яЇїІіЄєҐґ\-\—\.®']+\s?)+\s*"
            rb_exc = "[a-zа-яїієґ\-\—\.®']{0,5}\s*"
            regexp_brand = rb_word + '(' + rb_word + ')*' + '(' + rb_exc + rb_word + '){0,1}' + '(' + rb_word + ')*'
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
        brand = re.search(regexp_brand, product_key, flags=re.IGNORECASE)

        if amount is not None:
            amount = amount.group().strip()
            product_key = product_key.replace(amount, '')
        if percentages is not None:
            percentages = percentages.group().strip()
            product_key = product_key.replace(percentages, '')
        if number is not None:
            number = number.group().strip()
            product_key = product_key.replace(number, '')
        if brand is not None:
            brand = brand.group().strip()
            product_key = product_key.replace(brand, '')

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
        weight_info = parse_weight_info(product_info.weight)

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


def sort_products_by_price(product_element: ProductInfo, min_size: str = "") -> float:
    # может сделать 2 режима?
    # интересует ли ровно столько или можно больше (если ровно, то quantity должна получаться целой)
    end_price: float = 0
    normalized_weight_info: SizeInfo = normalize_weight_info(product_element.weight_info)
    try:
        price: float = product_element.price
        quantity: float = 0 # количество, которое нужно взять, чтобы собрать min_size
        normalized_min_size_info: SizeInfo = normalize_weight_info(parse_weight_info(min_size)) if min_size else None
        if normalized_min_size_info:
            if normalized_min_size_info == product_element.weight_info.unit:  # можно ли их сравнивать
                if product_element.bundle:
                    quantity = math.ceil(normalized_min_size_info.value /
                                         (normalized_weight_info.value * product_element.bundle))
                else:
                    quantity = math.ceil(normalized_min_size_info.value / normalized_weight_info.value)
        else:
            quantity = normalized_weight_info.value
        end_price = price * quantity
    except Exception as ex:
        logging.error("Sorting of product by price failed", exc_info=ex)
    return end_price / normalized_weight_info.value



# def find_filters():
#     regexp_filters = '(\"filters\": \[(\s(.*\s))*\]){1}'

def get_shop_locations(shop: str) -> List[str]:
    return [shopinfo.location for shopinfo in shop_infos.get(shop)]
