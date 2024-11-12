# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 11:07:07 2024

@author: q30930


Creates YAML file with all the information of EUR-Lex regulation in a structured form.

"""
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
DEBUG = True
DEBUG_CODE = 'BRRD'
BREAK_POINT_NODE = 10
DEBUG_STACK = 1

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

def get_call_stack(levels, ignore_list=['parse_node_error_control',]):
    if ignore_list is None:
        ignore_list = []
    
    stack = inspect.stack()
    call_stack = []
    level_count = 0
    
    for i in range(1, len(stack)):
        if level_count >= levels:
            break
        func_name = stack[i].function
        if func_name not in ignore_list:
            call_stack.append(func_name)
            level_count += 1
    
    return ' <- '.join(call_stack)


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
            'iteration': iteration, 'parser': get_call_stack(5 if DEBUG else DEBUG_STACK),
            'children': children}, next_sibling


#@print_function_name
# Articles, but also a global wrapper.
def parse_articles(element): #  Article
    if DEBUG:
        element2 = copy.deepcopy(element)
        # element = copy.deepcopy(element2)
       
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

    # Esta es una forma poco frecuente 
    if not sub_titles:
        next_sibling = element.find_next_sibling()
        if next_sibling and 'stitle-article-norm' in next_sibling.get('class', []):        
            subtitle_text = next_sibling.get_text()
            if  subtitle_text: 
                node_text = title + '\n' +  subtitle_text 
   
    metadata = {"level": level, "title": title, "subtitle": subtitle_text}
    children = []
    
    
    # next_element = element.find()    
    
    # Loop through next div and all next siblings 
    if next_element:
        child_dict, _ = parse_node(next_element, children)
        
        for sibling in next_element.next_siblings:
            child_dict, _ = parse_node(sibling, children)
        
    
    return {'id': node_id, 'text': node_text, 'metadata': metadata,
            'iteration': local_iteration, 'parser': get_call_stack(5 if DEBUG else DEBUG_STACK),
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
    
    node_text = title + '\n' + sub_text
    
    # Infer metadata level and title from the text

    if "subsection" in title.lower():
        level = "sub-section"
    elif "sub-section" in title.lower():
        level = "sub-section"        
    elif "unterabschnitt" in title.lower():
        level = "sub-section"
    elif "section" in title.lower():
        level = "section"
    elif "abschnitt" in title.lower():
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
            'iteration': local_iteration, 'parser': get_call_stack(5 if DEBUG else DEBUG_STACK),
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
            'iteration': iteration, 'parser': get_call_stack(5 if DEBUG else DEBUG_STACK),
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

        next_div = next_div.find_next_sibling()
    
    return {'id': node_id, 'text': node_text, 'metadata': metadata, 
            'iteration': local_iteration, 'parser': get_call_stack(5 if DEBUG else DEBUG_STACK),
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
            'iteration': local_iteration, 'parser': get_call_stack(5 if DEBUG else DEBUG_STACK),
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
    inline_text = element_text_to_div(inline_element)
    if not inline_text:
        inline_text = inline_element.get_text().strip()
        inline_element.decompose()    
    
    node_text = node_id + ' ' + inline_text #Obtiene el texto de todo hasta el primer div
    
    metadata = {"level": level, "title": title}
    children = []
    
    for child in element.find_all(recursive=False):
        child_dict, next_element = parse_node(child, children)
    
    return {'id': node_id, 'text': node_text, 'metadata': metadata,
            'iteration': local_iteration, 'parser': get_call_stack(5 if DEBUG else DEBUG_STACK),
            'children': children}, element.find_next_sibling()

def parse_table(element):
    node_id = element.get('id', '') # Id del nodo padre
    if DEBUG: print(f'iteration: {iteration:>4}, node_id {node_id}') 
    # node_text = "\n".join(p.get_text(strip=True) for p in element.find_all('p'))
    
    title    = element.get_text(strip=True)
    level = "table"    
    node_text = title 
    
    metadata = {"level": level, "title": title}
    children = []
    
    table_data = element.find_next_sibling()
    
    if table_data.name == 'table':
        data = parse_and_unmerge_cells(table_data, children, node_id, title)
        children.append(data)
        table_data.decompose() # Remove table data
    
    return {'id': node_id, 'text': node_text, 'metadata': metadata, 
            'iteration': iteration, 'parser': get_call_stack(5 if DEBUG else DEBUG_STACK),
            'children': children}, element.find_next_sibling()



# Function to unmerge cells
def parse_and_unmerge_cells(table, children, node_id, title): 
    
    global iteration
    iteration += 1
    
    node_id2 = table.get('id', '') # Id del nodo padre
    
    if node_id2:
        node_id = node_id2
    else:
        node_id += "_table_data"
        
    level = "table_data"       
    metadata = {"level": level, "title": title}
    
    
    # Find the maximum number of columns
    max_cols = max(len(row.find_all(['td', 'th'])) for row in table.find_all('tr'))
    
    # Initialize the output table with empty strings
    output = [[''] * max_cols for _ in range(len(table.find_all('tr')))]
    
    # Process each row
    row_index = 0
    for row in table.find_all('tr'):
        col_index = 0
        for cell in row.find_all(['td', 'th']):
            rowspan = int(cell.get('rowspan', 1))
            colspan = int(cell.get('colspan', 1))
            cell_text = cell.get_text(strip=True)
            
            # Find the next available cell in the output table
            while output[row_index][col_index]:
                col_index += 1
            
            # Fill the cell and handle rowspan and colspan
            for i in range(rowspan):
                for j in range(colspan):
                    output[row_index + i][col_index + j] = cell_text
            col_index += colspan
        row_index += 1
    
    node_text = '\n'.join(['|'.join(row) for row in output])        
    
    data =  {'id': node_id, 'text': node_text, 'metadata': metadata, 
                'iteration': iteration, 'parser': get_call_stack(5 if DEBUG else DEBUG_STACK),
                'children': []}
    
    return data
    
    
    # node_id = element.find(class_='grid-list-column-1').get_text(strip=True)
    # if DEBUG: print(f'iteration: {iteration:>4}, node_id {node_id}')
    # local_iteration = iteration    
    
    # title = ""    
    # level = "sub-paragraph"    
    
    # # inline_element contiene el texto del parrafo.
    # inline_element = element.find(class_='grid-list-column-2')
    # node_text = node_id + ' ' + element_text_to_div(inline_element) #Obtiene el texto de todo hasta el primer div
    
    # metadata = {"level": level, "title": title}
    # children = []
    
    # for child in element.find_all(recursive=False):
    #     child_dict, next_element = parse_node(child, children)
    
    # return {'id': node_id, 'text': node_text, 'metadata': metadata,
    #         'iteration': local_iteration, 'parser': get_call_stack(5 if DEBUG else DEBUG_STACK),
    #         'children': children}, element.find_next_sibling()
    
    # rows = element.find_all('tr')
    # data = []
    # for row in rows:
    #     cells = row.find_all(['td', 'th'])
    #     row_data = []
    #     for cell in cells:
    #         rowspan = int(cell.get('rowspan', 1))
    #         colspan = int(cell.get('colspan', 1))
    #         cell_text = cell.get_text(strip=True)
    #         for _ in range(rowspan):
    #             for _ in range(colspan):
    #                 row_data.append(cell_text)
    #     data.append(row_data)
    
    # # Normalize the data to ensure all rows have the same number of columns
    # max_cols = max(len(row) for row in data)
    # normalized_data = []
    # for row in data:
    #     while len(row) < max_cols:
    #         row.append('')
    #     normalized_data.append(row)
    
    # return normalized_data


#@print_function_name
def parse_dlist_definition(element):
    node_id = ''
    node_text = ''
    metadata = {'class': 'dlist-definition'}
    children = []
    
    for child in element.find_all(recursive=False):
        child_dict, next_element = parse_node(child, children)
    
    return {'id': node_id, 'text': node_text, 'metadata': metadata,
            'iteration': iteration, 'parser': get_call_stack(5 if DEBUG else DEBUG_STACK),
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
    
    if iteration in (BREAK_POINT_NODE,): #bbc
        if DEBUG: print('debugging breakpoint here')
    
    # if type(node) == str:
    #     return None, None   
    
    if node.name == 'div':
        first_child = node.find()
        
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
            
        # Sub parrafos formateados como listas.
        elif     'list' in node.get('class', []) \
            and  'grid-list-column-1' not in node.get('class', []) \
            and  (     not first_child \
                   or  'grid-list' not in first_child.get('class', [])):
            node_info, next_element = parse_sub_paragraph(node, sub_paragraph_no = 1)            
        else:
            for child in node.find_all(recursive=False):
                _, next_element = parse_node(child, children_list) # Los hijos se auto-insertan en children_list
    

    elif node.name == 'p' and 'title-article-norm' in node.get('class', []):
        node_info, next_element = parse_articles(node)    
    
    elif node.name == 'p' and 'title-division-1' in node.get('class', []):
        node_info, next_element = parse_title_division_1(node)
    
    
    
    #Parrafos no númerados
    elif node.name == 'p' and 'norm' in node.get('class', []):
        if 'grid-list-column-2' not in node.parent.get('class', []):
            node_info, next_element = parse_sub_paragraph(node, sub_paragraph_no = 0)
        else:
            ps = node.find_previous_sibling()
            if ps and 'norm' in ps.get('class', []):
                node_info, next_element = parse_sub_paragraph(node, sub_paragraph_no = 0)                

    elif node.name == 'p' and any([ 'title-gr-seq-level' in c for c in node.get('class', [])]):
        node_info, next_element = parse_sub_paragraph(node, sub_paragraph_no = 0)

    #Comentarios a una lista (dentro de un parrafo)
    elif node.name == 'p' and 'list' in node.get('class', []):
        if 'grid-list-column-2' not in node.parent.get('class', []):        
            node_info, next_element = parse_sub_paragraph(node, sub_paragraph_no = 1)

    elif node.name == 'p' and 'title-article-quoted' in node.get('class', []):        
        node_info, next_element = parse_sub_paragraph(node, sub_paragraph_no = 1)
        
        
    elif node.name == 'p' and 'title-table' in node.get('class', []):        
        node_info, next_element = parse_table(node)

    # elif node.name == 'table':
    #     for child in node.find_all(recursive=True):
    #         _, next_element = parse_node(child, children_list) # Los hijos se auto-insertan en children_list
                

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
import yaml
data_dir = f'C:\TRABAJO\_HKT\Datasets\EUR_Lex/'


with open(f'{data_dir}IRSB_main_pages.yml', 'r') as f:
    # Load the entire file as a single document
    IRSB = yaml.safe_load(f)

print("**** Starting EUR-Lex scrapping ****")

eur_lex = []
    
for regulation in IRSB:   
    metadata = {k:v for k,v in regulation.items() if k not in ['de_text','en_text']}
    # for url_key, lang in [('EURLex_url','main'), ('en_text','en'), ('de_text','de'), ]:
    # for url_key, lang in [('de_text','de'), ]:        
    # for url_key, lang in [('en_text','en'), ]: 
    for url_key, lang in [ ('en_text','en'), ('de_text','de'), ]:
        
        if DEBUG and regulation['legal_act_short_code'] != DEBUG_CODE:
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
                      'parser': get_call_stack(5 if DEBUG else DEBUG_STACK),
                      'children': lex}
    
        eur_lex.append(parsed)
    
with open(r'C:\TRABAJO\_HKT\Datasets\EUR_Lex.yml', 'w', encoding='utf-8') as f:
    yaml.dump(eur_lex, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

print('** Finished creating EUR_Lex.yml')   

for d in eur_lex:
    print(f'{d["id"]:<10} - {len(d["children"])}')


if DEBUG:
    
    #---------- todo esto para cargar create_comparison_files ----------------------#
    import importlib.util
    import sys
    
    # Define the file path
    file_path = r'C:\TRABAJO\_HKT\Datasets\eurolex_to_pandas_v2.py'
    
    # Load the module
    spec = importlib.util.spec_from_file_location("eurolex_to_pandas_v2", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["eurolex_to_pandas_v2"] = module
    spec.loader.exec_module(module)
    
    # Now you can use the function
    create_comparison_files = module.create_comparison_files

    create_comparison_files(eur_lex, regulation_short_name = DEBUG_CODE,
                            lang = 'en',
                            temp_dir = r'C:\TRABAJO\_HKT\Datasets\temp')
    


