import logging
import math
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
length_measures = ['м', 'см', 'мм', 'км', 'm', 'cm', 'mm', 'km']

def normalize_title(product_title: str, product_brand: str = ""):
    try:
        product_key = product_title.lower()
        if product_brand:
            regexp_brand = product_brand.lower().replace("+", "\+")
        else:
            rb_first_letter = "(?<=\s)([A-ZА-ЯЇІЄҐ\+]"
            rb_word = rb_first_letter + "[A-ZА-Яa-zа-яЇїІіЄєҐґ\-\—\.\+®']+\s?)+\s*"
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
    amount = amount.replace(' {1,}', '')
    regexp_num = '\d+(,?\d+|.?\d+)*'
    regexp_unit = '[a-zа-яЇїІіЄєҐґ]+'
    if not amount:
        value = 1
        unit = ''
    else:
        value = re.search(regexp_num, amount)
        unit = re.findall(regexp_unit, amount)
        if value:
            value = value.group()
            value = value.replace(',', '.')
            try:
                value = float(value)
            except Exception as ex:
                try:
                    value = value.replace('х', "*")
                    value = eval(value)
                except SyntaxError as se:
                    value = 0
        else:
            value = 1

        if unit:
            unit = unit[-1]
        else:
            unit = ''
    type = SizeInfoType.Quantity
    if unit in capacity_measures:
        type = SizeInfoType.Capacity
    elif unit in mass_measures:
        type = SizeInfoType.Mass
    elif unit in length_measures:
        type = SizeInfoType.Length

    return SizeInfo(value=value, unit=unit, type=type)


def parse_weight_info_with_validation(product_info: ProductInfo) -> SizeInfo:
    title, volume, weight, bundle, unit = product_info.title, product_info.volume, product_info.weight, product_info.bundle, product_info.unit

    weight_info = product_info.weight_info
    if not weight_info:
        weight_info = parse_weight_info(product_info.weight)
    weight_info_formatted = weight_info
    weight_value, weight_unit, type = weight_info.value, weight_info.unit, weight_info.type

    regexp_amount = "(?<=\s)(\d+(\,?\d+|\.?\d+)*\s{0,1}[a-zа-яЇїІіЄє]{1,6})+(\s|$)"
    weight_in_title = re.search(regexp_amount, title)
    if weight_in_title:

        weight_in_title = weight_in_title.group()
        if 'шт х ' in title:
            title = title.replace('шт', '')
            title = title.replace(' {2,}', ' ')
            title = title.replace(' х ', 'х')
            weight_in_title = re.search(regexp_amount, title)
            if weight_in_title:
                weight_in_title = weight_in_title.group()

        if type == SizeInfoType.Quantity:
            weight_info_formatted = parse_weight_info(weight_in_title)

        elif volume and (str(int(volume)) in weight_in_title
                         or str(float(volume / 1000)) in weight_in_title
                         or str(int(volume / 1000)) in weight_in_title
                         or str(float(volume / 1000)).replace('.', ',') in weight_in_title
                         or str(int(volume * 1000)) in weight_in_title):
            weight_info_formatted = parse_weight_info(weight_in_title)

        elif weight_value and (str(int(weight_value)) in weight_in_title
                               or str(float(weight_value / 1000)) in weight_in_title
                               or str(float(weight_value / 1000)).replace('.', ',') in weight_in_title
                               or str(int(weight_value * 1000)) in weight_in_title):
            weight_info_formatted = parse_weight_info(weight_in_title)

        elif bundle and (str(int(bundle)) in weight_in_title
                         or str(float(bundle / 1000)) in weight_in_title
                         or str(float(bundle / 1000)).replace('.', ',') in weight_in_title
                         or str(int(bundle * 1000)) in weight_in_title):
            weight_info_formatted = parse_weight_info(weight_in_title)

        elif not weight_value and not volume:
            weight_info_formatted = parse_weight_info(weight_in_title)

    elif bundle and unit:
        weight_info_formatted = parse_weight_info(str(bundle) + unit)

    elif weight and (weight_info.type == SizeInfoType.Quantity or not weight_unit):
        weight_unit = ''
        if float(weight_value) >= 10:
            weight_unit = 'г'
        elif float(weight_value) < 10:
            weight_unit = 'кг'
        weight_info_formatted = parse_weight_info(str(weight_value) + weight_unit)

    elif volume and (weight_info.type == SizeInfoType.Capacity or not weight_unit):
        weight_unit = ''
        if float(weight_value) >= 10:
            weight_unit = 'мл'
        elif float(weight_value) < 10:
            weight_unit = 'л'
        weight_info_formatted = parse_weight_info(str(volume) + weight_unit)

    formatted_value, formatted_unit, formatted_type = weight_info_formatted

    if not formatted_value:
        weight_info_formatted = weight_info

    return weight_info_formatted


