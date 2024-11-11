import streamlit as st
import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import plotly.graph_objects as go
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

# 新增：生成按钮查看成分股信息及MACD绘制
st.subheader("点击行业板块名称查看成份股信息")
for index, row in stock_board_industry_name_em_df.iterrows():
    board_name = row['板块名称']
    if st.button(board_name):
        # 获取成分股数据
        stock_board_industry_cons_em_df = ak.stock_board_industry_cons_em(symbol=board_name)

        # 按涨幅排名前十的成分股
        top_10_by_change = stock_board_industry_cons_em_df.sort_values(by='涨跌幅', ascending=False).head(10)
        st.write(f"{board_name} 涨幅前十成分股")
        st.dataframe(top_10_by_change[['名称', '代码', '涨跌幅', '成交额']])

        # 按成交额排名前十的成分股
        top_10_by_volume = stock_board_industry_cons_em_df.sort_values(by='成交额', ascending=False).head(10)
        st.write(f"{board_name} 成交额前十成分股")
        st.dataframe(top_10_by_volume[['名称', '代码', '成交额', '涨跌幅']])

        # 获取热度数据并计算加权
        try:
            for name, top_10 in zip(['涨幅前十', '成交额前十'], [top_10_by_change, top_10_by_volume]):
                total_weight = top_10['成交额'].sum()  # 可换为 '涨跌幅' 视具体需求
                weighted_data = pd.DataFrame()
                for _, stock_row in top_10.iterrows():
                    full_code = 'SH' + stock_row['代码'] if stock_row['代码'].startswith('6') else 'SZ' + stock_row['代码']
                    hot_data = ak.stock_hot_rank_detail_em(symbol=full_code)
                    hot_data['新晋粉丝加权'] = hot_data['新晋粉丝'] * (stock_row['成交额'] / total_weight)

                    if weighted_data.empty:
                        weighted_data = hot_data[['时间', '新晋粉丝加权']].copy()
                        weighted_data.set_index('时间', inplace=True)
                    else:
                        weighted_data['新晋粉丝加权'] += hot_data.set_index('时间')['新晋粉丝加权']

                # 计算 MACD
                short_period = 12  # 根据需求调整
                long_period = 26   # 根据需求调整
                weighted_data['Short_EMA'] = weighted_data['新晋粉丝加权'].ewm(span=short_period, adjust=False).mean()
                weighted_data['Long_EMA'] = weighted_data['新晋粉丝加权'].ewm(span=long_period, adjust=False).mean()
                weighted_data['MACD'] = weighted_data['Short_EMA'] - weighted_data['Long_EMA']
                weighted_data['Signal'] = weighted_data['MACD'].ewm(span=9, adjust=False).mean()

                # 绘制图表
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=weighted_data.index, y=weighted_data['MACD'], mode='lines', name=f'{name} MACD'))
                fig.add_trace(go.Scatter(x=weighted_data.index, y=weighted_data['Signal'], mode='lines', name='信号线'))
                fig.update_layout(title=f"{board_name} - {name} 加权新晋粉丝MACD", xaxis_title="时间", yaxis_title="MACD值")
                st.plotly_chart(fig)

        except Exception as e:
            st.write(f"获取或处理数据时出错: {e}")

