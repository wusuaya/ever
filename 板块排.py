
import streamlit as st
import akshare as ak
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.font_manager as fm
import os
import pandas as pd
import plotly.graph_objects as go
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

# 显示板块数据
def show_board_ranking(board_type):
    date_range = st.selectbox('请选择绘制图表的时间段', ('5日', '10日', '20日', '30日', '60日'))
    days_dict = {'5日': 5, '10日': 10, '20日': 20, '30日': 30, '60日': 60}
    selected_days = days_dict[date_range]
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=selected_days)).strftime("%Y%m%d")

    filtered_boards = stock_board_concept_name_em_df.head(10) if board_type == "概念板块" else stock_board_industry_name_em_df.head(10)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    for index, row in filtered_boards.iterrows():
        board_name = row['板块名称']
        stock_board_hist_em_df = ak.stock_board_concept_hist_em(
            symbol=board_name, period="daily",
            start_date=start_date, end_date=end_date, adjust=""
        ) if board_type == "概念板块" else ak.stock_board_industry_hist_em(
            symbol=board_name, period="日k",
            start_date=start_date, end_date=end_date, adjust=""
        )

        # 按日期升序排列
        stock_board_hist_em_df['日期'] = pd.to_datetime(stock_board_hist_em_df['日期'], format='%Y%m%d', errors='coerce')
        stock_board_hist_em_df = stock_board_hist_em_df.dropna(subset=['日期'])

        # 确保数据按日期升序排列
        stock_board_hist_em_df = stock_board_hist_em_df.sort_values(by='日期')

        ax1.plot(stock_board_hist_em_df['日期'], stock_board_hist_em_df['成交额'], label=board_name)
        initial_close = stock_board_hist_em_df['收盘'].iloc[0]
        scaled_close = stock_board_hist_em_df['收盘'] / initial_close
        ax2.plot(stock_board_hist_em_df['日期'], scaled_close, label=board_name)

    ax1.set_title(f"前十{board_type}成交额 - 最近{selected_days}天", fontproperties=font_prop)
    ax1.set_xlabel("日期", fontproperties=font_prop)
    ax1.set_ylabel("成交额", fontproperties=font_prop)
    ax1.legend(loc="upper left", prop=font_prop)

    ax2.set_title(f"前十{board_type}涨幅 - 最近{selected_days}天", fontproperties=font_prop)
    ax2.set_xlabel("日期", fontproperties=font_prop)
    ax2.set_ylabel("相对涨幅", fontproperties=font_prop)
    ax2.legend(loc="upper left", prop=font_prop)

    st.pyplot(fig)

    # 重复个股统计
    st.subheader("重复出现的个股（按重复次数排序）")
    stock_count = defaultdict(lambda: {'count': 0, 'boards': []})
    for board_name in filtered_boards['板块名称']:
        try:
            stock_board_cons_em_df = ak.stock_board_concept_cons_em(symbol=board_name) if board_type == "概念板块" else ak.stock_board_industry_cons_em(symbol=board_name)
            top_10_by_volume = stock_board_cons_em_df.sort_values(by='成交额', ascending=False).head(10)
            top_10_by_change = stock_board_cons_em_df.sort_values(by='涨跌幅', ascending=False).head(10)
            for _, row in pd.concat([top_10_by_volume, top_10_by_change]).drop_duplicates().iterrows():
                stock_name = row['名称']
                stock_count[stock_name]['count'] += 1
                stock_count[stock_name]['boards'].append(f"{board_name}（{board_type}）")
        except KeyError:
            st.warning(f"未能获取 {board_name} 的成分股数据。")

    repeated_stocks = pd.DataFrame([
        {'个股名称': stock, '重复次数': info['count'], '所属板块': ', '.join(set(info['boards']))}
        for stock, info in stock_count.items() if info['count'] > 1
    ])
    if not repeated_stocks.empty:
        st.dataframe(repeated_stocks.sort_values(by='重复次数', ascending=False))
    else:
        st.write("没有重复出现的个股。")

    # 展示所有板块的详细数据和MACD图表
    if st.button(f"展示所有前十{board_type}数据"):
        for index, row in filtered_boards.iterrows():
            board_name = row['板块名称']
            st.write(f"### {board_name}")
            stock_board_cons_em_df = ak.stock_board_concept_cons_em(symbol=board_name) if board_type == "概念板块" else ak.stock_board_industry_cons_em(symbol=board_name)
            top_10_by_change = stock_board_cons_em_df.sort_values(by='涨跌幅', ascending=False).head(10)
            st.write(f"{board_name} 涨幅前十成分股")
            st.dataframe(top_10_by_change[['名称', '代码', '涨跌幅', '成交额']])
            top_10_by_volume = stock_board_cons_em_df.sort_values(by='成交额', ascending=False).head(10)
            st.write(f"{board_name} 成交额前十成分股")
            st.dataframe(top_10_by_volume[['名称', '代码', '成交额', '涨跌幅']])

            short_period = 12
            long_period = 26
            signal_period = 9

            for name, top_10 in zip(['涨幅前十', '成交额前十'], [top_10_by_change, top_10_by_volume]):
                total_weight = top_10['成交额'].sum()
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

                weighted_data['Short_EMA'] = weighted_data['新晋粉丝加权'].ewm(span=short_period, adjust=False).mean()
                weighted_data['Long_EMA'] = weighted_data['新晋粉丝加权'].ewm(span=long_period, adjust=False).mean()
                weighted_data['MACD'] = weighted_data['Short_EMA'] - weighted_data['Long_EMA']
                weighted_data['Signal'] = weighted_data['MACD'].ewm(span=signal_period, adjust=False).mean()

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=weighted_data.index, y=weighted_data['MACD'], mode='lines', name=f'{name} MACD'))
                fig.add_trace(go.Scatter(x=weighted_data.index, y=weighted_data['Signal'], mode='lines', name='信号线'))
                fig.update_layout(title=f"{board_name} - {name} 加权新晋粉丝MACD", xaxis_title="时间", yaxis_title="MACD值")
                st.plotly_chart(fig)

# Streamlit 应用主界面
st.title("板块和行业排名图表展示")
option = st.selectbox('请选择要展示的图表', ('概念板块', '行业板块'))

if option == '概念板块':
    show_board_ranking("概念板块")
elif option == '行业板块':
    show_board_ranking("行业板块")
