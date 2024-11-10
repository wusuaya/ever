import streamlit as st
import akshare as ak
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

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

# Streamlit应用布局
st.title("微博舆情报告 - 股票数据分析")

# 用户选择
time_periods = ["CNHOUR12", "CNHOUR24", "CNDAY7", "CNDAY30"]
selected_ranks = st.selectbox("选择要绘制的股票排名区间", ["1-10", "11-20", "21-30", "31-40", "41-50", "1-100每隔10取一个"])

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
        return df.iloc[::10].iloc[:10]
    else:
        return df

# 将股票数据从右至左排列并绘制不同时间段的折线图
fig, ax = plt.subplots(figsize=(12, 6))
for stock in filter_data_by_rank(data_dict['CNHOUR24'], selected_ranks)['name']:
    ranks = []
    for period in reversed(time_periods):  # 从右到左排列时间段
        df = data_dict[period]
        # 获取排名，排名越高值越大
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

