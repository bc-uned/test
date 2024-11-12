# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 10:07:49 2024

@author: q30930
"""

import re
from bs4 import BeautifulSoup
import requests
import random
import time


def fix_sub_soup(soup):
    # Check and add <html> and <body> tags if they are missing
    if not soup.html:
        html_doc = "<html>" + str(soup) + "</html>"
    if "<body>" not in html_doc:
        html_doc = html_doc.replace("<html>", "<html><body>", 1)
        html_doc = html_doc.replace("</html>", "</body></html>", 1)
    
    # Re-import the modified HTML into BeautifulSoup
    soup = BeautifulSoup(html_doc, 'html.parser')
    
    return soup 

def replace_sub_list(soup):
    """ replace list elements """
    soup = fix_sub_soup(soup)
    for tbody in soup.find_all('tbody', recursive=True):
        # i += 1
        rows = tbody.find_all('tr')
        # t = tbody.text
        # n = len(rows)
        if len(rows) == 1:
            cols = rows[0].find_all('td')
            if len(cols) == 2 and len(cols[0].get_text(strip=True)) <= 5:
                col1_text = cols[0].get_text(strip=True)
                col2_text = cols[1].get_text(strip=True)
                new_p = soup.new_tag('p')
                # new_p.string = "~¬¡PART¡{'type':'list','number':'" + col1_text +  "'}¡¬~" + f"{col1_text} {col2_text}"
                new_p.string = f"{col1_text} {col2_text}"                
                tbody.replace_with(new_p)
    # print(i)
    return replace_sub_list2(soup)

def replace_sub_list2(soup):
    for container in soup.find_all('div', class_='grid-container grid-list'):
        col1 = container.find('div', class_='grid-list-column-1')
        col2 = container.find('div', class_='grid-list-column-2')
        
        if col1 and col2 and len(container.find_all('div')) == 2:
            col1_text = col1.get_text(strip=True)
            if len(col1_text) <= 5:
                col2_text = col2.get_text(strip=True)
                new_p = soup.new_tag('p')
                # new_p.string = "~¬¡PART¡{'type':'list','number':'" + col1_text +  "'}¡¬~" + f"{col1_text} {col2_text}"
                new_p.string = f"{col1_text} {col2_text}"                                
                container.replace_with(new_p)
    return soup


# Function to check if an element is centered
def is_centered(element):
    style = element.get('style', '')
    # for styletext in style:
    #     if 'text-align' in styletext:
    #         if 'center' in styletext:            
    #             return True

    if 'text-align: center' in style:
        return True
    return False

def clean_text(text):
    
    text = re.sub('\u00A0', ' ', text) # Non-breaking space to space    
    
    # text = re.sub(r'\u25BA.*?\n?.*?\u25C4', '', text) # Quita todo entre ► y ◄
    text = re.sub(r'►.\d\d?\n', ' ', text) # Quita todo entre ► y ◄    
    text = re.sub(r'◄', ' ', text) # Quita todo entre ► y ◄    
    text = re.sub(r"▼\w+\n?", '', text)     
    
    # Step 3: Replace multiple spaces and newlines with a single space or newline
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    
    # Step 1: Remove all spaces that are not between two letters or after punctuation
    # text = re.sub(r'(?<!\w)(?<![.,!?;:\'\"-\(\)]) | (?!\w)', '', text)
    
    # Remove spaces after '(' and before ')'
    text = re.sub(r'\(\s+', '(', text)
    text = re.sub(r'\s+\)', ')', text)    
    
    # Step 4: Eliminate newlines that don't have a period before or a capital letter after
    # text = re.sub(r'(?<![\.;])\n(?![A-Z\(\)\d])', ' ', text)
    
    # Step 5: Newlines at the beginning or the end
    text = re.sub(r'^\n+|\n+$', '', text)
    
    return text
     
# Function to identify parts in the text
def identify_parts(soup):
    """ MODIFICA LA SOPA PARA INSTERTAR IDENTIFICADORES DE PARTE EN EL PROPIO TEXTO """
    parts = []
    current_part = None

    for element in soup.find_all(['p', 'div', 'span']):
        text = element.get_text(strip=True)
        if not text:
            continue

        # Check if the text is centered
        if not is_centered(element):
            continue
        
        # keywords = ["TITLE", "CHAPTER", "SECTION", "SUB-SECTION", "ANNEX", "TABLE", "PART", "ARTICLE"]
          
        # part_match = re.match(r'(?i)^(TITLE|CHAPTER|SECTION|SUB-SECTION|ANNEX|TABLE|PART|ARTICLE)\s+([A-Z0-9]{1,6})$', text)
        # part_match = re.match(rf'(?i)^({"|".join(keywords)})\s+([A-Z0-9]{1,6})$', text)
        # part_match = re.match(r'(?i)^(?P<type>TITLE|CHAPTER|SECTION|SUB-SECTION|ANNEX|TABLE|PART|ARTICLE)\s+(?P<number>[A-Z0-9]{1,6})(?:\r?\n(?P<subtitle>.*))?$', text)
        # part_match = re.match(r'(?i)^(?P<type>TITLE|CHAPTER|SECTION|SUB-SECTION|ANNEX|TABLE|PART|ARTICLE)\s+(?P<number>[A-Z0-9]{1,6})(?:\r?\n(?P<subtitle>.*))?(?:\r?\n(?P<rest>.*))?$', text, re.DOTALL)
          
        # part_match = re.match(r'(?i)^(?P<type>{"|".join(keywords)})\s+(?P<number>[A-Z0-9]{1,6})(?:\r?\n(?P<subtitle>.*))?(?:\r?\n(?P<rest>.*))?$', text, re.DOTALL)

        # List of keywords
        keywords = ["TITLE", "CHAPTER", "subsection","SUB-SECTION", "SECTION",  "ANNEX", "TABLE", "PART", "ARTICLE", "Appendix",
                    "TITEL", "KAPITEL", "unterabschnitt", "abschnitt", "ANHANG", "Tabelle", "TEIL", "artikel",
                    ]
        
        type_equivalency = {
                                "TITLE"         : "TITLE",
                                "CHAPTER"       : "CHAPTER",
                                "SUBSECTION"    : "SUB-SECTION",
                                "SUB-SECTION"   : "SUB-SECTION",
                                "SECTION"       : "SECTION",
                                "ANNEX"         : "ANNEX",
                                "TABLE"         : "TABLE",
                                "PART"          : "PART",
                                "ARTICLE"       : "ARTICLE",
                                "TITEL"         : "TITLE",
                                "KAPITEL"       : "CHAPTER",
                                "UNTERABSCHNITT": "SUB-SECTION",
                                "ABSCHNITT"     : "SECTION",
                                "ANHANG"        : "ANNEX",
                                "TABELLE"       : "TABLE",
                                "TEIL"          : "PART",
                                "ARTIKEL"       : "ARTICLE",
                                "APPENDIX"      : "APPENDIX",
                                
                            }

        
        # Join the keywords into a regex pattern
        keywords_pattern = "|".join(keywords)
        
        # Create the regex pattern using the keywords list
        # pattern = rf'(?i)^({keywords_pattern})\s+([A-Z0-9]{{1,6}})$'        
        # pattern = rf'(?i)^(?P<type>{keywords_pattern})\s+(?P<number>[A-Z0-9]{1,6})(?:\r?\n(?P<subtitle>.*))?(?:\r?\n(?P<rest>.*))?$'        
        # pattern = rf'(?i)^(?P<type>{keywords_pattern})\s+(?P<number>[A-Z0-9]{{0,6}})(?:\r?\n(?P<subtitle>.*))?(?:\r?\n(?P<rest>.*))?$'               
        pattern = rf'^(?P<type>{keywords_pattern})\s*(?P<number>[A-Z0-9]{{0,6}})(?:\r?\n(?P<subtitle>.*))?(?:\r?\n(?P<rest>.*))?$'                       
        
        # part_match = re.match(pattern, text)        
        part_match = re.match(pattern, text, re.DOTALL | re.IGNORECASE)        
          
        # if part_match:
                    
        # print("Type:", part_match.group('type'))
        # print("Number:", part_match.group('number'))
        # print("Subtitle:", part_match.group('subtitle'))
          

        # Check if the text matches the pattern for parts
        # part_match = re.match(r'(?i)^(TITLE|CHAPTER|SECTION|SUB-SECTION|ANNEX|TABLE|PART|ARTICLE)\s+([A-Z0-9]{1,6})$', text)
        if part_match:
            text = element.get_text()
            element_id = element.get('id', '')
            
            _type = part_match.group('type') or ''
            number = part_match.group('number') or ''
            subtitle = part_match.group('subtitle') or ''
            
            if not subtitle:
                first_child = element.find()
                if first_child:
                    posible_subt_element = first_child
                else:
                    posible_subt_element = element.find_next_sibling()
                if posible_subt_element:
                    # Check if the text is centered
                    if is_centered(posible_subt_element):
                        subtitle = posible_subt_element.get_text(strip=True)                    
            
            element.string = "~¬¡PART¡{'type':'" +type_equivalency[ _type.upper()] + "','number':'" + number + \
                                    "','title':'" +  _type + ' ' + number + "','subtitle':'" + subtitle.replace("'","\\'") +\
                                    "','element_id':'" + element_id + "'}¡¬~" + text
            
            if current_part:
                parts.append(current_part)
            current_part = {
                'part_type'     : _type,                
                'part_title'    : _type + ' ' + number,
                'part_no'       : number,
                'part_subtitle' : subtitle,
                'full_text'     : text,
                'part_text'     : text,                
                    }
        elif current_part:
            # Check if the text is a part title
            current_part['part_text'] += text + ' '
            current_part['full_text'] += '\n' + text

    if current_part:
        parts.append(current_part)

    return (parts, soup)

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
    # soup = replace_sub_list(soup)
    
    if save_to_file_name:
        # Save to a plain text file
        with open(save_to_file_name, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
    eli_container = soup.find('div', class_='eli-container')
    
    if not eli_container:
        eli_container = soup.find('div', {'id': 'document1', 'class': 'tabContent'})
    
    if not eli_container:
        print("**** Error no existen  eli-container ni tabContent *** No se puede parsear ****")
        return None, None
    
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
        
    return identify_parts(eli_container)


file = r"C:\TRABAJO\_HKT\Datasets\EUR_LEX_INLINE_CSS/" + "CELEX_02015R0847-20200101_EN.html"
# file = data_dir + f'{regulation["legal_act_short_code"]}_{lang}.html'

# lex, soup = parse_eur_lex(url = None, load_from_file_name = file  )
# soup = replace_sub_list(soup)
# text = soup.get_text(separator='')
# text = "~¬¡PART¡{'type':'HEADER'}¡¬~\n" +\
#         text +\
#         "\n~¬¡PART¡{'type':'EOF'}¡¬~"
 


#%% Load files

# """import yaml
# data_dir = f'C:\TRABAJO\_HKT\Datasets\EUR_Lex/'


