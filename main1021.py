import streamlit as st
import akshare as ak
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.font_manager as fm
import os
import pandas as pd
from collections import defaultdict

# 设置字体文件名
FONT_FILENAME = "NotoSansMonoCJKsc-Regular.otf"
font_path = os.path.join(os.getcwd(), FONT_FILENAME)

# 检查字体文件是否存在
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

# 获取概念板块和行业板块数据，在全局范围内定义并过滤掉不需要的板块
excluded_boards = ['昨日连板', '昨日涨停', '昨日连板_含一字', '昨日涨停_含一字', '百元股']
stock_board_concept_name_em_df = ak.stock_board_concept_name_em()
stock_board_concept_name_em_df = stock_board_concept_name_em_df[
    ~stock_board_concept_name_em_df['板块名称'].str.contains('|'.join(excluded_boards))
]

stock_board_industry_name_em_df = ak.stock_board_industry_name_em()
stock_board_industry_name_em_df = stock_board_industry_name_em_df[
    ~stock_board_industry_name_em_df['板块名称'].str.contains('|'.join(excluded_boards))
]

# 绘制概念板块排名图表
def show_board_ranking():
    date_range = st.selectbox('请选择绘制图表的时间段（概念板块）', ('5日', '10日', '20日', '30日', '60日'))
    days_dict = {'5日': 5, '10日': 10, '20日': 20, '30日': 30, '60日': 60}
    selected_days = days_dict[date_range]
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=selected_days)).strftime("%Y%m%d")

    filtered_boards = stock_board_concept_name_em_df.head(10)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    for index, row in filtered_boards.iterrows():
        board_name = row['板块名称']
        stock_board_concept_hist_em_df = ak.stock_board_concept_hist_em(
            symbol=board_name, period="daily",
            start_date=start_date, end_date=end_date, adjust=""
        )
        ax1.plot(
            stock_board_concept_hist_em_df['日期'],
            stock_board_concept_hist_em_df['成交额'],
            label=board_name
        )
        initial_close = stock_board_concept_hist_em_df['收盘'].iloc[0]
        scaled_close = stock_board_concept_hist_em_df['收盘'] / initial_close
        ax2.plot(
            stock_board_concept_hist_em_df['日期'],
            scaled_close,
            label=board_name
        )

    ax1.set_title(f"前十概念板块成交额 - 最近{selected_days}天", fontproperties=font_prop)
    ax1.set_xlabel("日期", fontproperties=font_prop)
    ax1.set_ylabel("成交额", fontproperties=font_prop)
    ax1.legend(loc="upper left", prop=font_prop)

    ax2.set_title(f"前十概念板块涨幅 - 最近{selected_days}天", fontproperties=font_prop)
    ax2.set_xlabel("日期", fontproperties=font_prop)
    ax2.set_ylabel("相对涨幅", fontproperties=font_prop)
    ax2.legend(loc="upper left", prop=font_prop)

    st.pyplot(fig)
    st.subheader("点击板块名称查看成份股信息")
    for index, row in filtered_boards.iterrows():
        board_name = row['板块名称']
        if st.button(board_name):
            stock_board_concept_cons_em_df = ak.stock_board_concept_cons_em(symbol=board_name)
            top_10_by_change = stock_board_concept_cons_em_df.sort_values(by='涨跌幅', ascending=False).head(10)
            st.write(f"{board_name} 涨幅前十成分股")
            st.dataframe(top_10_by_change[['名称', '代码', '涨跌幅', '成交额']])
            top_10_by_volume = stock_board_concept_cons_em_df.sort_values(by='成交额', ascending=False).head(10)
            st.write(f"{board_name} 成交额前十成分股")
            st.dataframe(top_10_by_volume[['名称', '代码', '成交额', '涨跌幅']])

