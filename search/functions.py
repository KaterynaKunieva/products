import os
import json


def find_product_hierarchy(name):
    """
    :param name:
    :return:
    {'category': ['', ''], 'subcategory': ["", ""]}
    """
    # relative path ro product
    hierarchy = {}

    # path to data
    path_to_data = os.path.join(os.path.dirname(__file__), '..', 'data')
    filename = 'metadata_config.json'

    # paths to shop_metadata_config.json
    names_of_shops = ['auchan', 'eko', 'megamarket', 'metro', 'novus', 'varus']
    paths_to_shops = list(map(lambda name: os.path.join(path_to_data, name, name + "_" + filename), names_of_shops))

    for path in paths_to_shops:
        # work with file
        with open(path, 'r', encoding="utf-8") as f:
            file_content = f.read()
            file_content_json = json.loads(file_content)

        # search in content
        try:
            hierarchy[path] = file_content_json[name]
        except KeyError:
            hierarchy[path] = 'No such product'
    return hierarchy


def paths_from_hierarchy(hierarchy):
    paths = []
    for key in hierarchy.keys():
        if hierarchy[key] != 'No such product':
            for i in range(0, len(hierarchy[key]['category'])):
                if hierarchy[key]['subcategory'][i] == 'No subcategory':
                    path = os.path.join('\\'.join(key.split('\\')[0:-1]), hierarchy[key]['category'][i])
                else:
                    path = os.path.join('\\'.join(key.split('\\')[0:-1]), hierarchy[key]['category'][i], hierarchy[key]['subcategory'][i])
                # print(os.listdir(path))
                paths.append(path)
    return paths


def find_info_in_file(paths, name):
    filename = 'products.json'

    full_paths = []
    info = {}
    for path in paths:
        full_paths.append(os.path.join(path, filename))
    for full_path in full_paths:
        with open(full_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            file_content_json = json.loads(file_content)
            for content in file_content_json:
                if content[name] == name:
                    info[': '.join(full_path.split('\\')[16:-1])] = content
    return info


def search_product(name):
    hierarchy = find_product_hierarchy(name=name)
    paths = paths_from_hierarchy(hierarchy)
    info = find_info_in_file(paths, name=name)
    return info


def main():
    search_name = "Вино Bolgrad Chateau de Vin червоне напівсолодке 9-15% 1,5л"
    for key, value in search_product(search_name).items():
        print(f'У магазині `{key.split(" ")[0][0:-1].capitalize()}` товар `{search_name}` знаходиться в категорії `{" ".join(key.split(" ")[1:])}` і має наступні характеристики: ')
        [print('\t', k, ": ", v) for k, v in value.items()]
        print()


main()

