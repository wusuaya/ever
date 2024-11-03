import streamlit as st
import akshare as ak
import pandas as pd
import datetime
import plotly.graph_objects as go

# 获取当天日期并倒推100天
end_date = datetime.datetime.now().strftime("%Y%m%d")
start_date = (datetime.datetime.now() - datetime.timedelta(days=100)).strftime("%Y%m%d")

# 用户输入股票代码，不补全字母前缀
stock_code = st.text_input("请输入股票代码（六位数字）：", "000001")

# 自动补齐前缀：适用SH和SZ等前缀
if stock_code.startswith("6"):
    full_code = "SH" + stock_code
elif stock_code.startswith("0") or stock_code.startswith("3"):
    full_code = "SZ" + stock_code
else:
    full_code = stock_code  # 如果是其他市场代码，可以扩展

# 布林线参数设置
bollinger_period = st.slider("布林线周期", 10, 30, 20)
bollinger_std_dev = st.slider("布林线标准差", 1.0, 3.0, 2.0)

# 获取股票历史数据
try:
    stock_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
    stock_data['日期'] = pd.to_datetime(stock_data['日期'])
    stock_data.set_index('日期', inplace=True)

    # 去掉非交易日，只保留成交量大于0的记录
    stock_data = stock_data[stock_data['成交量'] > 0]

    # 计算布林线
    stock_data['MA'] = stock_data['收盘'].rolling(window=bollinger_period).mean()
    stock_data['Upper'] = stock_data['MA'] + bollinger_std_dev * stock_data['收盘'].rolling(window=bollinger_period).std()
    stock_data['Lower'] = stock_data['MA'] - bollinger_std_dev * stock_data['收盘'].rolling(window=bollinger_period).std()

    # 绘制K线图和布林线
    fig1 = go.Figure()

    # K线图
    fig1.add_trace(go.Candlestick(
        x=stock_data.index,
        open=stock_data['开盘'],
        high=stock_data['最高'],
        low=stock_data['最低'],
        close=stock_data['收盘'],
        name="K线图"
    ))

    # 布林线上下轨及中轨
    fig1.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Upper'], mode='lines', line=dict(color='blue', dash='dash'), name='上轨'))
    fig1.add_trace(go.Scatter(x=stock_data.index, y=stock_data['MA'], mode='lines', line=dict(color='black'), name='中轨'))
    fig1.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Lower'], mode='lines', line=dict(color='blue', dash='dash'), name='下轨'))
    fig1.update_layout(title="K线图及布林线", xaxis_title="日期", yaxis_title="价格", hovermode="x")
    st.plotly_chart(fig1)

except Exception as e:
    st.write("无法获取股票数据，请检查代码是否正确。")

# 获取股票历史热度数据
try:
    hot_data = ak.stock_hot_rank_detail_em(symbol=full_code)
    hot_data['时间'] = pd.to_datetime(hot_data['时间'])
    hot_data.set_index('时间', inplace=True)

    # 绘制排名变化图（倒数显示）
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

    # 计算“粉丝和”MACD
    hot_data['粉丝和'] = hot_data['新晋粉丝'] + hot_data['铁杆粉丝']
    hot_data['粉丝和_Short_EMA'] = hot_data['粉丝和'].ewm(span=short_period, adjust=False).mean()
    hot_data['粉丝和_Long_EMA'] = hot_data['粉丝和'].ewm(span=long_period, adjust=False).mean()
    hot_data['粉丝和_MACD'] = hot_data['粉丝和_Short_EMA'] - hot_data['粉丝和_Long_EMA']
    hot_data['粉丝和_Signal'] = hot_data['粉丝和_MACD'].ewm(span=9, adjust=False).mean()

    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=hot_data.index, y=hot_data['粉丝和_MACD'], mode='lines', line=dict(color='blue'), name='粉丝和MACD'))
    fig4.add_trace(go.Scatter(x=hot_data.index, y=hot_data['粉丝和_Signal'], mode='lines', line=dict(color='orange'), name='信号线'))
    fig4.add_trace(go.Bar(x=hot_data.index, y=hot_data['粉丝和_MACD'] - hot_data['粉丝和_Signal'], name='粉丝和MACD差值', marker_color='gray'))
    fig4.update_layout(title="粉丝和MACD", xaxis_title="时间", yaxis_title="MACD值", hovermode="x")
    st.plotly_chart(fig4)

except Exception as e:
    st.write("无法获取热度数据，请检查股票代码。")