# with open(f'{data_dir}IRSB_main_pages.yml', 'r') as f:
#     # Load the entire file as a single document
#     IRSB = yaml.safe_load(f)

# print("**** Starting EUR-Lex scrapping ****")

# eur_lex = []
# """
# Define the directories to search for files
import os
directories = [
    r"C:\\TRABAJO\\_HKT\\Datasets\\EUR_LEX_INLINE_CSS",
    r"C:\TRABAJO\_HKT\Datasets\EUR_LEX_INLINE_CSS_REGS",
    r"C:\TRABAJO\_HKT\Datasets\EUR_LEX_INLINE_CSS_RECS"
]

# Define the regex pattern to match the file names
pattern = re.compile(r'CELEX_(?P<celex>[^_]+)_(?P<lang>[^.]+)\.html')

# List to store the results
celex_inline_files = []

# Loop through each directory
for directory in directories:
    # List all files in the directory
    for file_name in os.listdir(directory):
        # Check if the file name matches the pattern
        match = pattern.match(file_name)
        if match:
            # Extract the celex and lang variables
            celex = match.group('celex')
            lang = match.group('lang')
            # Store the result
            full_path = os.path.join(directory, file_name)
            celex_inline_files.append((full_path, celex, lang))

# # Print the results
# for result in celex_inline_files:
#     print(f"File: {result[0]}, CELEX: {result[1]}, Language: {result[2]}")
    
