import os
from get_products_by_dirs import dump_to_json
from bs4 import BeautifulSoup
import requests

def get_soup(url, **kwargs): 
    """
        returns soup for url or None
    """
    response = requests.get(url, **kwargs)
    if response.status_code == 200:
        return BeautifulSoup(response.text, features='html.parser')
    return None


def get_sub_categories(url, fmt):
    """
    :param url:
    :param fmt:
    :return: sub = {
        title: amount
    }
    """
    soup = get_soup(url)  
    sub = {}
    if soup is None: 
        print('No soup') 
    else: 
        if soup.select('.CategoriesBox__list'): 
            for s in soup.select('.CategoriesBox__listItem'): 
                title = s.select_one('.CategoryCard__title').text
                amount = int(s.select_one('.CategoryCard__label').text.split(' ')[0])
                sub[title] = amount 
        else: 
            sub = 'No subcategories'
    return sub 


def get_categories(url):
    """
    :param url:
    :return:
    cats = [
        {'Category': title, 'SubCategories': subs},
        {'Category': title, 'SubCategories': subs},
        ...
    ]
    """
    soup = get_soup(url)  
    cats = []
    if soup is None: 
        print('No soup') 
    else: 
        for cat in soup.select('.CategoriesMenuListItem'):   
            href = cat.select_one('.CategoriesMenuListItem__link').attrs['href']
            subs = get_sub_categories(url+href, url)
            title = cat.attrs['title']
            print('\t' + title)
            item = {'Category': title, 'SubCategories': subs}
            cats.append(item)
    return cats


FILE_NAME = 'metadata.json'
SHOPS = [
    {'name': 'auchan', 'url': 'https://auchan.zakaz.ua'}, 
    {'name': 'eko', 'url': 'https://eko.zakaz.ua'}, 
    {'name': 'megamarket', 'url': 'https://megamarket.zakaz.ua'}, 
    {'name': 'metro', 'url': 'https://metro.zakaz.ua'},  
    {'name': 'novus', 'url': 'https://novus.zakaz.ua'},  
    {'name': 'varus', 'url': 'https://varus.zakaz.ua'},
    ]

for shop in SHOPS: 
    print(shop['name'])
    filename = os.path.join(shop['name'], FILE_NAME)
    cats = get_categories(shop['url']) 
    dump_to_json(filename, cats)
