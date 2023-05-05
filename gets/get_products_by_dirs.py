import json 
import math
import os 
import logging 
import re 
from bs4 import BeautifulSoup
import requests

logging.basicConfig(filename='metadata.log', level=logging.DEBUG)


def get_soup(url, **kwargs): 
    """
        returns soup for url or None
    """
    response = requests.get(url, **kwargs)
    if response.status_code == 200:
        return BeautifulSoup(response.text, features='html.parser')
    return None

def dump_to_json(filename, data, **kwargs):
    """
            filename - path like .../category/subcategory/products.json 
            data - {productKey: { title, brand, price... etc}} 
    """
    kwargs.setdefault('ensure_ascii', False)
    kwargs.setdefault('indent', 2)  
    
    # file not created yet
    if not os.path.isfile(filename): 
        with open(filename, 'w', encoding='utf-8') as f:  
            json.dump({}, f, **kwargs)
    
    with open(filename, 'r+', encoding='utf-8') as f: 
        file_data = json.load(f) # saving data from file 
        # adding data to data from file by key
        for k in data.keys(): 
            file_data.setdefault(k, [])  
            file_data[k].extend(data[k])
        
        # rewriting updated data to file  
        f.seek(0)
        json.dump(file_data, f, **kwargs)
    
    logging.debug(f'Saved data to file: {filename}')


def parse_product(url, fmt, path): 
    """
            url - path to page with products 
            fmt - universal part of url to product (to create link to product)
            path - created path to save result products 

            returns products = {keyTitle1: {title, price, amount ... etc}, 
                                keyTitle2: {title, price, amount ... etc }, 
                                ...etc}
    """
    soup = get_soup(url) 
    products = {} 
    if soup is None: 
        logging.warning(f'No soup for {url}')
    else: 
        # iterating over cards for products 
        for p in soup.select('.ProductsBox__listItem'): 
            if p.select_one('.ProductTile_withOpacity') is not None: # product not available
                break
            
            product_title = p.select_one('.ProductTile__title').text # title product 
            product_key = product_title # key title for grouping products (without brand, amount)

            rb_first_letter = "(?<=\s)([A-ZА-ЯЇІЄҐ]" # без першого слова у рядку і з великої літери 
            rb_word = rb_first_letter + "[A-ZА-Яa-zа-яЇїІіЄєҐґ\-\—\.®']+\s?)+\s*" # будь-які символи 1 або більше разів? пробіл між словами та в кінці рядка
            rb_exc = "[a-zа-яїієґ\-\—\.®']{0,5}\s*" # маленькі слова в брендах: до 5 символів, можуть зустрітися 1 раз
            regex_brand = rb_word + '(' + rb_word + ')*' + '(' + rb_exc + rb_word + '){0,1}' + '(' + rb_word + ')*'
            regex_amount = "(?<=\s)\d+(,?\d+|.?\d+)*[a-zа-яЇїІіЄєҐґ]+" # перед пробіл, хоча б 1 цифра, після може бути . або , і після них обов'язково ще хоча б одна цифра і маленькі літери
            regex_percentage = "(?<=\s)\d+(,\d+|.\d+)*\s*%" # перед пробіл, цифра . або , (якщо знаки, то обов'язково ще цифра) і знак % (між ними може бути пробіл)

            brand = re.search(regex_brand, product_title)
            amount = re.search(regex_amount, product_title)
            percentages = re.search(regex_percentage, product_title)

            # getting found text in title (if it found)
            if brand is not None: 
                brand = brand.group().strip() 
                product_key = re.sub(brand, '', product_key) # deleting brand from key
                product_key = re.sub('  ', ' ', product_key) # deleting double spaces
            if amount is not None: 
                amount = amount.group().strip()
                product_key = re.sub(amount, '', product_key) # deleting amount from key
                product_key = re.sub('  ', ' ', product_key) # deleting double spaces
            if percentages is not None: 
                percentages = percentages.group().strip()
                product_key = re.sub(percentages, '', product_key) # deleting percentages from key
                product_key = re.sub('  ', ' ', product_key) # deleting double spaces

            href = p.select_one('.ProductTile').attrs['href'] # link to product
            price = '-' # if no price for product  
            if p.select_one('.Price__value_caption'): # if price found 
                price = p.select_one('.Price__value_caption').text 

            size = p.select_one('.ProductTile__weight').text # size from html 
            size = re.sub('за', '', size) # deleting from size "за" (за 1кг -> 1кг, за 1л -> 1л)
            size = re.sub(' ', '', size) # deleting double spaces

            product_key = product_key.strip().lower() # lowercase key for product

            products.setdefault(product_key, []) 
            # each product is an object 
            product = {
                'product title': product_title, 
                'product brand': brand or '-', # if no brand
                'product percentages': percentages or '-', # if no percentages
                'product price': price, 
                'product size':  size or amount or "-",  # if no amount
                'product link': fmt + href,
            } 
            products[product_key].append(product) # resulting object of products
    
    full_path = os.path.join(path, 'products.json').strip() # path from category to end file
    dump_to_json(full_path, products) 

    return products


