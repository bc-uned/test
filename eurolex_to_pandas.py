# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 11:07:07 2024

@author: q30930

"""
import re
import yaml
import pandas as pd
from bs4 import BeautifulSoup

def clean_text(text):
    
    text = re.sub('\u00A0', ' ', text) # Non-breaking space to space    
    
    # text = re.sub(r'\u25BA.*?\n?.*?\u25C4', '', text) # Quita todo entre ► y ◄
    text = re.sub(r'►.\d\d?\n', ' ', text) # Quita todo entre ► y ◄    
    text = re.sub(r'◄', ' ', text) # Quita todo entre ► y ◄    
    
    # Step 3: Replace multiple spaces and newlines with a single space or newline
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    
    # Step 1: Remove all spaces that are not between two letters or after punctuation
    # text = re.sub(r'(?<!\w)(?<![.,!?;:\'\"-\(\)]) | (?!\w)', '', text)
    
    # Remove spaces after '(' and before ')'
    text = re.sub(r'\(\s+', '(', text)
    text = re.sub(r'\s+\)', ')', text)    
    
    # Step 4: Eliminate newlines that don't have a period before or a capital letter after
    text = re.sub(r'(?<![\.;])\n(?![A-Z\(\)\d])', ' ', text)
    
    # Step 5: Newlines at the beginning or the end
    text = re.sub(r'^\n+|\n+$', '', text)
    
    return text
   
text = """(e) require the 
►M3
 entity ◄  to limit or cease specific existing or proposed activities;
(f) restrict or prevent the development of new or existing business lines or sale of new or existing products;
(g) require changes to legal or operational structures of the 
►M3
 entity ◄  or any group entity, either directly or indirectly under its control, so as to reduce complexity in order to ensure that critical functions may be legally and operationally separated from other functions through the application of the resolution tools;
1(h) require an 
►M3
 entity ◄  or a parent undertaking to set up a parent financial holding company in a Member State or a Union parent financial holding company;
