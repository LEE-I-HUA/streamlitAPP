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
from PIL import Image
import math
import os

@st.cache_data
def readCsv(path):
    data = pd.read_csv(path)
    return data


DocCO = readCsv("nlp_output/DocCO.csv")
DocCR = readCsv("nlp_output/DocCR.csv")
SenCO = readCsv("nlp_output/SenCO.csv")
SenCR = readCsv("nlp_output/SenCR.csv")
E = readCsv("nlp_output/entityDict.csv")
# S = readCsv("nlp_output/sen_raw_data.csv")
# D = readCsv("nlp_output/doc_raw_data.csv")
# SenDTM = readCsv("nlp_output/SenDTM.csv")
# DocDTM = readCsv("nlp_output/DocDTM.csv")



class_list=["公司", "國家（地區）", "組織", "火箭", "衛星", "術語"]
E_list = ["com","loc","org","rocket","satellite","term"]
colour = ["#EFFFA8", "#79B2DB", "#C1B5C5", "#FFB86B", "#FF7666", "#7FFFD4"]

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
    
    st.button('Dump Settings')

# st.write('節點數量:', K,' 關聯強度:', Q)

# 'Bins selected: ', Q

# Initiate PyVis network object
ego = Network(height='800px', bgcolor='#222222', font_color='white')

# 取出某個詞類的所有關鍵字，並取得其dtm矩陣
if Unit == '篇':
    v = DocCR[Z].to_frame()
else:
    v = SenCR[Z].to_frame()

v = v[v[Z] > 0]

positiveV = list(set(v[Z].tolist()))
positiveV.sort(reverse=True)

valueIndex = []
for i in range(0, len(positiveV)):
    valueIndex.append(v.index[v[Z] == positiveV[i]].tolist())
valueIndex
si = []
for i in range(0,len(valueIndex)):
    si += valueIndex[i] 

if filter != "不篩選":
    vv = (E["keywords"][si] == Z) | (E["Label"][si] == filter)
    v_loc = [i for i, x in enumerate(vv) if x == 1]
    v_loc
    a_f = []
    for i in range(0,len(v_loc)):
        a_f.append(si[v_loc[i]])
    if len(a_f) > K:
        si = a_f[0:K]
    else: si = a_f
else:
    si = si[0:K]


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

pd.DataFrame(x)

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
x = x[x["val"] > 0]
links = x[x["val"] >= Q]

net = Network()

node_id = pd.unique(pd.concat([links['from'], links['to']])).tolist()
node_label = []
node_colour = []
node_size = []
for i in node_id:
    node_label.append(E.loc[i, 'keywords']) 
    node_colour.append(E.loc[i, 'colour']) 
    node_size.append(math.log(E.loc[i, 'freq'],2)+10) #  

net.add_nodes(node_id, 
              label= node_label,
              color = node_colour,
              size = node_size
              )

# Add edges to the network
for index, row in links.iterrows():
    net.add_edge(row['from'], row['to'], value=row['val'])


path = os.getcwd().replace('\\','/')
image = Image.open(f'{path}/legend.png')
st.image(image)

net.save_graph(f'{path}/node.html')
HtmlFile = open(f'{path}/node.html','r',encoding='utf-8')

# st.write('data:',a) 
# st.write('x')    
# st.dataframe(x)
# st.write('links') 
# st.dataframe(links)

components.html(HtmlFile.read(),
    height=800, width=960, scrolling=True)