def crawl_pages(url, fmt, path): 
    """
            url - url to (sub)category 
            fmt - start url to create link to page (adding ?page = i)
            path - dest to save products from page 

            returns products_on_page = [{parsed_prod1}, {parsed_prod2}, ... etc]
    """
    products_on_page = [] 
    soup = get_soup(url)  
    fmtp = url + '?page={}' # pagination

    if soup is None: 
        logging.warning(f'No soup for {url}')
    else: 
        # Getting number of pages
        # amount - num of available products in (sub)category, stored on page in one of 2 tags 
        amount = (soup.select_one('.FilterableLayout__productsCount') or soup.select_one('.SecondLevelCategory__goodsNumber')).text  
        amount = int(amount.split(' ')[0])
        # num of pages - text in the last item in pagination block 
            # or (if there are not available products) - num of available products / num of visible on page + 1 
            # if no pagination block - there is one page 
        pages_count = min(math.ceil(amount/30 + 1), int(soup.select('.Pagination__item')[-1].text) if soup.select('.Pagination__item') else 1)

        # For each page getting products
        for i in range(1, pages_count+1): 
            logging.debug(f'Start crawling page: {str(i)}')
            url = fmtp.format(i) # url of page 
            products_on_page.extend(parse_product(url, fmt, path)) # adding products by each page 
    return products_on_page


def parse_sub_categories(url, fmt, path):
    """
            url - url for category to explore 
            fmt - url to create link to subcategory 
            path - path like 'category' to save products 

            returns sub = [{subcategory1: {Products1}}, {subcategory1: {Products2}}]
    """

    soup = get_soup(url)  
    sub = [] 
    if soup is None: 
        logging.warning(f'No soup for {url}')
    else: 
        # Subcategory exists
        if soup.select('.CategoriesBox__list'): # (blocks for subcategories)

            # Get products for each subcategory in category 
            for s in soup.select('.CategoriesBox__listItem'): # blocks for subcategories

                title = s.select_one('.CategoryCard__title').text # subcategory title
                logging.debug(f'Subcategory: {title}')

                # dir for subcategory in category
                full_path = os.path.join(path, title).strip() # 'categoryName/subcategoryName'
                os.mkdir(full_path) # making dir for end results

                href = s.select_one('.CategoryCard').attrs['href'] # subcategory link 
                amount = s.select_one('.CategoryCard__label').text.split(' ')[0] # number of products in subcategory 
                
                products = crawl_pages(fmt+href, fmt, full_path) # explore each page in subcategory 

                # subcategory is a dictionary
                item = {
                    'sub name': title, 
                    'sub link': fmt+href, 
                    'sub amount': amount, 
                    'products': products
                }
                # list with subcategories
                sub.extend(item) # [{...subcatInfo, {Products}}}, {...subcatInfo, {Products}}]

        # no subcategories
        else: 
            # no link to subcategory, so explore products in category
            logging.debug('No subcategories')
            products = crawl_pages(url, fmt, path)

            # subcategory is a dictionary
            item = {
                'sub name': 'No subcategories',   
                'products': products
            }
            sub.extend(item) # [{'No subcategories': {Products}}]
    return sub 


def get_categories(url, name):  
    """
            url - url to catgeory 
            name - name of shop (to create dir to save products)

            returns [{CategoryName, Link, {Subcategories}}, ... etc]
    """
    soup = get_soup(url)  
    cats = []
    if soup is None: 
        logging.warning(f'No soup for {url}')
    else:  
        # for each category item 
        for cat in soup.select('.CategoriesMenuListItem'):  
            title = cat.attrs['title'] # title of the category
            logging.debug(f'Category: {title}')

            # directory for each category
            full_path = os.path.join(os.path.dirname(__file__), "..", 'data', name, title).strip()
            os.mkdir(full_path) 

            href = cat.select_one('.CategoriesMenuListItem__link').attrs['href'] # link to the category 
            subs = parse_sub_categories(url = url + href, fmt = url, path = full_path) # subcategories [{SubCat: {prods}}, {SubCat: {prods}}]

            # category is a dictionary
            item = {
                'category name': title, 
                'link': url + href, 
                'sub categories': subs
            }
            cats.extend(item)
    return cats


FILE_NAME = 'products.json'
SHOPS = [
    {'name': 'auchan', 'url': 'https://auchan.zakaz.ua'}, 
    {'name': 'eko', 'url': 'https://eko.zakaz.ua'}, 
    {'name': 'megamarket', 'url': 'https://megamarket.zakaz.ua'}, 
    {'name': 'metro', 'url': 'https://metro.zakaz.ua'},  
    {'name': 'novus', 'url': 'https://novus.zakaz.ua'},  
    {'name': 'varus', 'url': 'https://varus.zakaz.ua'},
    ]

for shop in SHOPS:
    logging.debug(f'Shop{shop["name"]}')
    data = get_categories(shop['url'], shop['name'])  
