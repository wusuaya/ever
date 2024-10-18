import akshare as ak
import pandas as pd
import streamlit as st
from datetime import datetime

# 定义每天更新数据的函数
def get_top_5(dataframe, name):
    """获取前五行数据"""
    if dataframe is not None and not dataframe.empty:
        st.write(f"### {name} 前五名")
        st.dataframe(dataframe.head(5))
    else:
        st.write(f"{name} 暂无数据")

# 定义每个接口的函数
def get_stock_hk_hot_rank_em():
    return ak.stock_hk_hot_rank_em()

def get_stock_hot_rank_em():
    return ak.stock_hot_rank_em()

def get_stock_hot_up_em():
    return ak.stock_hot_up_em()

def get_stock_hot_follow_xq():
    return ak.stock_hot_follow_xq(symbol="最热门")

def get_stock_hot_deal_xq():
    return ak.stock_hot_deal_xq(symbol="最热门")

def get_stock_hot_tweet_xq():
    return ak.stock_hot_tweet_xq(symbol="最热门")

def get_stock_hot_search_baidu():
    return ak.stock_hot_search_baidu(symbol="A股", date="20240929", time="今日")

def get_stock_comment_em():
    return ak.stock_comment_em()

def get_stock_hot_keyword_em():
    return ak.stock_hot_keyword_em(symbol="SZ000665")

def get_stock_hsgt_fund_flow_summary_em():
    return ak.stock_hsgt_fund_flow_summary_em()

def get_stock_hsgt_fund_min_em_north():
    return ak.stock_hsgt_fund_min_em(symbol="北向资金")

def get_stock_hsgt_fund_min_em_south():
    return ak.stock_hsgt_fund_min_em(symbol="南向资金")

# 使用Streamlit创建网页
st.title("股票数据每日更新")

# 显示人气榜-港股
hk_hot_rank_data = get_stock_hk_hot_rank_em()
get_top_5(hk_hot_rank_data, "人气榜-港股")

# 显示人气榜-A股
hot_rank_data = get_stock_hot_rank_em()
get_top_5(hot_rank_data, "人气榜-A股")

# 显示飙升榜-A股
hot_up_data = get_stock_hot_up_em()
get_top_5(hot_up_data, "飙升榜-A股")

# 显示雪球 关注排行榜
hot_follow_data = get_stock_hot_follow_xq()
get_top_5(hot_follow_data, "雪球 关注排行榜")

# 显示雪球 交易排行榜
hot_deal_data = get_stock_hot_deal_xq()
get_top_5(hot_deal_data, "雪球 交易排行榜")

# 显示雪球 讨论排行榜
hot_tweet_data = get_stock_hot_tweet_xq()
get_top_5(hot_tweet_data, "雪球 讨论排行榜")

# 显示热搜股票
hot_search_data = get_stock_hot_search_baidu()
get_top_5(hot_search_data, "热搜股票")

# 显示千股千评排名
comment_data = get_stock_comment_em()
get_top_5(comment_data, "千股千评排名")

# 显示热门关键词
hot_keyword_data = get_stock_hot_keyword_em()
get_top_5(hot_keyword_data, "热门关键词")

# 显示沪深港通资金流向
fund_flow_summary_data = get_stock_hsgt_fund_flow_summary_em()
get_top_5(fund_flow_summary_data, "沪深港通资金流向")

# 显示沪深港通分时数据-北向资金
fund_min_north_data = get_stock_hsgt_fund_min_em_north()
get_top_5(fund_min_north_data, "沪深港通分时数据-北向资金")

# 显示沪深港通分时数据-南向资金
fund_min_south_data = get_stock_hsgt_fund_min_em_south()
get_top_5(fund_min_south_data, "沪深港通分时数据-南向资金")

st.write("数据每日自动更新，页面会展示前五名。")
