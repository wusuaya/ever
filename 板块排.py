import streamlit as st
import akshare as ak
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime, timedelta

# 设置字体，确保系统上有SimHei字体或其他支持中文的字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用SimHei字体显示中文
plt.rcParams['axes.unicode_minus'] = False    # 解决坐标轴负号显示问题

# 获取日期范围的选择
date_range = st.selectbox(
    '请选择绘制图表的时间段',
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

# 设置标题
st.title(f"东方财富概念板块-近{selected_days}天")

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
    board_code = row['板块代码']
    
    # 获取板块的历史数据
    stock_board_concept_hist_em_df = ak.stock_board_concept_hist_em(symbol=board_name, period="daily", 
                                                                   start_date=start_date, end_date=end_date, adjust="")
    
    # 绘制成交额折线图
    ax1.plot(stock_board_concept_hist_em_df['日期'], stock_board_concept_hist_em_df['成交额'], label=board_name)
    
    # 绘制涨幅折线图
    initial_close = stock_board_concept_hist_em_df['收盘'].iloc[0]
    scaled_close = stock_board_concept_hist_em_df['收盘'] / initial_close  # 按比例缩放
    ax2.plot(stock_board_concept_hist_em_df['日期'], scaled_close, label=board_name)

# 设置图表标题和图例
ax1.set_title(f"前十概念板块成交额 - 最近{selected_days}天")
ax1.set_xlabel("日期")
ax1.set_ylabel("成交额")
ax1.legend(loc="upper left")

ax2.set_title(f"前十概念板块涨幅 - 最近{selected_days}天")
ax2.set_xlabel("日期")
ax2.set_ylabel("相对涨幅")
ax2.legend(loc="upper left")

# 在Streamlit中显示图表
st.pyplot(fig)

# 2. 动态生成按钮
st.subheader("点击板块名称查看成份股信息")

for index, row in filtered_boards.iterrows():
    board_name = row['板块名称']
    board_code = row['板块代码']
    
    # 生成按钮，当按钮被点击时，显示成分股信息
    if st.button(board_name):
        # 获取该板块的成份股数据
        stock_board_concept_cons_em_df = ak.stock_board_concept_cons_em(symbol=board_name)
        
        # 按涨幅排名前十的成份股
        top_10_by_change = stock_board_concept_cons_em_df.sort_values(by='涨跌幅', ascending=False).head(10)
        st.write(f"{board_name} 涨幅前十成分股")
        st.dataframe(top_10_by_change[['名称', '代码', '涨跌幅', '成交额']])

        # 按成交额排名前十的成份股
        top_10_by_volume = stock_board_concept_cons_em_df.sort_values(by='成交额', ascending=False).head(10)
        st.write(f"{board_name} 成交额前十成分股")
        st.dataframe(top_10_by_volume[['名称', '代码', '成交额', '涨跌幅']])



# 设置字体，确保系统上有SimHei字体或其他支持中文的字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用SimHei字体显示中文
plt.rcParams['axes.unicode_minus'] = False    # 解决坐标轴负号显示问题

# 获取日期范围的选择
date_range = st.selectbox(
    '请选择绘制图表的时间段',
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

# 设置标题
st.title(f"东方财富行业板块-近{selected_days}天")

# 获取行业板块数据
stock_board_industry_name_em_df = ak.stock_board_industry_name_em()

# 去掉特定的板块名称
excluded_boards = ['昨日连板', '昨日涨停', '昨日连板_含一字', '昨日涨停_含一字', '百元股']
filtered_boards = stock_board_industry_name_em_df[
    (~stock_board_industry_name_em_df['板块名称'].str.contains('|'.join(excluded_boards)))
].head(10)

# 1. 绘制成交额和涨幅折线图
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

for index, row in filtered_boards.iterrows():
    board_name = row['板块名称']
    board_code = row['板块代码']
    
    # 获取行业板块的历史数据
    stock_board_industry_hist_em_df = ak.stock_board_industry_hist_em(symbol=board_name, period="日k", 
                                                                     start_date=start_date, end_date=end_date, adjust="")
    
    # 绘制成交额折线图
    ax1.plot(stock_board_industry_hist_em_df['日期'], stock_board_industry_hist_em_df['成交额'], label=board_name)
    
    # 绘制涨幅折线图
    initial_close = stock_board_industry_hist_em_df['收盘'].iloc[0]
    scaled_close = stock_board_industry_hist_em_df['收盘'] / initial_close  # 按比例缩放
    ax2.plot(stock_board_industry_hist_em_df['日期'], scaled_close, label=board_name)

# 设置图表标题和图例
ax1.set_title(f"前十行业板块成交额 - 最近{selected_days}天")
ax1.set_xlabel("日期")
ax1.set_ylabel("成交额")
ax1.legend(loc="upper left")

ax2.set_title(f"前十行业板块涨幅 - 最近{selected_days}天")
ax2.set_xlabel("日期")
ax2.set_ylabel("相对涨幅")
ax2.legend(loc="upper left")

# 在Streamlit中显示图表
st.pyplot(fig)

# 2. 动态生成按钮
st.subheader("点击行业板块名称查看成份股信息")

for index, row in filtered_boards.iterrows():
    board_name = row['板块名称']
    board_code = row['板块代码']
    
    # 生成按钮，当按钮被点击时，显示成分股信息
    if st.button(board_name):
        # 获取该行业板块的成份股数据
        stock_board_industry_cons_em_df = ak.stock_board_industry_cons_em(symbol=board_name)
        
        # 按涨幅排名前十的成份股
        top_10_by_change = stock_board_industry_cons_em_df.sort_values(by='涨跌幅', ascending=False).head(10)
        st.write(f"{board_name} 涨幅前十成分股")
        st.dataframe(top_10_by_change[['名称', '代码', '涨跌幅', '成交额']])

        # 按成交额排名前十的成份股
        top_10_by_volume = stock_board_industry_cons_em_df.sort_values(by='成交额', ascending=False).head(10)
        st.write(f"{board_name} 成交额前十成分股")
        st.dataframe(top_10_by_volume[['名称', '代码', '成交额', '涨跌幅']])