"""


try:
    with open(r'C:\TRABAJO\_HKT\Datasets\EUR_Lex.yml', 'r', encoding='utf-8') as f:
        # Load the entire file as a single document
        eur_lex = yaml.safe_load(f)
except FileNotFoundError:
    print("Error: EBA_rulebook.yml not found.")
    exit(1)  # Exit with an error code
except yaml.YAMLError as e:
    print(f"Error parsing EBA_rulebook.yml: {e}")
    exit(1)

#%% flatten and to excel:

def flatten_EURLex(eur_lex, parent_full_id='', parent_short_name='', level=0):
    rows = []
    #TODO make shure that sub-paragraphs are one level lower than paragphahs, which is not alwaws the case.
    for item in eur_lex:
        full_id = f"{parent_full_id}·{item['id']}" if parent_full_id else item['id']
        metadata = item.get('metadata', {})
        row = {
            'full_id': full_id,
            'id': item['id'],
            'parent_id': parent_full_id,
            'level': level,
            'text': item.get('text', ''),            
            'clean_text': clean_text(item.get('text', '')),
            'metadata': metadata,
            # 'type': metadata.get('type', ''),
            'type': metadata.get('level', ''),            
            'short_name': metadata.get('short_name', parent_short_name),
            'parser' : item['parser'],
        }
        if row['text'].strip(): # Salta la fila si son solo caracteres en blanco.
            rows.append(row)
            
        if 'children' in item:
            rows.extend(flatten_EURLex(item['children'], full_id, row['short_name'], level + 1))
    return rows

flattened_data = flatten_EURLex(eur_lex)
df = pd.DataFrame(flattened_data)


df.to_excel('C:\TRABAJO\_HKT\Datasets\eur_lex.xlsx', index=False)

#%% Prepare to compare articles

filter_en = df.full_id.str.contains(r"_en")
filter_de = df.full_id.str.contains(r"_de")


df_art_en = df[filter_en][['short_name', 'full_id', 'level', 'type', 'short_name', 'parser']]
df_art_de = df[filter_de][['short_name', 'full_id', 'level', 'type', 'short_name', 'parser']]
df_art_en['lang'] = 'en'
df_art_de['lang'] = 'de'

df_art = pd.concat([df_art_en,df_art_de], axis=0)

def normalize_full_id(full_id):
    # Dictionary to map Roman numerals to integers
    roman_to_int = {
        'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5',
        'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10',
        'XI': '11', 'XII': '12', 'XIII': '13', 'XIV': '14', 'XV': '15',
        'XVI': '16', 'XVII': '17', 'XVIII': '18', 'XIX': '19', 'XX': '20'}
    
    
    # Function to replace Roman numerals with integers
    def replace_roman_numerals(match):
        roman_numeral = match.group(1)
        return 'prt_' + roman_to_int[roman_numeral]
    
    
    if type(full_id) is pd.Series:
        series = full_id.str.replace(r"\(|\)|_en|_de|\.|‘|„|►[CM]\d|‚", "", regex=True)

        # Replace Roman numerals
        series = series.str.replace(r'prt_(XX|XIX|XVIII|XVII|XVI|XV|XIV|XIII|XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)', replace_roman_numerals, regex=True)
    
        re        
        
        
        

    
df_art['normalized_id'] = df_art['full_id'].str.replace(r"\(|\)|_en|_de|\.|‘|„|►[CM]\d|‚", "", regex=True)




# Replace Roman numerals
df_art['normalized_id'] = df_art['normalized_id'].str.replace(r'prt_(XX|XIX|XVIII|XVII|XVI|XV|XIV|XIII|XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)', replace_roman_numerals, regex=True)


df_art.to_excel('C:\TRABAJO\_HKT\Datasets\df_articles.xlsx', index=False)


#%% Couunt all letters in column
import pandas as pd
from collections import Counter


# Concatenate all text in the "text" column
all_text = ''.join(df['text'])

# Count all UTF-8 characters in the concatenated text
char_count = Counter(all_text)

# Create a new dataframe with character representation, utf-8 code, and count
char_data = {
    'character': list(char_count.keys()),
    'utf-8 code': [ord(c) for c in char_count.keys()],
    'count': list(char_count.values())
}

char_df = pd.DataFrame(char_data)

print(char_df)


char_df.to_excel('C:\TRABAJO\_HKT\Datasets\char_df.xlsx', index=False)


#%% Create files to make shure scrapping got everithing:
data_dir = f'C:\TRABAJO\_HKT\Datasets\EUR_Lex/'

with open(f'{data_dir}IRSB_main_pages.yml', 'r') as f:
    # Load the entire file as a single document
    IRSB = yaml.safe_load(f)


import yaml
data_dir = f'C:\TRABAJO\_HKT\Datasets\EUR_Lex/'


with open(f'{data_dir}IRSB_main_pages.yml', 'r') as f:
    # Load the entire file as a single document
    IRSB = yaml.safe_load(f)

print("**** Escrbiendo archivos html ****")

eur_lex = []
    
for regulation in IRSB:   
    metadata = {k:v for k,v in regulation.items() if k not in ['de_text','en_text']}
    for url_key, lang in [('EURLex_url','main'), ('en_text','en'), ('de_text','de'), ]:
        
        load_from_file_name =  data_dir + f'{regulation["legal_act_short_code"]}_{lang}.html'         
        
        if load_from_file_name:
            # Read from the plain text file
            # print(f'reading from filename: {load_from_file_name}')
            with open(load_from_file_name, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
        
    
        eli_container = soup.find('div', class_='eli-container')
        
        if not eli_container:
            eli_container = soup.find('div', {'id': 'document1', 'class': 'tabContent'})
        
        if not eli_container:
            print("**** Error no existen  eli-container ni tabContent *** No se puede parsear ****")
       
        full_text = clean_text(eli_container.get_text(strip=False))
        
        full_text = re.sub(r'\)(\s+)\n', ') ', full_text)
        full_text = re.sub(r'(\d[\d|a-f]?\.)(\s+)\n', r'\1 ', full_text)        
        full_text = re.sub(r"▼\w+\n?", '', full_text) 
        
        for exp in ['replaced by the following:' , "is added:",
                    "point is inserted:","amended as follows:",
                    'following formula:', ]:
            full_text = re.sub(f'{exp} ', f'{exp}\n', full_text)     


        with open(data_dir + f'Comparison\html\{lang}\{regulation["legal_act_short_code"]}.txt', "w", encoding='utf-8') as file:
            file.write(full_text)        
        
    
    
full_text = """
1. 
This Directive applies to investment firms authorised and supervised under Directive 2014/65/EU.
2. 
By way of derogation from paragraph 1, Titles IV and V of this Directive do not apply to investment firms referred to in Article 1(2) and (5) of Regulation (EU) 2019/2033, which shall be supervised for compliance with prudential requirements under Titles VII and VIII of Directive 2013/36/EU in accordance with the second subparagraph of Article 1(2) and third subparagraph of Article 1(5) of Regulation (EU) 2019/2033.
1. 
Member States shall designate one or more competent authorities to carry out the functions and duties provided for in this Directive and in Regulation (EU) 2019/2033. The Member States shall inform the Commission, EBA and ESMA of that designation, and, where there is more than one competent authority, of the functions and duties of each competent authority.
2. 
Member States shall ensure that the competent authorities supervise the activities of investment firms, and, where applicable, of investment holding companies and mixed financial holding companies, to assess compliance with the requirements of this Directive and of Regulation (EU) 2019/2033.
3. 
Member States shall ensure that the competent authorities have all necessary powers, including the power to conduct on‐the‐spot checks in accordance with Article 14, to obtain the information needed to assess the compliance of investment firms and, where applicable, of investment holding companies and mixed financial holding companies, with the requirements of this Directive and of Regulation (EU) 2019/2033, and to investigate possible breaches of those requirements.
4. 
Member States shall ensure that the competent authorities have the expertise, resources, operational capacity, powers and independence necessary to carry out the functions relating to the prudential supervision, investigations and sanctions set out in this Directive.
5. 
Member States shall require investment firms to provide their competent authorities with all the information necessary for the assessment of the compliance of investment firms with the national provisions transposing this Directive and compliance with Regulation (EU) 2019/2033. Internal control mechanisms and administrative and accounting procedures of the investment firms shall enable the competent authorities to check their compliance with those provisions at all times.
6. 
Member States shall ensure that investment firms record all their transactions and document the systems and processes which are subject to this Directive and to Regulation (EU) 2019/2033 in such a manner that the competent authorities are able to assess compliance with the national provisions transposing this Directive and compliance with Regulation (EU) 2019/2033 at all times.
"""

    
    
print("**** Escrbiendo archivos scrapeados ****")

previous_reg = flattened_data[0]['full_id'].split('·')[0]
all_text = []

for line in flattened_data:
    reg = line['full_id'].split('·')[0]
    if reg == previous_reg:
        all_text.append(line['clean_text'])
    else:
        full_text = '\n'.join(all_text)
        a = previous_reg.split('_')
        if len(a) == 1:
            lang = 'main'
        else:
            lang = a[1]
        
        regulation = a[0]
        
        full_text = re.sub(r"point is inserted: ", r'point is inserted:\n', full_text) 
        full_text = re.sub(r"replaced by the following: ", r'replaced by the following:\n', full_text)         
        full_text = re.sub(r"is added:: ", r'is added:\n', full_text)         
                
        with open(data_dir + f'Comparison\scrapped\{lang}\{regulation}.txt', "w", encoding='utf-8') as file:
            file.write(full_text)          
        
        previous_reg = reg
        all_text = [line['clean_text'],]
        
        
 
#%% 
       
        
    
    

#%% 














eur_lex = []
    
for regulation in IRSB:   
    metadata = {k:v for k,v in regulation.items() if k not in ['de_text','en_text']}
    for url_key, lang in [('EURLex_url','main'), ('en_text','en'), ('de_text','de'), ]:
    # for url_key, lang in [('de_text','de'), ]:        
    # for url_key, lang in [('en_text','en'), ]: 

        if DEBUG and regulation['legal_act_short_code'] != "WTR":
            continue
               
        url = regulation[url_key]
        metadata['lang'] = lang 
        print(f'*** Parsing {regulation["legal_act_short_code"]} ({regulation["legal_act"]}) in language {lang}')
        lex = parse_eur_lex(url,metadata, load_from_file_name =  data_dir + f'{regulation["legal_act_short_code"]}_{lang}.html' )
        
        parsed = {'id':   regulation['legal_act_short_code'] + ( '' if lang == 'main' else ( '_' + lang)) , 
                      'text': regulation['legal_act'],
                      'metadata': {'CELEX' : regulation['CELEX'] ,
                                   'short_name' :  regulation['legal_act_short_code'] ,
                                   'url' : url ,
                                   'level': 'legal_act',
                                   'type' : regulation['legal_act_type'],
                                   'ISRB':  regulation['ISRB'],
                                   'ISRB_url' : regulation['ISRB_url'],
                                   'lang' : lang,
                                   # 'total_nodes' : len(lex),
                                   }, 
                      'iteration': 0,
                      'parser': inspect.currentframe().f_code.co_name,
                      'children': lex}
    
        eur_lex.append(parsed)
    



#%%

# from bs4 import BeautifulSoup

# # Read from the plain text file
# with open(r'C:\TRABAJO\_HKT\Datasets\eli_container.html', 'r', encoding='utf-8') as f:
#     html_content = f.read()

# # Convert to BeautifulSoup element
# eli_container = BeautifulSoup(html_content, 'html.parser').find('div', class_='eli-container')


def print_function_name(func):
    def wrapper(*args, **kwargs):
        print(f"Calling function: {func.__name__}")
        return func(*args, **kwargs)
    return wrapper



#%% Parser

import requests
from bs4 import BeautifulSoup
import json
import yaml
import inspect
import copy
import re
import time
import random
import traceback

iteration = 0
DEBUG = False

def element_text_to_div(element):
    """ devuelve el texto contenido antes del primer div hijo """  
    #Obtiene el texto de todo hasta el primer div
    node_text = ""
    for child in element.children:
        text = None
        # print(child.name)
        if child.name == 'div':
            break
        elif child.name == 'a':
            text = child.get_text(strip=True)
        else:                
            text = child.get_text()
            
        if text:
            node_text += text
            #     node_text += text + "\n"

    # node_text = node_text[:-1] # Quital el último salto de linea
    
    return node_text.strip()

#Law (root node)
#@print_function_name
def parse_eli_main_title(element): # Law
    #TODO añadir CELEX y nombre corto de la ley / directiva
    node_id = element.get('id', '')
    if DEBUG: print(f'iteration: {iteration:>4}, node_id {node_id}') 
    node_text = "\n".join(p.get_text(strip=True) for p in element.find_all('p'))
    
    # Infer metadata level and title from the text
    if "DIRECTIVE" in node_text:
        level = "directive"
    elif "RICHTLINIE" in node_text:
        level = "directive"
    elif "REGULATION" in node_text:
        level = "regulation"
    elif "VERORDNUNG" in node_text:
        level = "regulation"        
    else:
        level = "unknown"
        title = ""
        
    
    metadata = {"level": level, "title": ''}
    children = []
    
    next_sibling = element.find_next_sibling()
    
    return {'id': node_id, 'text': node_text, 'metadata': metadata, 
            'iteration': iteration, 'parser': inspect.currentframe().f_code.co_name,
            'children': children}, next_sibling


#@print_function_name
# Articles, but also a global wrapper.
def parse_articles(element): #  Article
    if DEBUG:
        element2 = copy.deepcopy(element)
        element = copy.deepcopy(element2)
       
    node_id = element.get('id', '')
    if DEBUG: print(f'iteration: {iteration:>4}, node_id {node_id}')    
    local_iteration = iteration
      
    node_text = element_text_to_div(element) #Obtiene el texto de todo hasta el primer div
    next_element = element.find('div') # Importante ponerlo aqui porque eliminamos un div con sub_titles
                    
    # Infer metadata level and title from the text
    if "article" in node_text.lower():
        level = "article"
        title = node_text.split("\n")[0]
    elif "artikel " in node_text.lower():
        level = "article"
        title = node_text.split("\n")[0]
    
    else:
        level = "unknown"
        title = ""
   
    sub_titles = element.find_all(class_='eli-title', recursive=False)
    
    if sub_titles:
        element = copy.deepcopy(element) # Como vamos a borrar, no trabajamos sobre el soup principal.
        sub_titles = element.find_all(class_='eli-title', recursive=False)
        sub_title = sub_titles[0]
        subtitle_text = sub_title.text.strip() 
        sub_title.decompose() # Chapu borrando el subtitulo para que el resto funcione como antes        
        
        title += '\n' + subtitle_text
        #Hay que volver a parsear el texto.
        node_text = title +  '\n' + element_text_to_div(element) #Obtiene el texto de todo hasta el primer div
        node_text = title 
    else:
        subtitle_text = ''

   
    metadata = {"level": level, "title": title, "subtitle": subtitle_text}
    children = []
    
    
    # next_element = element.find()    
    
    # Loop through next div and all next siblings 
    if next_element:
        child_dict, _ = parse_node(next_element, children)
        
        for sibling in next_element.next_siblings:
            child_dict, _ = parse_node(sibling, children)
        
    
    return {'id': node_id, 'text': node_text, 'metadata': metadata,
            'iteration': local_iteration, 'parser': inspect.currentframe().f_code.co_name,
            'children': children}, element.find_next_sibling()

#Section y Chapter
#@print_function_name
def parse_title_division_1(element):
    node_id = element.parent.get('id', '') # Id del nodo padre
    if DEBUG: print(f'iteration: {iteration:>4}, node_id {node_id}') 
    local_iteration = iteration
    # node_text = "\n".join(p.get_text(strip=True) for p in element.find_all('p'))

    title    = element.text.strip()
    sub_text = element.find_next_sibling().text
    
    node_text = title + sub_text
    
    # Infer metadata level and title from the text
    if "SECTION" in title:
        level = "section"
    elif "ABSCHNITT" in title:
        level = "section"        
    elif "CHAPTER" in title:
        level = "chapter"
    elif "KAPITEL" in title:
        level = "chapter"   
    elif "PART" in title:
        level = "part"
    elif "TEIL" in title:
        level = "part"   
    elif "TITLE" in title:
        level = "title"
    elif "TITEL" in title:
        level = "title"           
        
    else:
        level = "unknown"
        title = ""
    
    metadata = {"level": level, "title": title}
    children = []
    
    next_div = element.find('div')
    while next_div:
        child_dict, _ = parse_node(next_div, children)

        next_div = next_div.find_next_sibling('div')
    
    return {'id': node_id, 'text': node_text, 'metadata': metadata,
            'iteration': local_iteration, 'parser': inspect.currentframe().f_code.co_name,
            'children': children}, element.find_next_sibling()

#Annex
#@print_function_name
def parse_annex(element):
    node_id = element.get('id', '') # Id del nodo padre
    if DEBUG: print(f'iteration: {iteration:>4}, node_id {node_id}') 
    # node_text = "\n".join(p.get_text(strip=True) for p in element.find_all('p'))

    annex_div = element.find(class_='title-annex-1') 

    title    = annex_div.get_text(strip=True)
    node_text = title 
    level = "annex"    
    
    metadata = {"level": level, "title": title}
    children = []
    
    next_div = annex_div.find_next_sibling()
    while next_div:
        child_dict, _ = parse_node(next_div, children)

        next_div = next_div.find_next_sibling()
    
    return {'id': node_id, 'text': node_text, 'metadata': metadata, 
            'iteration': iteration, 'parser': inspect.currentframe().f_code.co_name,
            'children': children}, element.find_next_sibling()


#@print_function_name
# Paragraphs within articles
def parse_article_norm(element): # Article.Paragaph

    node_id = element.find(class_='no-parag').get_text(strip=True)
    if DEBUG: print(f'iteration: {iteration:>4}, node_id {node_id}')   
    local_iteration = iteration

    title = ""    
    level = "paragraph"

    # inline_element contiene el texto del parrafo.
    inline_element = element.find(class_='inline-element')
    node_text = node_id + ' ' + element_text_to_div(inline_element) #Obtiene el texto de todo hasta el primer div

    # if node_text.startswith('5. Competent authorities shall'):
    #     print(1)
   
    metadata = {"level": level, "title": title}
    children = []   
    next_div = inline_element.find('div')
    while next_div:
        child_dict, _ = parse_node(next_div, children)

        next_div = next_div.find_next_sibling('div')
    
    return {'id': node_id, 'text': node_text, 'metadata': metadata, 
            'iteration': local_iteration, 'parser': inspect.currentframe().f_code.co_name,
            'children': children}, element.find_next_sibling()

#@print_function_name
# Sub-paragraphs: bullet points or letters within Paragraphs
def parse_sub_paragraph(element, sub_paragraph_no):
    node_id = sub_paragraph_no
    if DEBUG: print(f'iteration: {iteration:>4}, node_id {node_id}')    
    local_iteration = iteration
    
    title = ""    
    level = "sub-paragraph"    
    
    # inline_element contiene el texto del parrafo.
    node_text = element.text
    
    metadata = {"level": level, "title": title}
    children = []
    
    for child in element.find_all(recursive=False):
        child_dict, next_element = parse_node(child, children)
    
    return {'id': node_id, 'text': node_text, 'metadata': metadata,
            'iteration': local_iteration, 'parser': inspect.currentframe().f_code.co_name,
            'children': children}, element.find_next_sibling()

#@print_function_name
# Sub-paragraphs: bullet points or letters within Paragraphs
def parse_grid_container(element):
    node_id = element.find(class_='grid-list-column-1').get_text(strip=True)
    if DEBUG: print(f'iteration: {iteration:>4}, node_id {node_id}')
    local_iteration = iteration    
    
    title = ""    
    level = "sub-paragraph"    
    
    # inline_element contiene el texto del parrafo.
    inline_element = element.find(class_='grid-list-column-2')
    node_text = node_id + ' ' + element_text_to_div(inline_element) #Obtiene el texto de todo hasta el primer div
    
    metadata = {"level": level, "title": title}
    children = []
    
    for child in element.find_all(recursive=False):
        child_dict, next_element = parse_node(child, children)
    
    return {'id': node_id, 'text': node_text, 'metadata': metadata,
            'iteration': local_iteration, 'parser': inspect.currentframe().f_code.co_name,
            'children': children}, element.find_next_sibling()


#@print_function_name
def parse_dlist_definition(element):
    node_id = ''
    node_text = ''
    metadata = {'class': 'dlist-definition'}
    children = []
    
    for child in element.find_all(recursive=False):
        child_dict, next_element = parse_node(child, children)
    
    return {'id': node_id, 'text': node_text, 'metadata': metadata,
            'iteration': iteration, 'parser': inspect.currentframe().f_code.co_name,
            'children': children}, element.find_next_sibling()

def parse_node(node, children_list = [], metadata = {}):
    """ Captura todos los errores en parse_node """
    try:
        return parse_node_error_control(node, children_list, metadata)
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        last_call = tb[-1]
        print(f'***************** parse_node ERROR  in iteration {iteration} *******************************************')
        print(f"Exception: {e}")
        print(f"Function: {last_call.name}")
        print(f"Line: {last_call.lineno} - Code: {last_call.line}")
        try:
            print(f"previous node id: {children_list[-1].get('id', '')}")
        except Exception as e:
            pass
        print(f"node: {str(node)[:200]}")
        print(f'************************************+******************************************************************\n')        
        return None, None
    

def parse_node_error_control(node, children_list = [], metadata = {}): # Main parser
    """ main EUR LEX parser """

    node_info = None
    
    if node is None:
        return None, None
    
    next_element = None
    
    global iteration
    iteration += 1
    
    #if iteration in (428,): #bbc
    #    print('debugging breakpoint here')
    
    # if type(node) == str:
    #     return None, None   
    if node.name == 'div':
        if 'title-article-norm' in node.get('class', []):
            node_info, next_element = parse_articles(node)

        if 'norm' in node.get('class', []):
            node_info, next_element = parse_article_norm(node)
            
        elif ('grid-container' in node.get('class', [])) and \
             ('grid-list' in node.get('class', [])):
            node_info, next_element = parse_grid_container(node)
            
        elif 'dlist-definition' in node.get('class', []):
            node_info, next_element = parse_dlist_definition(node)
            
        elif 'eli-main-title' in node.get('class', []):
            node_info, next_element = parse_eli_main_title(node)
            
        elif 'eli-subdivision' in node.get('class', []):
            node_info, next_element = parse_articles(node)

        # elif node.find() and ('separator-annex' in node.find().get('class', [])):
        #     # Hay por lo menos un hijo, find() devuelve el primer hijo
        #     node_info, next_element = parse_annex(node)

        # Verifica si entre los 5 primeros hijos, hay in separator-annex
        elif any(['separator-annex' in n.get('class', []) if n.name else False for n in list(node.children)[:5]]):
            # Hay por lo menos un hijo, find() devuelve el primer hijo
            node_info, next_element = parse_annex(node)
            
        else:
            for child in node.find_all(recursive=False):
                _, next_element = parse_node(child, children_list) # Los hijos se auto-insertan en children_list
    
    elif node.name == 'p' and 'title-division-1' in node.get('class', []):
        node_info, next_element = parse_title_division_1(node)
    
    #Parrafos no númerados
    elif node.name == 'p' and 'norm' in node.get('class', []) \
         and 'grid-list-column-2' not in node.parent.get('class', []):        
        node_info, next_element = parse_sub_paragraph(node, sub_paragraph_no = 0)

    #Comentarios a una lista (dentro de un parrafo)
    elif node.name == 'p' and 'list' in node.get('class', []):        
        node_info, next_element = parse_sub_paragraph(node, sub_paragraph_no = 1)
            

    if node_info: children_list.append(node_info)
        
    return node_info if node_info else None, next_element

def parse_eur_lex(url, document_metadata = {}, save_to_file_name = None, load_from_file_name = None):
    global iteration
    iteration = 0
    
    if load_from_file_name:
        # Read from the plain text file
        # print(f'reading from filename: {load_from_file_name}')
        with open(load_from_file_name, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
    else:
        request_error = True
        # print(f'Scraping from url: {url}')
        for attempt in range(5):  # Retry up to 5 times
            try:
                # Send a GET request to the page
                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for bad status codes
                request_error = False
            except requests.exceptions.RequestException as e:
                print(f"Error during request (attempt {attempt + 1}): {e}")
                wait_time = random.uniform(attempt + 1 - 0.7, attempt + 1 + 0.7)  # Increasing wait time with jitter
                print(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
    
        if request_error:
            print("Failed to retrieve the page after multiple attempts.")
            return None  # Return None if all attempts fail

        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, 'html.parser')
    
    if save_to_file_name:
        # Save to a plain text file
        with open(save_to_file_name, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
    eli_container = soup.find('div', class_='eli-container')
    
    if not eli_container:
        eli_container = soup.find('div', {'id': 'document1', 'class': 'tabContent'})
    
    if not eli_container:
        print("**** Error no existen  eli-container ni tabContent *** No se puede parsear ****")
        return []
    
    #TODO pendiente tratar referencias externas de modificación : class_='modref'
    # Elimina todas las referencias externas de modificación: class_='modref'
    for element in eli_container.find_all(class_='modref'):
        element.decompose()

    #Limpia saltos de lineas no deseados:    
    eli_container_str = str(eli_container)   
    if isinstance(eli_container_str, str):
        # eli_container_str = re.sub(r'</a>\n*<span', '</a><span', eli_container_str) # replaces any newlines between </a> and <span> with nothing.
        eli_container_str = re.sub(r'(<a[^>]*>)\n\W*(<span)', r'\1\2', eli_container_str)        
        eli_container_str = re.sub(r'(<\/span>)\n\W*(<\/a>)', r'\1\2', eli_container_str) # does the same for the whitespace between </span> and </a>.
        eli_container_str = re.sub(r'[\u00A0\u202F]', ' ', eli_container_str) # Replace non breaking spaces.                
        eli_container =  BeautifulSoup(eli_container_str, 'html.parser').find('div', class_='eli-container')    

        if not eli_container:
            eli_container = BeautifulSoup(eli_container_str, 'html.parser').find('div', {'id': 'document1', 'class': 'tabContent'})        
        
    global paragraph_counter
    paragraph_counter = [0]
    
    tree_structure = []
    
    _, _ = parse_node(eli_container, tree_structure, metadata = document_metadata) # tree_structure se modifica por referencia.
    
    return tree_structure

def concatenate_text(tree_structure):
    result = []

    def traverse(node):
        result.append(node['text'])
        for child in node.get('children', []):
            traverse(child)

    for element in tree_structure:
        traverse(element)

    return '\n'.join(result)
            
#composed_text = concatenate_text(tree_structure)

"""
#@print_function_name
def parse_eur_lex2(eli_container = eli_container):
    tree_structure = []
    
    #TODO pendiente tratar referencias externas de modificación : class_='modref'
    # Elimina todas las referencias externas de modificación: class_='modref'
    for element in eli_container.find_all(class_='modref'):
        element.decompose()

    #Limpia saltos de lineas no deseados:    
    eli_container_str = str(eli_container)   
    if isinstance(eli_container_str, str):
        # eli_container_str = re.sub(r'</a>\n*<span', '</a><span', eli_container_str) # replaces any newlines between </a> and <span> with nothing.
        eli_container_str = re.sub(r'(<a[^>]*>)\n\W*(<span)', r'\1\2', eli_container_str)        
        eli_container_str = re.sub(r'(<\/span>)\n\W*(<\/a>)', r'\1\2', eli_container_str) # does the same for the whitespace between </span> and </a>.
        eli_container_str = re.sub(r'[\u00A0\u202F]', ' ', eli_container_str) # Replace non breaking spaces.        
        
        eli_container =  BeautifulSoup(eli_container_str, 'html.parser').find('div', class_='eli-container')
  
        
    _, _ = parse_node(eli_container, tree_structure) # tree_structure se modifica por referencia.
    
    return tree_structure

