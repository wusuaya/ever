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

# 显示微博舆情数据
def show_weibo_report():
    st.header("微博舆情报告 - 股票人气变化趋势")
    time_periods = ["CNDAY30", "CNDAY7", "CNHOUR24", "CNHOUR12", "CNHOUR6", "CNHOUR2"]
    time_period_names = ["一月", "一周", "一天", "12小时", "6小时", "2小时"]
    
    weibo_data = {}
    for period in time_periods:
        try:
            df = ak.stock_js_weibo_report(time_period=period)
            # 检查 'rate' 列是否存在
            if 'rate' not in df.columns:
                st.warning(f"数据中缺少 'rate' 列，无法处理 {period} 的数据")
                continue
            weibo_data[period] = df
        except Exception as e:
            st.error(f"获取 {period} 数据时出错: {e}")
            continue
    
    if "CNHOUR24" not in weibo_data:
        st.error("无法获取 1 天的舆情数据，请检查数据源")
        return
    
    main_df = weibo_data["CNHOUR24"]
    main_df = main_df.sort_values(by="rate", ascending=False).reset_index(drop=True)
    
    top_ranges = [f"{i}-{i+9}" for i in range(1, 101, 10)]
    selected_range = st.selectbox("请选择要显示的排名范围", top_ranges)
    start, end = map(int, selected_range.split('-'))
    
    selected_stocks = main_df.loc[start-1:end-1, 'name'].tolist()
    
    fig, ax = plt.subplots(figsize=(14, 8))
    for stock in selected_stocks:
        rates = [
            weibo_data[period].set_index('name').at[stock, 'rate'] if stock in weibo_data[period]['name'].values else None
            for period in time_periods
        ]
        ax.plot(time_period_names, rates, label=stock)
    
    ax.set_title("微博舆情股票人气变化趋势")
    ax.set_xlabel("时间段")
    ax.set_ylabel("人气指数")
    ax.legend()
    st.pyplot(fig)

# 调用微博舆情报告函数
show_weibo_report()

# 以下为你上传的原代码（保持不变）
# --原代码开始--
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

excluded_boards = ['昨日连板', '昨日涨停', '昨日连板_含一字', '昨日涨停_含一字', '百元股']
stock_board_concept_name_em_df = ak.stock_board_concept_name_em()
stock_board_concept_name_em_df = stock_board_concept_name_em_df[
    ~stock_board_concept_name_em_df['板块名称'].str.contains('|'.join(excluded_boards))
]

stock_board_industry_name_em_df = ak.stock_board_industry_name_em()
stock_board_industry_name_em_df = stock_board_industry_name_em_df[
    ~stock_board_industry_name_em_df['板块名称'].str.contains('|'.join(excluded_boards))
]

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

# 显示重复个股的统计信息的原始代码请保持不变

st.title("板块和行业排名图表展示")

option = st.selectbox('请选择要展示的图表', ('概念板块排名', '行业排名'))

if option == '概念板块排名':
    show_board_ranking()
elif option == '行业排名':
    show_industry_ranking()

# 调用 show_repeated_stocks() 函数的位置请保持不变


