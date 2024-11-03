import streamlit as st
import pandas as pd
import akshare as ak
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Streamlit 界面
st.title("股票K线图分析")

# 自由定义日期
custom_date = st.date_input("输入日期", value=datetime.now())
selected_date = custom_date.strftime('%Y-%m-%d')

# 自由定义股票代码
custom_code = st.text_input("输入股票代码（6位）", "")

# 检查股票代码是否为空
if custom_code:
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

    # 获取股票数据
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

            # 获取当日及下一日数据
            if date_obj in stock_data.index:
                today = stock_data.loc[date_obj]
                next_day = stock_data.loc[date_obj + timedelta(days=1)] if (date_obj + timedelta(days=1)) in stock_data.index else None

                # 展示当日和下一日的开盘、收盘、最高、最低信息
                st.write("当日和下一日价格信息")
                today_data = {
                    "日期": [date_obj.strftime('%Y-%m-%d'), (date_obj + timedelta(days=1)).strftime('%Y-%m-%d')],
                    "开盘价": [today['开盘'], next_day['开盘'] if next_day is not None else None],
                    "收盘价": [today['收盘'], next_day['收盘'] if next_day is not None else None],
                    "最高价": [today['最高'], next_day['最高'] if next_day is not None else None],
                    "最低价": [today['最低'], next_day['最低'] if next_day is not None else None],
                }
                st.table(pd.DataFrame(today_data))

                # 计算当日和下一日的均线和布林线参数
                today_ma1 = stock_data['收盘'].rolling(window=ma_period_1).mean().loc[date_obj]
                today_ma2 = stock_data['收盘'].rolling(window=ma_period_2).mean().loc[date_obj]
                today_ma3 = stock_data['收盘'].rolling(window=ma_period_3).mean().loc[date_obj]
                today_boll_up = stock_data['收盘'].rolling(window=boll_period).mean().loc[date_obj] + boll_std * stock_data['收盘'].rolling(window=boll_period).std().loc[date_obj]
                today_boll_down = stock_data['收盘'].rolling(window=boll_period).mean().loc[date_obj] - boll_std * stock_data['收盘'].rolling(window=boll_period).std().loc[date_obj]

                # 下一日均线和布林线值（如果有数据）
                if next_day is not None:
                    next_day_ma1 = stock_data['收盘'].rolling(window=ma_period_1).mean().loc[date_obj + timedelta(days=1)]
                    next_day_ma2 = stock_data['收盘'].rolling(window=ma_period_2).mean().loc[date_obj + timedelta(days=1)]
                    next_day_ma3 = stock_data['收盘'].rolling(window=ma_period_3).mean().loc[date_obj + timedelta(days=1)]
                    next_day_boll_up = stock_data['收盘'].rolling(window=boll_period).mean().loc[date_obj + timedelta(days=1)] + boll_std * stock_data['收盘'].rolling(window=boll_period).std().loc[date_obj + timedelta(days=1)]
                    next_day_boll_down = stock_data['收盘'].rolling(window=boll_period).mean().loc[date_obj + timedelta(days=1)] - boll_std * stock_data['收盘'].rolling(window=boll_period).std().loc[date_obj + timedelta(days=1)]
                else:
                    next_day_ma1 = next_day_ma2 = next_day_ma3 = next_day_boll_up = next_day_boll_down = None

                # 均线和布林线参数信息表格展示
                st.write("均线和布林线参数计算信息")
                ma_boll_data = {
                    "参数名称": ["MA" + str(ma_period_1), "MA" + str(ma_period_2), "MA" + str(ma_period_3), "布林线上轨", "布林线下轨"],
                    "当日值": [today_ma1, today_ma2, today_ma3, today_boll_up, today_boll_down],
                    "下一日值": [next_day_ma1, next_day_ma2, next_day_ma3, next_day_boll_up, next_day_boll_down]
                }
                st.table(pd.DataFrame(ma_boll_data))

            # 绘制交互式K线图
            fig = go.Figure()

            # 添加K线数据
            fig.add_trace(go.Candlestick(
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
            stock_data[f'MA{ma_period_1}'] = stock_data['收盘'].rolling(window=ma_period_1).mean()
            stock_data[f'MA{ma_period_2}'] = stock_data['收盘'].rolling(window=ma_period_2).mean()
            stock_data[f'MA{ma_period_3}'] = stock_data['收盘'].rolling(window=ma_period_3).mean()
            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data[f'MA{ma_period_1}'], mode='lines', name=f'MA{ma_period_1}'))
            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data[f'MA{ma_period_2}'], mode='lines', name=f'MA{ma_period_2}'))
            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data[f'MA{ma_period_3}'], mode='lines', name=f'MA{ma_period_3}'))

            # 添加布林线数据
            stock_data['Bollinger_up'] = stock_data[f'MA{ma_period_3}'] + boll_std * stock_data['收盘'].rolling(window=boll_period).std()
            stock_data['Bollinger_down'] = stock_data[f'MA{ma_period_3}'] - boll_std * stock_data['收盘'].rolling(window=boll_period).std()
            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Bollinger_up'],
                                     mode='lines', name='布林线上轨', line=dict(dash='dot', color='purple')))
            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Bollinger_down'],
                                     mode='lines', name='布林线下轨', line=dict(dash='dot', color='purple')))

            # 图表布局调整
            fig.update_layout(
                title=f"{symbol} K线图",
                xaxis_title="日期",
                yaxis_title="价格",
                xaxis_rangeslider_visible=False
            )

            # 显示图表
            st.plotly_chart(fig)

    except Exception as e:
        st.write(f"发生错误: {e}")

else:
    st.write("请输入有效的股票代码。")


