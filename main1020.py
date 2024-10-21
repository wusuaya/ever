import streamlit as st
import subprocess

# 设置应用程序的标题
st.title("板块和行业排名图表展示")

# 创建两个按钮
if st.button('概念板块排名'):
    # 运行板块排.py
    subprocess.run(['python', '板块排.py'])

if st.button('行业排名'):
    # 运行行业排.py
    subprocess.run(['python', '行业排.py'])
