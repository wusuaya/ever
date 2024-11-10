import streamlit as st
import akshare as ak
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import pandas as pd
from collections import defaultdict

# 设置字体文件路径
FONT_FILENAME = "NotoSansMonoCJKsc-Regular.otf"
font_path = os.path.join(os.getcwd(), FONT_FILENAME)

# 检查字体文件是否存在并设置字体
if not os.path.exists(font_path):
    st.error(f"字体文件未找到：{font_path}")
else:
    try:
        font_prop = fm.FontProperties(fname=font_path, size=12)
        plt.rcParams['font.family'] = font_prop.get_name()
        plt.rcParams['font.size'] = 12
        plt.rcParams['axes.unicode_minus'] = False
    except Exception as e:
        st.error(f"加载字体时出错：{e}")

# 获取不同时间段数据的函数
def get_weibo_data(time_period):
    return ak.stock_js_weibo_report(time_period=time_period)

# 原有main1021.py中的逻辑
# 读取概念和行业板块数据
excluded_boards = ['昨日连板', '昨日涨停', '昨日连板_含一字', '昨日涨停_含一字', '百元股']
stock_board_concept_name_em_df = ak.stock_board_concept_name_em()
stock_board_concept_name_em_df = stock_board_concept_name_em_df[
    ~stock_board_concept_name_em_df['板块名称'].str.contains('|'.join(excluded_boards))
]

stock_board_industry_name_em_df = ak.stock_board_industry_name_em()
stock_board_industry_name_em_df = stock_board_industry_name_em_df[
    ~stock_board_industry_name_em_df['板块名称'].str.contains('|'.join(excluded_boards))
]

# 统计重复出现的个股
def show_repeated_stocks():
    concept_boards = stock_board_concept_name_em_df.head(10)['板块名称'].tolist()
    industry_boards = stock_board_industry_name_em_df.head(10)['板块名称'].tolist()
    stock_count = defaultdict(lambda: {'count': 0, 'boards': []})

    for board_name in concept_boards + industry_boards:
        if board_name in concept_boards:
            stock_board_concept_cons_em_df = ak.stock_board_concept_cons_em(symbol=board_name)
            top_stocks = stock_board_concept_cons_em_df.sort_values(by='涨跌幅', ascending=False).head(10)
        else:
            stock_board_industry_cons_em_df = ak.stock_board_industry_cons_em(symbol=board_name)
            top_stocks = stock_board_industry_cons_em_df.sort_values(by='涨跌幅', ascending=False).head(10)
        
        for _, row in top_stocks.iterrows():
            stock_name = row['名称']
            stock_count[stock_name]['count'] += 1
            stock_count[stock_name]['boards'].append(f"{board_name}（{'概念' if board_name in concept_boards else '行业'}板块）")
    
    repeated_stocks = pd.DataFrame([
        {'个股名称': stock, '重复次数': info['count'], '所属板块': ', '.join(info['boards'])}
        for stock, info in stock_count.items() if info['count'] > 1
    ])
    
    repeated_stocks = repeated_stocks.sort_values(by='重复次数', ascending=False)
    st.subheader("重复出现的个股（按重复次数排序）")
    st.dataframe(repeated_stocks)
    
    return repeated_stocks['个股名称'].tolist()

selected_stocks = show_repeated_stocks()

# 获取CNHOUR24数据
cnhour24_data = get_weibo_data("CNHOUR24")

# 检查哪些股票在CNHOUR24中有数据
valid_stocks = [stock for stock in selected_stocks if stock in cnhour24_data['name'].values]

# 获取所有时间段的数据
time_periods = ["CNHOUR12", "CNHOUR24", "CNDAY7", "CNDAY30"]
data_dict = {period: get_weibo_data(period) for period in time_periods}

# 绘制股票在不同时间段的人气排名折线图
fig, ax = plt.subplots(figsize=(12, 6))
for stock in valid_stocks:
    ranks = []
    for period in reversed(time_periods):  # 从右到左排列时间段
        df = data_dict[period]
        if stock in df['name'].values:
            rank = df.index[df['name'] == stock].tolist()[0]
            rank_value = len(df) - rank  # 取倒数，排名第一的值最高
            ranks.append(rank_value)
        else:
            ranks.append(None)

    ax.plot(
        time_periods[::-1],  # 反转时间段顺序
        ranks,
        marker='o',
        label=stock
    )

ax.set_title("微博舆情股票人气排名对比（不同时间段）", fontproperties=font_prop)
ax.set_xlabel("时间段", fontproperties=font_prop)
ax.set_ylabel("倒数人气排名", fontproperties=font_prop)
ax.legend(prop=font_prop)
plt.xticks(rotation=45, fontproperties=font_prop)

# 在Streamlit中展示图表
st.pyplot(fig)
