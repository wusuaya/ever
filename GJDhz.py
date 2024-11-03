import streamlit as st
import pandas as pd
import akshare as ak
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Streamlit 界面
st.title("股票K线图和热度分析")

# 自由定义日期
custom_date = st.date_input("输入日期", value=datetime.now())
selected_date = custom_date.strftime('%Y-%m-%d')

# 自由定义股票代码
custom_code = st.text_input("输入股票代码（6位）", "")

# 检查股票代码是否为空
if custom_code:
    # 自动补齐前缀：适用SH和SZ等前缀
    if custom_code.startswith("6"):
        full_code = "SH" + custom_code
    elif custom_code.startswith("0") or custom_code.startswith("3"):
        full_code = "SZ" + custom_code
    else:
        full_code = custom_code  # 如果是其他市场代码，可以扩展

    # 自由定义起始和结束时间
    start_days = st.number_input("起始时间提前天数", value=60, min_value=1)
    end_days = st.number_input("结束时间延后天数", value=10, min_value=1)

    # 转换日期格式
    date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
    start_date = (date_obj - timedelta(days=start_days)).strftime('%Y%m%d')
    end_date = (date_obj + timedelta(days=end_days)).strftime('%Y%m%d')

    # 均线和布林线参数调节
    ma_period_1 = st.slider("第一个均线周期", 1, 250, 5)
    ma_period_2 = st.slider("第二个均线周期", 1, 250, 10)
    ma_period_3 = st.slider("第三个均线周期", 1, 250, 20)
    boll_period = st.slider("布林线周期", 1, 250, 20)
    boll_std = st.slider("布林线标准差", 0.1, 5.0, 2.5)

    # 获取股票历史数据
    symbol = custom_code
    try:
        # 使用 akshare 获取数据
        stock_data = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        if stock_data.empty:
            st.write("未能获取股票数据，请检查日期和代码的有效性")
        else:
            # 将日期转换为datetime对象，方便比较
            stock_data['日期'] = pd.to_datetime(stock_data['日期'])
            stock_data.set_index('日期', inplace=True)

            # 计算均线和布林线参数
            stock_data[f'MA{ma_period_1}'] = stock_data['收盘'].rolling(window=ma_period_1).mean()
            stock_data[f'MA{ma_period_2}'] = stock_data['收盘'].rolling(window=ma_period_2).mean()
            stock_data[f'MA{ma_period_3}'] = stock_data['收盘'].rolling(window=ma_period_3).mean()
            stock_data['Bollinger_up'] = stock_data[f'MA{ma_period_3}'] + boll_std * stock_data['收盘'].rolling(window=boll_period).std()
            stock_data['Bollinger_down'] = stock_data[f'MA{ma_period_3}'] - boll_std * stock_data['收盘'].rolling(window=boll_period).std()

            # 绘制交互式K线图
            fig1 = go.Figure()

            # 添加K线数据
            fig1.add_trace(go.Candlestick(
                x=stock_data.index,
                open=stock_data['开盘'],
                high=stock_data['最高'],
                low=stock_data['最低'],
                close=stock_data['收盘'],
                increasing_line_color='red',  # 上涨为红色
                decreasing_line_color='green',  # 下跌为绿色
                name='K线'
            ))

            # 添加均线数据
            fig1.add_trace(go.Scatter(x=stock_data.index, y=stock_data[f'MA{ma_period_1}'], mode='lines', name=f'MA{ma_period_1}'))
            fig1.add_trace(go.Scatter(x=stock_data.index, y=stock_data[f'MA{ma_period_2}'], mode='lines', name=f'MA{ma_period_2}'))
            fig1.add_trace(go.Scatter(x=stock_data.index, y=stock_data[f'MA{ma_period_3}'], mode='lines', name=f'MA{ma_period_3}'))

            # 添加布林线数据
            fig1.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Bollinger_up'],
                                      mode='lines', name='布林线上轨', line=dict(dash='dot', color='purple')))
            fig1.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Bollinger_down'],
                                      mode='lines', name='布林线下轨', line=dict(dash='dot', color='purple')))

            # 图表布局调整
            fig1.update_layout(
                title=f"{symbol} K线图",
                xaxis_title="日期",
                yaxis_title="价格",
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig1)

    except Exception as e:
        st.write(f"发生错误: {e}")

    # 获取股票热度排名数据
    try:
        hot_data = ak.stock_hot_rank_detail_em(symbol=full_code)
        hot_data['时间'] = pd.to_datetime(hot_data['时间'])
        hot_data.set_index('时间', inplace=True)

        # 绘制热度排名变化图（倒数显示）
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=hot_data.index, y=-hot_data['排名'], mode='lines+markers', line=dict(color='purple'), name='热度排名 (倒数)'))
        fig2.update_layout(title="热度排名变化", xaxis_title="时间", yaxis_title="排名（倒数）", hovermode="x")
        st.plotly_chart(fig2)

        # MACD参数设置
        short_period = st.slider("MACD短期周期", 5, 20, 12)
        long_period = st.slider("MACD长期周期", 20, 50, 26)

        # 计算新晋粉丝MACD
        hot_data['新晋粉丝_Short_EMA'] = hot_data['新晋粉丝'].ewm(span=short_period, adjust=False).mean()
        hot_data['新晋粉丝_Long_EMA'] = hot_data['新晋粉丝'].ewm(span=long_period, adjust=False).mean()
        hot_data['新晋粉丝_MACD'] = hot_data['新晋粉丝_Short_EMA'] - hot_data['新晋粉丝_Long_EMA']
        hot_data['新晋粉丝_Signal'] = hot_data['新晋粉丝_MACD'].ewm(span=9, adjust=False).mean()

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=hot_data.index, y=hot_data['新晋粉丝_MACD'], mode='lines', line=dict(color='blue'), name='新晋粉丝MACD'))
        fig3.add_trace(go.Scatter(x=hot_data.index, y=hot_data['新晋粉丝_Signal'], mode='lines', line=dict(color='orange'), name='信号线'))
        fig3.add_trace(go.Bar(x=hot_data.index, y=hot_data['新晋粉丝_MACD'] - hot_data['新晋粉丝_Signal'], name='新晋粉丝MACD差值', marker_color='gray'))
        fig3.update_layout(title="新晋粉丝MACD", xaxis_title="时间", yaxis_title="MACD值", hovermode="x")
        st.plotly_chart(fig3)

    except Exception as e:
        st.write("无法获取热度数据，请检查股票代码。")

else:
    st.write("请输入有效的股票代码。")

