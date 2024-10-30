import streamlit as st
import akshare as ak
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.font_manager as fm
import os
import pandas as pd
from collections import Counter

# 设置字体文件名
FONT_FILENAME = "NotoSansMonoCJKsc-Regular.otf"

# 构建字体文件路径
font_path = os.path.join(os.getcwd(), FONT_FILENAME)

# 检查字体文件是否存在
if not os.path.exists(font_path):
    st.error(f"字体文件未找到：{font_path}")
else:
    try:
        # 加载字体属性并设置字体大小
        font_prop = fm.FontProperties(fname=font_path, size=12)
        # 设置 Matplotlib 全局字体
        plt.rcParams['font.family'] = font_prop.get_name()
        plt.rcParams['font.size'] = 12  # 设置字体大小
        plt.rcParams['axes.unicode_minus'] = False  # 解决坐标轴负号显示问题
    except Exception as e:
        st.error(f"加载字体时出错：{e}")

# 获取行业排名和概念板块排名前十的板块
st.header("行业和概念板块排名")

# 获取行业板块前十
industry_board_df = ak.stock_board_industry_name_em().head(10)
# 获取概念板块前十
concept_board_df = ak.stock_board_concept_name_em().head(10)

# 合并行业和概念板块前十，共计 20 个板块
top_20_boards = pd.concat([industry_board_df, concept_board_df], axis=0)

# 获取每个板块中成交量前十和涨幅前十的股票
top_stocks = []
for board_name in top_20_boards['板块名称']:
    try:
        stocks_df = ak.stock_board_industry_hist_em(symbol=board_name) if board_name in industry_board_df['板块名称'].tolist() else ak.stock_board_concept_hist_em(symbol=board_name)
        if stocks_df is None or stocks_df.empty:
            st.warning(f"未能获取板块 {board_name} 的数据，可能该板块数据为空或接口错误。")
            continue
    except AttributeError as e:
        st.error(f"获取板块 {board_name} 成份股时出错：{e}")
        continue
    top_volume_stocks = stocks_df.sort_values(by=['成交量'], ascending=False).head(10)
    top_stocks.extend(top_volume_stocks['股票代码'].tolist())
    top_gain_stocks = stocks_df.sort_values(by=['涨幅'], ascending=False).head(10)
    top_stocks.extend(top_gain_stocks['股票代码'].tolist())

# 统计重复次数并筛选出重复次数大于等于 2 的股票
stock_counter = Counter(top_stocks)
repeated_stocks = {stock: count for stock, count in stock_counter.items() if count >= 2}

# 将结果转换为 DataFrame 并按照重复次数排序
repeated_stocks_df = pd.DataFrame(list(repeated_stocks.items()), columns=['股票代码', '重复次数'])
repeated_stocks_df = repeated_stocks_df.sort_values(by=['重复次数'], ascending=False)

# 列出每只股票属于的板块及其类型（行业/概念），是成交量前十还是涨幅前十
stock_details = []
for stock in repeated_stocks_df['股票代码']:
    stock_info = {'股票代码': stock, '板块类型': [], '板块名称': [], '排名类别': []}
    for index, row in top_20_boards.iterrows():
        board_name = row['板块名称']
        board_type = '行业' if index < 10 else '概念'
        try:
            stocks_df = ak.stock_board_industry_hist_em(symbol=board_name) if board_type == '行业' else ak.stock_board_concept_hist_em(symbol=board_name)
            if stocks_df is None or stocks_df.empty:
                st.warning(f"未能获取板块 {board_name} 的数据，可能该板块数据为空或接口错误。")
                continue
        except AttributeError as e:
            st.error(f"获取板块 {board_name} 成份股时出错：{e}")
            continue
        if stock in stocks_df['股票代码'].tolist():
            stock_info['板块名称'].append(board_name)
            stock_info['板块类型'].append(board_type)
            if stock in stocks_df.sort_values(by=['成交量'], ascending=False).head(10)['股票代码'].tolist():
                stock_info['排名类别'].append('成交量前十')
            if stock in stocks_df.sort_values(by=['涨幅'], ascending=False).head(10)['股票代码'].tolist():
                stock_info['排名类别'].append('涨幅前十')
    stock_details.append(stock_info)

stock_details_df = pd.DataFrame(stock_details)

# 显示统计结果
st.subheader("重复次数大于等于 2 的股票列表")
st.dataframe(repeated_stocks_df)

st.subheader("股票所属板块及排名类别")
st.dataframe(stock_details_df)

# 绘制图表
fig, ax = plt.subplots()
ax.bar(repeated_stocks_df['股票代码'], repeated_stocks_df['重复次数'], color='b')
ax.set_xlabel('股票代码')
ax.set_ylabel('重复次数')
ax.set_title('重复次数大于等于 2 的股票统计')
plt.xticks(rotation=90)

st.pyplot(fig)

# 其余代码保持不变...

