"""
File     : ego.py
Title    : first streamlit app based R-shiny "Ego"
Date     : 2023.05.27
Author   : I HUA Lee
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pyvis.network import Network
import numpy as np
import math
from annotated_text import annotated_text
# import os
# from PIL import Image

@st.cache_data
def readCsv(path):
    data = pd.read_csv(path)
    return data


DocCO = readCsv("ego/nlp_output/DocCO.csv")
DocCR = readCsv("ego/nlp_output/DocCR.csv")
SenCO = readCsv("ego/nlp_output/SenCO.csv")
SenCR = readCsv("ego/nlp_output/SenCR.csv")
E = readCsv("ego/nlp_output/entityDict.csv")
# S = readCsv("nlp_output/sen_raw_data.csv")
# D = readCsv("nlp_output/doc_raw_data.csv")
# SenDTM = readCsv("nlp_output/SenDTM.csv")
# DocDTM = readCsv("nlp_output/DocDTM.csv")


# class_list is a list save all type of node's class in our dataset
class_list=["公司", "國家（地區）", "組織", "火箭", "衛星", "術語"]
# E_list is a English version class_list
E_list = ["com","loc","org","rocket","satellite","term"]
# each colour in colour list represent a specific class in class_list
colour = ["#FFFAA0", "#A3B7F9", "#C1B5C5", "#FFB86B", "#ff6961", "#a6cba3"]

# add an Mandarin label in dictionary
E["Label"] = E["label"]  
E["colour"] = E["label"] 
for i in range(0,len(class_list)):
    E['Label'] = E['Label'].replace({E_list[i]: class_list[i]})
    E['colour'] = E['colour'].replace({E_list[i]: colour[i]})

# create a list for filter
f0=list(pd.unique(E["Label"]))
f0.insert(0,"不篩選")

st.markdown("""
<style>
.color-font {
    font-size:12px;
    color:#FF9797;
}
</style>

