import json 
import os 

with open('./config/word_dict.json', mode='r', encoding='utf-8') as file:
    word_dict = json.load(file)
print(word_dict)