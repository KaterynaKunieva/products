from bs4 import BeautifulSoup
import requests
import json 
import math
import os 
import logging

logging.basicConfig(filename='../metadata.log', level=logging.DEBUG)

FILE_NAME = 'product_list.json'
SHOPS = [
    {'name': 'auchan', 'url': 'https://auchan.zakaz.ua'}, 
    {'name': 'eko', 'url': 'https://eko.zakaz.ua'}, 
    {'name': 'megamarket', 'url': 'https://megamarket.zakaz.ua'}, 
    {'name': 'metro', 'url': 'https://metro.zakaz.ua'},  
    {'name': 'novus', 'url': 'https://novus.zakaz.ua'},  
    {'name': 'varus', 'url': 'https://varus.zakaz.ua'},
]

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
            filename - path to (sub)category to save data
            data - list of products titles 
            saving data to json = [] in dir data
    """
    kwargs.setdefault('ensure_ascii', False)
    kwargs.setdefault('indent', 2)  

    # all will be saved in dir data + filename 
    full_path = os.path.join(os.path.dirname(__file__), '..', 'data', filename).strip()

    # if file not created yet
    if not os.path.isfile(full_path): 
        with open(full_path, 'w', encoding='utf-8') as f:  
            json.dump([], f, **kwargs)
            logging.debug(f'Created file: {filename}')
    
    with open(full_path, 'a+', encoding='utf-8') as f: 
        # file_data = json.load(f) # saving data from file 
        # file_data = [*file_data, *data] # adding new data
        
        # # rewriting updated data to file  
        # f.seek(0)
        json.dump(data, f, **kwargs) 
        logging.debug(f'Saved data to file: {filename}')


def get_products(url, path): 
    """
            returns a list of products by url [title1, title2, title3, ...]
    """
    soup = get_soup(url) 
    products = []
    if soup is None: 
        logging.warning(f'No soup for product {url}')
    else: 
        # parsing each product-card
        for p in soup.select('.ProductsBox__listItem'): 
            if p.select_one('.ProductTile_withOpacity') is not None: # Product not available
                break
            product_title = p.select_one('.ProductTile__title').text  
            products.append(product_title) 
    full_path = os.path.join(path, FILE_NAME).strip() # path to save end list with products titles category/subcategory/product_list.json
    dump_to_json(full_path, products)
    return products


def crawl_pages(url, path): 
    """
            returns list of products titles on page by url [title1, title2, title3, ...]
    """ 
    products_on_page = [] 
    soup = get_soup(url)  
    fmtp = url + '?page={}'

    if soup is None: 
        logging.warning(f'No soup for page {url}')
    else: 
        # Getting number of pages
        amount = (soup.select_one('.FilterableLayout__productsCount') or soup.select_one('.SecondLevelCategory__goodsNumber')).text  
        amount = int(amount.split(' ')[0])
        pages_count = min(math.ceil(amount/30 + 1), int(soup.select('.Pagination__item')[-1].text) if soup.select('.Pagination__item') else 1)

        # For each page getting products
        for i in range(1, pages_count+1): 
            logging.debug(f'Page: {str(i)}') 
            url = fmtp.format(i) 
            products_on_page.extend(get_products(url = url, path = path)) 
    
    return products_on_page


def get_sub_categories(url, fmt, path):
    """
            returns a list of products titles in subcategory by url [title1, title2, title3, ...]
    """

    soup = get_soup(url)  
    products_in_sub = [] 
    if soup is None: 
        logging.warning(f'No soup for subcategory {url}')
    
    else: 
        # subcategories exist
        if soup.select('.CategoriesBox__list'): 

            # Get products for each subcategory for each page
            for s in soup.select('.CategoriesBox__listItem'): 
                title = s.select_one('.CategoryCard__title').text
                logging.debug(f'Subcategory: {title}') 
                full_path = os.path.join(path, title).strip()
                href = s.select_one('.CategoryCard').attrs['href']
                products_in_sub.extend(crawl_pages(url = fmt+href, path = full_path))

        # no subcategories
        else: 
            # logging.debug('Category with no subcategories') 
            # full_path = path.strip() 
            products_in_sub.extend(crawl_pages(url = url, path = path.strip()))
    return products_in_sub


def get_categories(url, path):  
    """
            returns list of products titles in category by url [title1, title2, title3, ...]
    """
    soup = get_soup(url)  
    products_in_cat = []
    if soup is None: 
        logging.warning(f'No soup for category {url}')
    else:  
        for cat in soup.select('.CategoriesMenuListItem'):  
            title = cat.attrs['title']
            logging.debug(f'Category: {title}')
            
            href = cat.select_one('.CategoriesMenuListItem__link').attrs['href']
            path_to_cat = os.path.join(path, title).strip() 
            products = get_sub_categories(url = url + href, fmt = url, path = path_to_cat) 
            products_in_cat.extend(products)
    return products_in_cat


for shop in SHOPS:
    logging.debug(f'Shop{shop["name"]}')  
    data = get_categories(url = shop['url'], path = shop['name'])
