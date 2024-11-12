# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 10:28:43 2024

@author: q30930


https://eur-lex.europa.eu/expert-search-form.html?action=update&qid=1731230886820&home=ecb

ECB Regulations and Guidelines:  -  Domain: EU law and case-law, Subdomain: European Central Bank, Type of act: Regulation, Guideline, Limit to ECB legal acts in force: True, Search language: English
    
DTS_SUBDOM = ECB_ACTS AND ((FM_CODED = REG) OR (FM_CODED = GUIDELINE)) AND (VV = true OR (DTC=false AND FM_CODED = OPIN* OR OWNINI_OPIN* OR RECO NOT ((MD = {3*,AI} OR {3*,AA} OR {3*,RR}) OR (SP = {5*,AI} OR {5*,AA} OR {5*,RR}))))



ECB Opinions and recomendations (1794 documents):  Domain: EU law and case-law, Subdomain: European Central Bank, Type of act: Opinion, Recommendation, Limit to ECB legal acts in force: True, Search language: English

DTS_SUBDOM = ECB_ACTS AND ((FM_CODED = OPIN OR OPIN_DRAFT_NATION_LEGIS OR OWNINI_OPIN OR OWNINI_OPIN_DRAFT_NATION_LEGIS) OR (FM_CODED = RECO)) AND (VV = true OR (DTC=false AND FM_CODED = OPIN* OR OWNINI_OPIN* OR RECO NOT ((MD = {3*,AI} OR {3*,AA} OR {3*,RR}) OR (SP = {5*,AI} OR {5*,AA} OR {5*,RR}))))


"""


import pandas as pd
import re
from io import StringIO

# Open the file in read mode
with open(r'C:\TRABAJO\_HKT\Datasets\Search results 20241110-Regulations and Guidelines.csv', 'r', encoding='utf-8') as file:
    content = file.read()

# Replace occurrences of \n\s*\( with (
content = re.sub(r'\n\s*\(', '(', content)
content = re.sub(r'special edition\(s\)\s*\(\n\s*', r'special edition\(s\) \(', content)
content = re.sub(r'\)\n\s*\"\,', r'\)",', content)


# Use StringIO to treat the string as a file-like object
data = StringIO(content)    

# Read the data into a pandas DataFrame
df = pd.read_csv(data, sep=',', quotechar='"', header=0)

df.to_excel('C:\TRABAJO\_HKT\Datasets\EUR-LEX.Regulations and Guidelines.xlsx', index=False)

# Display the DataFrame
# print(df)

# -------------------------------------------------------x--
# Open the file in read mode
with open(r'C:\TRABAJO\_HKT\Datasets\Search results 20241110-Recomendations.csv', 'r', encoding='utf-8') as file:
    content = file.read()

# Replace occurrences of \n\s*\( with (
content = re.sub(r'\n\s*\(', '(', content)
content = re.sub(r'special edition\(s\)\s*\(\n\s*', r'special edition\(s\) \(', content)
content = re.sub(r'\\\"', r"'", content)


# Use StringIO to treat the string as a file-like object
data = StringIO(content)    

# Read the data into a pandas DataFrame
df = pd.read_csv(data, sep=',', quotechar='"', header=0)

df.to_excel('C:\TRABAJO\_HKT\Datasets\EUR-LEX.Recomendations.xlsx', index=False)

# Display the DataFrame
# print(df)