<style>
.emphasize {
    font-size:12px;
    color:#FFFFFF;
    font-style:italic;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<p class="color-font">以特定主題為中心，從文集中選出相關性最高的關鍵詞，並對它們進行社會網絡分析</p>', unsafe_allow_html=True)
    # Add a slider to the sidebar:
    Z_class = st.selectbox(
    "選擇關鍵字類別",
    class_list,
    index = 0)

    Z = st.selectbox(
    "選擇關鍵字",
    (E["keywords"][E["Label"]== Z_class]).sort_values())

    filter = st.selectbox(
    "網路篩選遮罩",
    f0)

    st.markdown('<p class="color-font">針對網路圖的節點可以進行篩選</p>', unsafe_allow_html=True)
    K = st.sidebar.slider(
        '**設定網路節點數量**',
        4, 32, 16, 1
    )
    Q = st.slider(
    '**依關聯強度篩選鏈結**',
    0.0, 1.0, 0.5)
    
    Unit = st.radio(
    "字詞連結段落",
    ('句', '篇'),
    horizontal=True)

    Cor = st.radio(
    "連結強度計算方式",
    ('共同出現次數', '相關係數'),
    horizontal=True,
    index = 1)

    st.markdown('<p class="color-font">如果字詞出現頻率較高，可以選擇<span class="emphasize">相關係數</span>來定義連結強度；如果字詞出現頻率較低，可以選擇<span class="emphasize">共同出現次數</span>作為連結強度</p>', unsafe_allow_html=True)
    # Dump Settings button has no function now, wheras it can show the link which including specific variables
    st.button('Dump Settings')

# extract keywords form the specific class then get it Document Term Matrix (DTM)
if Unit == '篇':
    v = DocCR[Z].to_frame()
else:
    v = SenCR[Z].to_frame()
    
# Select keywords with a correlation coefficient greater than zero 
v = v[v[Z] > 0]

positiveV = list(set(v[Z].tolist()))
positiveV.sort(reverse=True)

valueIndex = []
for i in range(0, len(positiveV)):
    valueIndex.append(v.index[v[Z] == positiveV[i]].tolist())
si = []
for i in range(0,len(valueIndex)):
    si += valueIndex[i] 

if filter != "不篩選":
    # the keywords appear should be 'Z', the keyword u have selected or the keywords which Label corresponds the filter u have selected
    # vv will show whether the keywords is fit the condition above or not
    vv = (E["keywords"][si] == Z) | (E["Label"][si] == filter)
    # enumerate the keywords fiting in conditions 
    v_loc = [i for i, x in enumerate(vv) if x == 1]
    # the keywords you get must be equal or less than 'K', the number of nodes show on the graph
    a_f = []
    for i in range(0,len(v_loc)):
        a_f.append(si[v_loc[i]])
    if len(a_f) > K:
        si = a_f[0:K]
    else: si = a_f
else:
    si = si[0:K]

# get corresponding data
if Cor == '相關係數':
    if Unit == '篇':
        x = DocCR.loc[si][E["keywords"][si]].set_axis(si, axis='columns')
        a = 'DocCR'
    else: 
        x = SenCR.loc[si][E["keywords"][si]].set_axis(si, axis='columns')
        a = 'SenCR'
else:
    if Unit == '篇':
        x = DocCO.loc[si][E["keywords"][si]].set_axis(si, axis='columns')
        a = 'DocCO'
    else: 
        x = SenCO.loc[si][E["keywords"][si]].set_axis(si, axis='columns')
        a = 'SenCO'

x = pd.DataFrame(x)
# there's no directionality between 'from' and 'to' therefore we have to 
# remove the repeated data and the correlation coefficient corealated the node itself.
def matrix_to_xy(df, columns=None, reset_index=False):
    bool_index = np.triu(np.ones(df.shape), k=1).astype(bool)
    xy = (
        df.where(bool_index).stack().reset_index()
        if reset_index
        else df.where(bool_index).stack()
    )
    if reset_index:
        xy.columns = columns or ["from", "to", "val"]
    return xy

x = matrix_to_xy(x, reset_index=True)
# only reserve the data which correlation coefficient is over 0
x = x[x["val"] > 0]
x = pd.DataFrame(x)
# 'Q' is a relative value not absolute value
links = x[x["val"] >= round(float(x.quantile(Q).loc['val']),2)]

# Initiate PyVis network object
ego = Network(height='800px', bgcolor='#222222', font_color='white')

# node_id: concatenate 'from' and 'to' then get rid of the repeated serial number in dataframe before transform its' type to list
node_id = pd.unique(pd.concat([links['from'], links['to']])).tolist()
node_label = []
node_colour = []
node_size = []
node_title = []
for i in node_id:
    # node label is the keyword of node
    node_label.append(E.loc[i, 'keywords']) 
    # node colour symbolize the class of the node 
    node_colour.append(E.loc[i, 'colour'])
    # node size presents how many times the keyword shows in articles
    # The more time it is shown, the larger the node size is
    node_size.append(math.log(E.loc[i, 'freq'],2)+10)
    # when the user clicks on a specific node, detailed information about that node will be shown
    # the formate of the information is like: keyword(class, frequency)
    node_title.append(E.loc[i]['keywords']+ '('+ E.loc[i]['label']+ ', '+ str(E.loc[i]['freq'])+ ')')

ego.add_nodes(node_id, 
              label= node_label,
              color = node_colour,
              size = node_size,
              title = node_title
              )

# Add edges to the network
for index, row in links.iterrows():
    ego.add_edge(row['from'], row['to'], value=row['val'])


# use this path on your pc or your own notebook
# path = os.getcwd().replace('\\','/') 

# use this github path when app is connected to streamlit cloud 
path = 'ego'

# lengend_list is a list save lists which have a tuple and a string inside
legend_list =[]
for i in range(len(class_list)):
    legend=[]
    # annotated_text format: ("keyword", "annotation", "high light colorr")
    # legend's high light colour adding
    legend.append(("", "", colour[i]))
    # add secific class after legend colour 
    legend.append(class_list[i])
    # legend is like: [("", "", colour), class] 
    # append these lengends into the legend_list
    legend_list.append(legend)

# save the pyvis graph 
ego.save_graph(f'{path}/node.html')
# open pyvis graph as HtmlFile 
HtmlFile = open(f'{path}/node.html','r',encoding='utf-8')

# seperate page into two part 8 for graph of nodes and 1 for lengends
col1, col2= st.columns([8, 1])
with col1:
    # show HtmlFile on app
    components.html(HtmlFile.read(), height=660, scrolling=True)
with col2:
    # show the legend of graph
    # extract the lengends from legend_list 
    # legend_list is like: [[("", "", colour0), class0], [("", "", colour1), class1]......]
    for i in legend_list: 
            annotated_text(i)

components.html(HtmlFile.read(),
    height=800, width=960, scrolling=True)
