import streamlit as st
import akshare as ak
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.font_manager as fm
import os

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
        # 输出调试信息，查看字体是否加载成功
        st.success(f"字体文件加载成功：{font_path}")

        # 设置 Matplotlib 全局字体
        plt.rcParams['font.family'] = font_prop.get_name()
        plt.rcParams['font.size'] = 12  # 设置字体大小
        plt.rcParams['axes.unicode_minus'] = False  # 解决坐标轴负号显示问题
    except Exception as e:
        st.error(f"加载字体时出错：{e}")

# 定义绘制概念板块排名的函数
def show_board_ranking():
    # 获取日期范围的选择
    date_range = st.selectbox(
        '请选择绘制图表的时间段（概念板块）',
        ('5日', '10日', '20日', '30日', '60日')
    )

    # 根据选择的时间段设置对应的天数
    days_dict = {
        '5日': 5,
        '10日': 10,
        '20日': 20,
        '30日': 30,
        '60日': 60
    }
    selected_days = days_dict[date_range]

    # 获取今天的日期和对应时间段的开始日期
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=selected_days)).strftime("%Y%m%d")

    # 获取概念板块数据
    stock_board_concept_name_em_df = ak.stock_board_concept_name_em()

    # 去掉特定的板块名称
    excluded_boards = ['昨日连板', '昨日涨停', '昨日连板_含一字', '昨日涨停_含一字', '百元股']
    filtered_boards = stock_board_concept_name_em_df[
        (~stock_board_concept_name_em_df['板块名称'].str.contains('|'.join(excluded_boards)))
    ].head(10)

    # 1. 绘制成交额和涨幅折线图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    for index, row in filtered_boards.iterrows():
        board_name = row['板块名称']
        # 获取板块的历史数据
        stock_board_concept_hist_em_df = ak.stock_board_concept_hist_em(
            symbol=board_name, period="daily",
            start_date=start_date, end_date=end_date, adjust=""
        )

        # 绘制成交额折线图
        ax1.plot(
            stock_board_concept_hist_em_df['日期'],
            stock_board_concept_hist_em_df['成交额'],
            label=board_name
        )

        # 绘制涨幅折线图
        initial_close = stock_board_concept_hist_em_df['收盘'].iloc[0]
        scaled_close = stock_board_concept_hist_em_df['收盘'] / initial_close  # 按比例缩放
        ax2.plot(
            stock_board_concept_hist_em_df['日期'],
            scaled_close,
            label=board_name
        )

    # 显式设置标题、X轴和Y轴的字体属性
    ax1.set_title(f"前十概念板块成交额 - 最近{selected_days}天", fontproperties=font_prop)
    ax1.set_xlabel("日期", fontproperties=font_prop)
    ax1.set_ylabel("成交额", fontproperties=font_prop)
    ax1.legend(loc="upper left", prop=font_prop)

    ax2.set_title(f"前十概念板块涨幅 - 最近{selected_days}天", fontproperties=font_prop)
    ax2.set_xlabel("日期", fontproperties=font_prop)
    ax2.set_ylabel("相对涨幅", fontproperties=font_prop)
    ax2.legend(loc="upper left", prop=font_prop)

    # 在 Streamlit 中显示图表
    st.pyplot(fig)

    # 生成按钮查看成分股信息
    st.subheader("点击板块名称查看成份股信息")
    for index, row in filtered_boards.iterrows():
        board_name = row['板块名称']
        if st.button(board_name):
            # 获取成分股数据
            stock_board_concept_cons_em_df = ak.stock_board_concept_cons_em(symbol=board_name)

            # 按涨幅排名前十的成分股
            top_10_by_change = stock_board_concept_cons_em_df.sort_values(
                by='涨跌幅', ascending=False
            ).head(10)
            st.write(f"{board_name} 涨幅前十成分股")
            st.dataframe(top_10_by_change[['名称', '代码', '涨跌幅', '成交额']])

            # 按成交额排名前十的成分股
            top_10_by_volume = stock_board_concept_cons_em_df.sort_values(
                by='成交额', ascending=False
            ).head(10)
            st.write(f"{board_name} 成交额前十成分股")
            st.dataframe(top_10_by_volume[['名称', '代码', '成交额', '涨跌幅']])

# Streamlit 应用主界面
st.title("板块和行业排名图表展示")

# 创建选择框来选择显示的内容
option = st.selectbox('请选择要展示的图表', ('概念板块排名', '行业排名'))

# 根据选择显示相应的图表
if option == '概念板块排名':
    show_board_ranking()
elif option == '行业排名':
    # 定义行业排名的代码逻辑，可以与 show_board_ranking 类似的结构
    pass

