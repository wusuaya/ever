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

# 获取板块数据
excluded_boards = ['昨日连板', '昨日涨停', '昨日连板_含一字', '昨日涨停_含一字', '百元股']
stock_board_concept_name_em_df = ak.stock_board_concept_name_em()
stock_board_concept_name_em_df = stock_board_concept_name_em_df[
    ~stock_board_concept_name_em_df['板块名称'].str.contains('|'.join(excluded_boards))
]
stock_board_industry_name_em_df = ak.stock_board_industry_name_em()
stock_board_industry_name_em_df = stock_board_industry_name_em_df[
    ~stock_board_industry_name_em_df['板块名称'].str.contains('|'.join(excluded_boards))
]

# 定义绘制概念板块排名的函数
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
        stock_board_concept_hist_em_df['日期'] = pd.to_datetime(stock_board_concept_hist_em_df['日期'], format="%Y%m%d")
        stock_board_concept_hist_em_df = stock_board_concept_hist_em_df.sort_values(by='日期')

        ax1.plot(stock_board_concept_hist_em_df['日期'], stock_board_concept_hist_em_df['成交额'], label=board_name)
        initial_close = stock_board_concept_hist_em_df['收盘'].iloc[0]
        scaled_close = stock_board_concept_hist_em_df['收盘'] / initial_close
        ax2.plot(stock_board_concept_hist_em_df['日期'], scaled_close, label=board_name)

    ax1.set_title(f"前十概念板块成交额 - 最近{selected_days}天", fontproperties=font_prop)
    ax1.set_xlabel("日期", fontproperties=font_prop)
    ax1.set_ylabel("成交额", fontproperties=font_prop)
    ax1.legend(loc="upper left", prop=font_prop)

    ax2.set_title(f"前十概念板块涨幅 - 最近{selected_days}天", fontproperties=font_prop)
    ax2.set_xlabel("日期", fontproperties=font_prop)
    ax2.set_ylabel("相对涨幅", fontproperties=font_prop)
    ax2.legend(loc="upper left", prop=font_prop)

    st.pyplot(fig)

# 显示板块数据的主函数
def show_board_data(board_type):
    if board_type == "概念板块":
        show_board_ranking()
    elif board_type == "行业板块":
        date_range = st.selectbox('请选择绘制图表的时间段（行业板块）', ('5日', '10日', '20日', '30日', '60日'))
        days_dict = {'5日': 5, '10日': 10, '20日': 20, '30日': 30, '60日': 60}
        selected_days = days_dict[date_range]
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=selected_days)).strftime("%Y%m%d")

        filtered_boards = stock_board_industry_name_em_df.head(10)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        for index, row in filtered_boards.iterrows():
            board_name = row['板块名称']
            stock_board_hist_em_df = ak.stock_board_industry_hist_em(
                symbol=board_name, period="日k",
                start_date=start_date, end_date=end_date, adjust=""
            )
            ax1.plot(stock_board_hist_em_df['日期'], stock_board_hist_em_df['成交额'], label=board_name)
            initial_close = stock_board_hist_em_df['收盘'].iloc[0]
            scaled_close = stock_board_hist_em_df['收盘'] / initial_close
            ax2.plot(stock_board_hist_em_df['日期'], scaled_close, label=board_name)

        ax1.set_title(f"前十行业板块成交额 - 最近{selected_days}天", fontproperties=font_prop)
        ax1.set_xlabel("日期", fontproperties=font_prop)
        ax1.set_ylabel("成交额", fontproperties=font_prop)
        ax1.legend(loc="upper left", prop=font_prop)

        ax2.set_title(f"前十行业板块涨幅 - 最近{selected_days}天", fontproperties=font_prop)
        ax2.set_xlabel("日期", fontproperties=font_prop)
        ax2.set_ylabel("相对涨幅", fontproperties=font_prop)
        ax2.legend(loc="upper left", prop=font_prop)

        st.pyplot(fig)

# Streamlit 应用主界面
st.title("板块和行业排名图表展示")
option = st.selectbox('请选择要展示的图表', ('概念板块', '行业板块'))

if option:
    show_board_data(option)

