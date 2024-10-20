import streamlit as st
import akshare as ak
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta

# 设置字体，确保系统上有SimHei字体或其他支持中文的字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用SimHei字体显示中文
plt.rcParams['axes.unicode_minus'] = False    # 解决坐标轴负号显示问题

# 页面标题
st.title("北向资金增持与板块分析")

# 获取时间段选项，按从“1年”到“今日”的顺序排列
time_period_options = ["1年", "1季", "1月", "10日", "5日", "3日", "今日"]

# 定义函数，获取不同时间段的板块排名数据
def get_board_rank_data(symbol, periods):
    board_rank_data = {}
    for period in periods:
        try:
            data = ak.stock_hsgt_board_rank_em(symbol=symbol, indicator=period)
            board_rank_data[period] = data
        except Exception as e:
            st.error(f"获取 {period} 数据失败: {e}")
    return board_rank_data

# 定义函数，绘制板块排名变化
def plot_board_rank(board_rank_data, periods, title):
    today_data = board_rank_data["今日"].head(10)
    board_names = today_data["名称"].tolist()
    
    fig, ax = plt.subplots(figsize=(10, 6))

    for board_name in board_names:
        rankings = []
        for period in periods:
            period_data = board_rank_data[period]
            board_row = period_data[period_data["名称"] == board_name]
            if not board_row.empty:
                rank = board_row.index[0] + 1
                rankings.append(rank)
            else:
                rankings.append(None)

        ax.plot(periods, rankings, marker='o', label=board_name)

    ax.set_title(title)
    ax.set_xlabel("时间段")
    ax.set_ylabel("排名（越小越靠前）")
    ax.invert_yaxis()  # 排名越小，位置越靠上
    ax.legend()
    st.pyplot(fig)

# 获取北向持股个股排行中的增持估计总市值
st.subheader("北向持股个股增持估计-市值总和")
stock_today_data = ak.stock_hsgt_hold_stock_em(market="北向", indicator="今日排行")
total_increase_value = stock_today_data['增持估计-市值'].sum()
st.write(f"北向持股个股增持估计的总市值为：{total_increase_value:.2f} 万元")

# 添加板块选择的按钮
if st.button('北向资金增持行业板块排行'):
    symbol = "北向资金增持行业板块排行"
    board_rank_data = get_board_rank_data(symbol, time_period_options)
    plot_board_rank(board_rank_data, time_period_options, "北向资金增持行业板块排行")

if st.button('北向资金增持概念板块排行'):
    symbol = "北向资金增持概念板块排行"
    board_rank_data = get_board_rank_data(symbol, time_period_options)
    plot_board_rank(board_rank_data, time_period_options, "北向资金增持概念板块排行")

# 增加一个用于个股排名折线图的函数
def plot_stock_rank(stock_rank_data, periods):
    today_data = stock_rank_data["今日排行"].head(10)
    stock_names = today_data["名称"].tolist()

    fig, ax = plt.subplots(figsize=(10, 6))

    for stock_name in stock_names:
        rankings = []
        for period in periods:
            period_data = stock_rank_data[period]
            stock_row = period_data[period_data["名称"] == stock_name]
            if not stock_row.empty:
                rank = stock_row.index[0] + 1
                rankings.append(rank)
            else:
                rankings.append(None)

        ax.plot(periods, rankings, marker='o', label=stock_name)

    ax.set_title("前十个股在不同时间段的排名变化")
    ax.set_xlabel("时间段")
    ax.set_ylabel("排名（越小越靠前）")
    ax.invert_yaxis()  # 排名越小，位置越靠上
    ax.legend()
    st.pyplot(fig)

# 获取个股排名并绘制图表
if st.button('北向持股个股排行'):
    stock_rank_data = get_stock_rank_data(market="北向", periods=["今日排行", "3日排行", "5日排行", "10日排行", "月排行", "季排行", "年排行"])
    plot_stock_rank(stock_rank_data, ["年排行", "季排行", "月排行", "10日排行", "5日排行", "3日排行", "今日排行"])

# 定义requirements.txt文件内容
requirements = """
streamlit
akshare
matplotlib
pandas
"""

# 生成并写入requirements.txt文件
with open("requirements.txt", "w") as file:
    file.write(requirements)
