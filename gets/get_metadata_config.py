import json
import math
import os
import logging
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
        saving data = {product: {category, subcategory}} to filename.json
    """
    kwargs.setdefault('ensure_ascii', False)
    kwargs.setdefault('indent', 2)
    full_path = os.path.join(os.path.dirname(__file__), '..', 'data', filename)

    # file not created yet
    if not os.path.isfile(full_path):
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, **kwargs)

    # work with created file
    with open(full_path, 'r+', encoding='utf-8') as f:

        # get file content
        file_data = json.load(f) 

        # check each product in data to add
        for k in data.keys():

            file_data.setdefault(k, {})  
            file_data[k].setdefault('category', []) 
            file_data[k].setdefault('subcategory', []) 
            
            # (sub)category-value exist in product?
            if data[k]['category'] not in file_data[k]['category']:
                file_data[k]['category'].append(data[k]['category']) 
                file_data[k]['subcategory'].append(data[k]['subcategory'])

        # add updated data to file 
        f.seek(0)
        json.dump(file_data, f, **kwargs)

    logging.debug(f'Saved data to file: {filename}')


def get_products(url, cat, subcat):
    """
            returns products = {
                title:
                {
                    category: category_name,
                    subcategory: subcategory_name
                }
            }
    """
    soup = get_soup(url)
    products = {}
    if soup is None:
        logging.warning(f'No soup for {url}')
    else:
        for p in soup.select('.ProductsBox__listItem'):
            if p.select_one('.ProductTile_withOpacity') is not None:  # Product not available
                break
            title = p.select_one('.ProductTile__title').text
            products[title] = {'category': cat, 'subcategory': subcat}
    return products


def crawl_pages(url, cat, subcat):
    """
            returns products_on_page = {
                title:
                {
                    category: category_name,
                    subcategory: subcategory_name
                }
            }
    """
    products_on_page = {}
    soup = get_soup(url)
    fmt_page = url + '?page={}'

    if soup is None:
        logging.warning(f'No soup for {url}')
    else:

        # Getting number of pages
        amount = (soup.select_one('.FilterableLayout__productsCount') or soup.select_one(
            '.SecondLevelCategory__goodsNumber')).text
        amount = int(amount.split(' ')[0])
        pages_count = min(math.ceil(amount / 30 + 1),
                        int(soup.select('.Pagination__item')[-1].text) if soup.select('.Pagination__item') else 1)

        # For each page getting products
        for i in range(1, pages_count + 1):
            logging.debug(f'Start crawling page: {str(i)}')
            url = fmt_page.format(i)
            products_on_page.update(get_products(url=url, cat=cat, subcat=subcat))
    return products_on_page


def get_sub_categories(url, fmt, cat):
    """
            returns subs = {
                title:
                {
                    category: category_name,
                    subcategory: subcategory_name
                }
            }
    """
    subs = {}
    soup = get_soup(url)
    if soup is None:
        logging.warning(f'No soup for {url}')
    else:
        # subcategories exist
        if soup.select('.CategoriesBox__list'):

            # Get products for each subcategory for each page
            for s in soup.select('.CategoriesBox__listItem'):
                title = s.select_one('.CategoryCard__title').text
                logging.debug(f'Subcategory: {title}')
                href = s.select_one('.CategoryCard').attrs['href']
                subs.update(crawl_pages(url=fmt + href, cat=cat, subcat=title))

        # no subcategories
        else:
            # Get products for category for each page
            logging.debug('No subcategories')
            subs.update(crawl_pages(url, cat=cat, subcat="No subcategories"))
    return subs


def get_categories(url, name):
    """
            returns cats = {
                title:
                {
                    category: category_name,
                    subcategory: subcategory_name
                }
            }
    """
    cats = {}
    soup = get_soup(url)
    if soup is None:
        logging.warning(f'No soup for {url}')
    else:
        # Get products for each category
        for cat in soup.select('.CategoriesMenuListItem'):
            title = cat.attrs['title']
            logging.debug(f'Category: {title}')
            href = cat.select_one('.CategoriesMenuListItem__link').attrs['href']
            cats.update(get_sub_categories(url=url+href, fmt=url, cat=title))
            dump_to_json(name, cats)
    return cats


FILE_NAME = 'metadata_config.json'
SHOPS = [
    {'name': 'auchan', 'url': 'https://auchan.zakaz.ua'},
    {'name': 'eko', 'url': 'https://eko.zakaz.ua'},
    {'name': 'megamarket', 'url': 'https://megamarket.zakaz.ua'},
    {'name': 'metro', 'url': 'https://metro.zakaz.ua'},
    {'name': 'novus', 'url': 'https://novus.zakaz.ua'},
    {'name': 'varus', 'url': 'https://varus.zakaz.ua'},
]
for shop in SHOPS:
    logging.debug(f'Shop: {shop["name"]}')

    file_name = shop['name'] + "_" + FILE_NAME
    get_categories(shop['url'], os.path.join(shop['name'], file_name))
