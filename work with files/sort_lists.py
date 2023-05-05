import os 
import json 
FILE_NAME = 'product_list.json'
# FILE_NAME = 'product_brands.json'
path = os.path.join(os.path.dirname(__file__), '../data')
for root, dirs, files in os.walk(path): 
    for file in files: 
        if file == FILE_NAME: 
            p = os.path.join(path, root, file) 
            with open(p, 'r+', encoding='utf-8') as f: 
                file_data = json.load(f) 
                file_data.sort()
            with open("path", "w") as f: 
                json.dump(file_data, f, ensure_ascii=False, indent=2) 