# Test the function with the provided URL
url = 'https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02015L0849-20240709'
#tree_structure = parse_eur_lex(url)


#Test sin llamar a requests
tree_structure = parse_eur_lex2()



# Pretty print the dictionary
# print(json.dumps(tree_structure, indent=4))
        
with open(r'C:\TRABAJO\_HKT\Datasets/TestEURLEX.yml', 'w', encoding='utf-8') as f:
    yaml.dump(tree_structure, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

"""


#%% Loop thru regulations

    
    C:\TRABAJO\_HKT\Datasets\EUR_Lex\Comparison\html
    

    
    # for url_key, lang in [('de_text','de'), ]:        
    # for url_key, lang in [('en_text','en'), ]: 

        if DEBUG and regulation['legal_act_short_code'] != "WTR":
            continue
               
        url = regulation[url_key]
        metadata['lang'] = lang 
        print(f'*** Parsing {regulation["legal_act_short_code"]} ({regulation["legal_act"]}) in language {lang}')
        lex = parse_eur_lex(url,metadata, load_from_file_name =  data_dir + f'{regulation["legal_act_short_code"]}_{lang}.html' )
        
        parsed = {'id':   regulation['legal_act_short_code'] + ( '' if lang == 'main' else ( '_' + lang)) , 
                      'text': regulation['legal_act'],
                      'metadata': {'CELEX' : regulation['CELEX'] ,
                                   'short_name' :  regulation['legal_act_short_code'] ,
                                   'url' : url ,
                                   'level': 'legal_act',
                                   'type' : regulation['legal_act_type'],
                                   'ISRB':  regulation['ISRB'],
                                   'ISRB_url' : regulation['ISRB_url'],
                                   # 'total_nodes' : len(lex),
                                   }, 
                      'iteration': 0,
                      'parser': inspect.currentframe().f_code.co_name,
                      'children': lex}
    
        eur_lex.append(parsed)
    
with open(r'C:\TRABAJO\_HKT\Datasets\EUR_Lex.yml', 'w', encoding='utf-8') as f:
    yaml.dump(eur_lex, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

print('** Finished creating EUR_Lex.yml')   

for d in eur_lex:
    print(f'{d["id"]:<10} - {len(d["children"])}')


