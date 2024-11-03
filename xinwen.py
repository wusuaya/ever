import streamlit as st
import akshare as ak
import datetime

# Set the title of the Streamlit app
st.title("财经新闻汇总")

# Get today's date
today = datetime.date.today()

# Button for 东方财富-财经早餐
if st.button("财经早餐 - 东方财富"):
    st.write("正在下载数据...")
    stock_info_cjzc_em_df = ak.stock_info_cjzc_em().head(10)
    st.write(stock_info_cjzc_em_df)
    for i in range(len(stock_info_cjzc_em_df)):
        st.markdown(f"[{stock_info_cjzc_em_df['标题'][i]}]({stock_info_cjzc_em_df['链接'][i]})")

# Button for 东方财富-全球财经快讯
if st.button("全球财经快讯 - 东方财富"):
    st.write("正在下载数据...")
    stock_info_global_em_df = ak.stock_info_global_em().head(10)
    st.write(stock_info_global_em_df)
    for i in range(len(stock_info_global_em_df)):
        st.markdown(f"[{stock_info_global_em_df['标题'][i]}]({stock_info_global_em_df['链接'][i]})")

# Button for 新浪财经-全球财经快讯
if st.button("全球财经快讯 - 新浪财经"):
    st.write("正在下载数据...")
    stock_info_global_sina_df = ak.stock_info_global_sina().head(10)
    st.write(stock_info_global_sina_df)

# Button for 富途牛牛-快讯
if st.button("快讯 - 富途牛牛"):
    st.write("正在下载数据...")
    stock_info_global_futu_df = ak.stock_info_global_futu().head(10)
    stock_info_global_futu_df = stock_info_global_futu_df[['发布时间', '标题', '内容']]
    st.write(stock_info_global_futu_df)

# Button for 同花顺财经-全球财经直播
if st.button("全球财经直播 - 同花顺财经"):
    st.write("正在下载数据...")
    stock_info_global_ths_df = ak.stock_info_global_ths().head(10)
    stock_info_global_ths_df = stock_info_global_ths_df[['发布时间', '标题', '内容']]
    st.write(stock_info_global_ths_df)

# Button for 财联社-电报
if st.button("电报 - 财联社"):
    st.write("正在下载数据...")
    stock_info_global_cls_df = ak.stock_info_global_cls(symbol="全部").head(10)
    stock_info_global_cls_df = stock_info_global_cls_df[['发布日期', '发布时间', '内容']]
    st.write(stock_info_global_cls_df)

# Button for 新浪财经-证券原创
if st.button("证券原创 - 新浪财经"):
    st.write("正在下载数据...")
    stock_info_broker_sina_df = ak.stock_info_broker_sina(page="1").head(10)
    for i in range(len(stock_info_broker_sina_df)):
        st.markdown(f"[{stock_info_broker_sina_df['内容'][i]}]({stock_info_broker_sina_df['链接'][i]})")

# Button for 新闻联播文字稿
if st.button("新闻联播文字稿"):
    st.write("正在下载数据...")
    news_cctv_df = ak.news_cctv(date=today.strftime("%Y%m%d"))
    if news_cctv_df.empty:
        # Try fetching data from the previous day if today's data is not available
        previous_day = today - datetime.timedelta(days=1)
        news_cctv_df = ak.news_cctv(date=previous_day.strftime("%Y%m%d"))
    if news_cctv_df.empty:
        st.write("暂无数据")
    else:
        loaded_count = 10
        st.write(news_cctv_df.head(loaded_count))
        if st.button("加载更多新闻联播文字稿"):
            loaded_count += 10
            st.write(news_cctv_df.head(loaded_count))
