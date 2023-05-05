import os 
FILE_NAME = 'product_list.json'
# FILE_NAME = 'product_brands.json'
path = os.path.join(os.path.dirname(__file__), '../data')
for root, dirs, files in os.walk(path): 
    for file in files: 
        if file == FILE_NAME: 
            p = os.path.join(path, root, file) 
            os.remove(p)