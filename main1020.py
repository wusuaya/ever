import streamlit as st
import akshare as ak
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 设置中文字体
font_path = "C:\\Windows\\Fonts\\simsun.ttc"  # 替换为实际的中文字体路径
plt.rcParams['font.family'] = fm.FontProperties(fname=font_path).get_name()

# 获取不同时间段数据的函数
def get_weibo_data(time_period):
    return ak.stock_js_weibo_report(time_period=time_period)

# Streamlit应用布局
st.title("微博舆情报告股票数据分析")

# 用户选择
time_periods = ["CNHOUR12", "CNHOUR24", "CNDAY7", "CNDAY30"]
selected_ranks = st.selectbox("选择要绘制的排名区间", ["1-10", "11-20", "21-30", "31-40", "41-50", "1-100每隔10取一个"])

# 获取所有时间段的数据
data_dict = {}
for period in time_periods:
    data_dict[period] = get_weibo_data(period)

# 按选择区间筛选股票数据
def filter_data_by_rank(df, rank_str):
    if rank_str == "1-10":
        return df.iloc[:10]
    elif rank_str == "11-20":
        return df.iloc[10:20]
    elif rank_str == "21-30":
        return df.iloc[20:30]
    elif rank_str == "31-40":
        return df.iloc[30:40]
    elif rank_str == "41-50":
        return df.iloc[40:50]
    elif rank_str == "1-100每隔10取一个":
        return df.iloc[::10].iloc[:10]  # 每隔10取一个，最多取10个
    else:
        return df

# 绘制折线图
fig, ax = plt.subplots(figsize=(12, 6))
for i, (period, df) in enumerate(data_dict.items()):
    filtered_df = filter_data_by_rank(df, selected_ranks)
    ax.plot(
        filtered_df['name'],
        filtered_df['rate'],
        marker='o',
        label=f"{period}数据"
    )

ax.set_title("微博舆情股票数据对比")
ax.set_xlabel("股票名称")
ax.set_ylabel("人气排行指数")
ax.legend()
plt.xticks(rotation=45)

# 展示图表
st.pyplot(fig)