# 绘制行业板块排名图表
def show_industry_ranking():
    date_range = st.selectbox('请选择绘制图表的时间段（行业排名）', ('5日', '10日', '20日', '30日', '60日'))
    days_dict = {'5日': 5, '10日': 10, '20日': 20, '30日': 30, '60日': 60}
    selected_days = days_dict[date_range]
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=selected_days)).strftime("%Y%m%d")

    filtered_boards = stock_board_industry_name_em_df.head(10)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    for index, row in filtered_boards.iterrows():
        board_name = row['板块名称']
        stock_board_industry_hist_em_df = ak.stock_board_industry_hist_em(
            symbol=board_name, period="日k",
            start_date=start_date, end_date=end_date, adjust=""
        )
        ax1.plot(
            stock_board_industry_hist_em_df['日期'],
            stock_board_industry_hist_em_df['成交额'],
            label=board_name
        )
        initial_close = stock_board_industry_hist_em_df['收盘'].iloc[0]
        scaled_close = stock_board_industry_hist_em_df['收盘'] / initial_close
        ax2.plot(
            stock_board_industry_hist_em_df['日期'],
            scaled_close,
            label=board_name
        )

    ax1.set_title(f"前十行业板块成交额 - 最近{selected_days}天", fontproperties=font_prop)
    ax1.set_xlabel("日期", fontproperties=font_prop)
    ax1.set_ylabel("成交额", fontproperties=font_prop)
    ax1.legend(loc="upper left", prop=font_prop)

    ax2.set_title(f"前十行业板块涨幅 - 最近{selected_days}天", fontproperties=font_prop)
    ax2.set_xlabel("日期", fontproperties=font_prop)
    ax2.set_ylabel("相对涨幅", fontproperties=font_prop)
    ax2.legend(loc="upper left", prop=font_prop)

    st.pyplot(fig)
    st.subheader("点击行业板块名称查看成份股信息")
    for index, row in filtered_boards.iterrows():
        board_name = row['板块名称']
        if st.button(board_name):
            stock_board_industry_cons_em_df = ak.stock_board_industry_cons_em(symbol=board_name)
            top_10_by_change = stock_board_industry_cons_em_df.sort_values(by='涨跌幅', ascending=False).head(10)
            st.write(f"{board_name} 涨幅前十成分股")
            st.dataframe(top_10_by_change[['名称', '代码', '涨跌幅', '成交额']])
            top_10_by_volume = stock_board_industry_cons_em_df.sort_values(by='成交额', ascending=False).head(10)
            st.write(f"{board_name} 成交额前十成分股")
            st.dataframe(top_10_by_volume[['名称', '代码', '成交额', '涨跌幅']])

# 显示微博舆情数据
def show_weibo_report():
    time_periods = ["CNDAY30", "CNDAY7", "CNHOUR24", "CNHOUR12", "CNHOUR6", "CNHOUR2"]
    time_period_names = ["一月", "一周", "一天", "12小时", "6小时", "2小时"]
    
    weibo_data = {}
    for period in time_periods:
        df = ak.stock_js_weibo_report(time_period=period)
        weibo_data[period] = df
    
    main_df = weibo_data["CNHOUR24"]
    main_df = main_df.sort_values(by="rate", ascending=False).reset_index(drop=True)
    
    top_ranges = [f"{i}-{i+9}" for i in range(1, 101, 10)]
    selected_range = st.selectbox("请选择要显示的排名范围", top_ranges)
    start, end = map(int, selected_range.split('-'))
    
    selected_stocks = main_df.loc[start-1:end-1, 'name'].tolist()
    
    fig, ax = plt.subplots(figsize=(14, 8))
    for stock in selected_stocks:
        rates = [weibo_data[period].set_index('name').at[stock, 'rate'] if stock in weibo_data[period]['name'].values else None for period in time_periods]
        ax.plot(time_period_names, rates, label=stock)
    
    ax.set_title("微博舆情股票人气变化趋势")
    ax.set_xlabel("时间段")
    ax.set_ylabel("人气指数")
    ax.legend()
    st.pyplot(fig)

# Streamlit 主程序
st.title("板块、行业和微博舆情报告展示")

option = st.selectbox('请选择要展示的内容', ('概念板块排名', '行业排名', '微博舆情报告'))
if option == '概念板块排名':
    show_board_ranking()
elif option == '行业排名':
    show_industry_ranking()
elif option == '微博舆情报告':
    show_weibo_report()