#%% Loop thru regulations
import yaml

def parse_simplified(text):
    # Regex pattern to match ~¬¡PART¡(.*?)¡¬~
    pattern = r'~¬¡PART¡(.*?)¡¬~'
    
    # Find all matches
    matches = re.finditer(pattern, text, re.DOTALL)
    
    refs = []
    
    for match in matches:
        refs.append((match.group(1), match.start(), match.end() ))

    
    lex = []
    
    # Print the contents between the matches
    for i, (metadata_str, start, end) in enumerate( refs[:-1] ):
        meta = eval(metadata_str)
        
        node_id = meta.get('id','')
        node_text = text[end:refs[i+1][1]]
        
        lex.append( {'id': node_id, 'text': node_text, 'metadata': meta, 
                'iteration': i, 'parser': 'parse_simplified',
                'children': []})
        
    return lex

results = {}        
DEBUG = False
DEBUG_CODE = "51994AB0001"    

for file, celex, lang in celex_inline_files:   
    print(celex,lang)
    metadata = {'file' : file, 'celex': celex, 'lang': lang,
                'url': f"https://eur-lex.europa.eu/legal-content/{lang.upper()}/TXT/?uri=CELEX%3A{celex}"}

    if DEBUG and celex != DEBUG_CODE:
        continue
    #Identify parts tags
    lex, soup = parse_eur_lex(url = None, load_from_file_name = file  )
    if not soup:
        continue
    soup = replace_sub_list(soup)
    text = soup.get_text(separator='')
    text = clean_text(text)
    
    # text = re.sub(r'\)(\s+)\n', ') ', text)
    # text = re.sub(r'(\d[\d|a-f]?\.)(\s+)\n', r'\1 ', text)        
    
            
    
    #Add first and last tag
    text = "~¬¡PART¡{'type':'DOCUMENT'}¡¬~\n" +\
           text +\
           "\n~¬¡PART¡{'type':'EOF'}¡¬~"

    lex = parse_simplified(text)
    
    results[f'CELEX_{celex}_{lang}'] = {'doc_parse' : lex, 'doc_metadata' :  metadata}
    

