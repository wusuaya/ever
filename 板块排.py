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

# 获取概念板块和行业板块数据
def get_boards():
    excluded_boards = ['昨日连板', '昨日涨停', '昨日连板_含一字', '昨日涨停_含一字', '百元股']
    concept_df = ak.stock_board_concept_name_em()
    concept_df = concept_df[~concept_df['板块名称'].str.contains('|'.join(excluded_boards))]
    industry_df = ak.stock_board_industry_name_em()
    industry_df = industry_df[~industry_df['板块名称'].str.contains('|'.join(excluded_boards))]
    return concept_df, industry_df

# 定义绘制概念板块排名的函数
def show_board_ranking(concept_df):
    date_range = st.selectbox('请选择绘制图表的时间段（概念板块）', ('5日', '10日', '20日', '30日', '60日'))
    days_dict = {'5日': 5, '10日': 10, '20日': 20, '30日': 30, '60日': 60}
    selected_days = days_dict[date_range]
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=selected_days)).strftime("%Y%m%d")

    filtered_boards = concept_df.head(10)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    for index, row in filtered_boards.iterrows():
        board_name = row['板块名称']
        stock_board_concept_hist_em_df = ak.stock_board_concept_hist_em(
            symbol=board_name, period="daily",
            start_date=start_date, end_date=end_date, adjust=""
        )
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

# 新增功能：NTTS 文件关联按钮
def ntts_association(concept_df, industry_df, ntts_file_path):
    try:
        # 读取 NTTS 文件
        ntts_data = pd.read_excel(ntts_file_path)
        ntts_data['code_clean'] = ntts_data['code'].astype(str).str.extract(r'(\d{6})')[0]  # 提取后六位数字

        # 获取所有概念板块和行业板块的成交量前十和涨幅前十的股票代码
        all_codes = set()

        for board_df, board_name in zip([concept_df, industry_df], ["概念板块", "行业板块"]):
            for _, row in board_df.head(10).iterrows():
                board_name = row['板块名称']
                cons_em_df = ak.stock_board_concept_cons_em(symbol=board_name) if board_name in concept_df.values else ak.stock_board_industry_cons_em(symbol=board_name)
                top_10_volume = cons_em_df.sort_values(by='成交额', ascending=False).head(10)['代码']
                top_10_change = cons_em_df.sort_values(by='涨跌幅', ascending=False).head(10)['代码']
                all_codes.update(top_10_volume.tolist())
                all_codes.update(top_10_change.tolist())

        # 匹配 NTTS 数据中的代码
        matched_data = ntts_data[ntts_data['code_clean'].isin(all_codes)]

        # 显示匹配结果
        if not matched_data.empty:
            st.subheader("NTTS 筛选统计关联的股票信息")
            st.dataframe(matched_data)
        else:
            st.write("没有匹配的股票信息。")
    except Exception as e:
        st.error(f"关联失败：{e}")

# Streamlit 主界面
def main():
    st.title("板块和行业排名图表展示")
    concept_df, industry_df = get_boards()
    
    # 显示概念板块排名
    if st.checkbox("显示概念板块排名"):
        show_board_ranking(concept_df)
    
    # 新增 NTTS 关联按钮
    ntts_file_path = "./NTTS筛选统计.xlsx"  # 根目录下的默认文件路径
    if st.button("NTTS 关联"):
        ntts_association(concept_df, industry_df, ntts_file_path)

if __name__ == "__main__":
    main()