def normalize_weight_info(weight_info: SizeInfo, filter_unit: str = "") -> SizeInfo:
    weight_value, weight_unit, weight_type = weight_info.value, weight_info.unit, weight_info.type
    if weight_unit == 'л' or weight_unit == 'l':
        weight_value *= 1000
        weight_unit = 'мл'
    elif weight_unit == 'кг' or weight_unit == 'kg':
        weight_value *= 1000
        weight_unit = 'г'
    elif weight_unit == 'см' or weight_unit == 'cm':
        weight_value /= 100
        weight_unit = 'м'
    elif weight_unit == 'мм' or weight_unit == 'mm':
        weight_value /= 1000
        weight_unit = 'м'
    elif weight_unit == 'км' or weight_unit == 'km':
        weight_value *= 1000
        weight_unit = 'м'
    if weight_type == SizeInfoType.Capacity:
        if weight_unit == 'мл':
            weight_unit = 'г'
    if filter_unit == SizeInfoType.Capacity:
        weight_value, weight_unit, weight_type = mass_to_capacity(weight_info)
    elif filter_unit == SizeInfoType.Mass:
        weight_value, weight_unit, weight_type = capacity_to_mass(weight_info)
    return SizeInfo(value=weight_value, unit=weight_unit, type=weight_info.type)


# нужно приводить единицы измерения запроса к ед.изм. товаров
def capacity_to_mass(weight_info: SizeInfo) -> SizeInfo:
    weight_value, weight_unit, weight_type = weight_info.value, weight_info.unit, weight_info.type
    if weight_type == SizeInfoType.Capacity:
        if weight_unit == 'мл':
            weight_unit = 'г'
    return SizeInfo(value=weight_value, unit=weight_unit, type=weight_info.type)


def mass_to_capacity(weight_info: SizeInfo) -> SizeInfo:
    weight_value, weight_unit, weight_type = weight_info.value, weight_info.unit, weight_info.type
    if weight_type == SizeInfoType.Capacity:
        if weight_unit == 'г':
            weight_unit = 'мл'
    return SizeInfo(value=weight_value, unit=weight_unit, type=weight_info.type)


def sort_products_by_price(product_element: ProductInfo, min_size: str = "") -> float:
    end_price: float = 0
    normalized_min_size_info: SizeInfo = normalize_weight_info(parse_weight_info(min_size)) if min_size else None
    normalized_weight_info: SizeInfo
    if normalized_min_size_info.unit:
        normalized_weight_info = normalize_weight_info(product_element.weight_info,
                                                       filter_unit=normalized_min_size_info.unit)
    else:
        normalized_weight_info = normalize_weight_info(product_element.weight_info)
    try:
        price: float = product_element.price
        quantity: float = 0
        if normalized_min_size_info:
            if product_element.bundle and normalized_weight_info.value:
                quantity = math.ceil(normalized_min_size_info.value /
                                     (normalized_weight_info.value * product_element.bundle))
            elif product_element.bundle:
                quantity = math.ceil(normalized_min_size_info.value / product_element.bundle)
            elif normalized_weight_info.value:
                quantity = math.ceil(normalized_min_size_info.value / normalized_weight_info.value)
            end_price = price * quantity / normalized_min_size_info.value

        elif normalized_weight_info.value:
            quantity = normalized_weight_info.value / normalized_weight_info.value
            end_price = price * quantity / normalized_weight_info.value
        print(f"{product_element.title}")
        print(
            f"\tNeed {int(quantity)} with amount {normalized_weight_info.value} {normalized_weight_info.unit} and price {price} uah")
        print(
            f"\tResult: {quantity * normalized_weight_info.value} {normalized_weight_info.unit} by {(math.ceil(price * quantity)) * 100 / 100} uah")
    except Exception as ex:
        logging.error("Sorting of product by price failed", exc_info=ex)
    return end_price




# def find_filters():
#     regexp_filters = '(\"filters\": \[(\s(.*\s))*\]){1}'

def get_shop_locations(shop: str) -> List[str]:
    return [shopinfo.location for shopinfo in shop_infos.get(shop)]