with open(r'C:\TRABAJO\_HKT\Datasets\EUR_Lex_SimpleParser.yml', 'w', encoding='utf-8') as f:
    yaml.dump(results, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

print('** Finished creating EUR_Lex_SimpleParser.yml')   

#%% Export to pandas
# Flatten the dictionary
flattened_data = []
for key, value in results.items():
    doc_metadata = value['doc_metadata']
    for doc in value['doc_parse']:
        flattened_entry = {**doc_metadata, **doc, **doc['metadata']}
        flattened_data.append(flattened_entry)

import pandas as pd
df = pd.DataFrame(flattened_data).drop(columns = ['file', 'metadata', 'iteration', 'parser', 'children', 'id'] ).fillna("")

df = df[['celex', 'lang', 'type', 'text' , 'title', 'subtitle', 'number', 'url', 'element_id']]
df['len'] = df['text'].map(len)
df['word'] = df['text'].map(lambda x: len(x.split(' ')))

df.to_excel('C:\TRABAJO\_HKT\Datasets\EUR_Lex_SimpleParser.xlsx', index=False)

# for d in eur_lex:
#     print(f'{d["id"]:<10} - {len(d["children"])}')



# # Example HTML content (replace with actual HTML content)
# html_content = """
# <p style="text-align:center">TITLE I</p>
# <p style="text-align:center"><b>SCOPE, DEFINITIONS AND AUTHORITIES</b></p>
# <p>Some introductory text.</p>
# <p style="text-align:center">CHAPTER I</p>
# <p style="text-align:center"><b>Recovery and resolution planning</b></p>
# <p>Details about recovery and resolution planning.</p>
# """

# # Parse the HTML content with BeautifulSoup
# soup = BeautifulSoup(html_content, 'html.parser')

# # Identify parts in the soup
# parts = identify_parts(soup)

# # Print the identified parts
# for part in parts:
#     print(part)
