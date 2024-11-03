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
        full_code = custom_code

    # 自定义起始和结束时间
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
        stock_data = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        if stock_data.empty:
            st.write("未能获取股票数据，请检查日期和代码的有效性")
        else:
            stock_data['日期'] = pd.to_datetime(stock_data['日期'])
            stock_data.set_index('日期', inplace=True)

            # 获取当日及下一个交易日的信息
            if date_obj in stock_data.index:
                today = stock_data.loc[date_obj]
                next_date = stock_data.index[stock_data.index.get_loc(date_obj) + 1] if date_obj in stock_data.index[:-1] else None
                next_day = stock_data.loc[next_date] if next_date is not None else None

                st.write("当日和下一交易日价格信息")
                today_data = {
                    "日期": [date_obj.strftime('%Y-%m-%d'), next_date.strftime('%Y-%m-%d') if next_date else None],
                    "开盘价": [today['开盘'], next_day['开盘'] if next_day is not None else None],
                    "收盘价": [today['收盘'], next_day['收盘'] if next_day is not None else None],
                    "最高价": [today['最高'], next_day['最高'] if next_day is not None else None],
                    "最低价": [today['最低'], next_day['最低'] if next_day is not None else None],
                }
                st.table(pd.DataFrame(today_data))

                # 计算支撑和阻力位
                H, L, C = today['最高'], today['最低'], today['收盘']
                P = (H + L + C) / 3
                R1, R2 = 2 * P - L, P + (H - L)
                S1, S2 = 2 * P - H, P - (H - L)
                fib_38_2 = L + 0.382 * (H - L)
                fib_61_8 = L + 0.618 * (H - L)

                st.write("基于当前日期计算的下一日支撑位和阻力位")
                pivot_data = {
                    "枢轴点 (P)": [P],
                    "阻力位1 (R1)": [R1],
                    "阻力位2 (R2)": [R2],
                    "支撑位1 (S1)": [S1],
                    "支撑位2 (S2)": [S2],
                    "斐波那契 38.2%": [fib_38_2],
                    "斐波那契 61.8%": [fib_61_8],
                }
                st.table(pd.DataFrame(pivot_data))

                # 七分位计算
                prev_close = C
                high_limit = round(prev_close * 1.1 if symbol.startswith("6") or symbol.startswith("0") else prev_close * 1.2, 2)
                range_size = (high_limit - prev_close) / 7
                positive_segments = [prev_close + i * range_size for i in range(1, 8)]
                negative_segments = [prev_close - i * range_size for i in range(1, 8)]
                seven_segments = negative_segments[::-1] + [prev_close] + positive_segments

                st.write("基于当前日期收盘价的下一日七分位信息")
                seven_segment_data = {
                    "位置": ["负七分位", "负六分位", "负五分位", "负四分位", "负三分位", "负二分位", "负一分位", "零轴（前收）", "正一分位", "正二分位", "正三分位", "正四分位", "正五分位", "正六分位", "正七分位"],
                    "价格": seven_segments
                }
                st.table(pd.DataFrame(seven_segment_data))

                # 均线和布林线参数计算信息
                today_ma1 = stock_data['收盘'].rolling(window=ma_period_1).mean().loc[date_obj]
                today_ma2 = stock_data['收盘'].rolling(window=ma_period_2).mean().loc[date_obj]
                today_ma3 = stock_data['收盘'].rolling(window=ma_period_3).mean().loc[date_obj]
                today_boll_up = stock_data['收盘'].rolling(window=boll_period).mean().loc[date_obj] + boll_std * stock_data['收盘'].rolling(window=boll_period).std().loc[date_obj]
                today_boll_down = stock_data['收盘'].rolling(window=boll_period).mean().loc[date_obj] - boll_std * stock_data['收盘'].rolling(window=boll_period).std().loc[date_obj]

                if next_day is not None:
                    next_day_ma1 = stock_data['收盘'].rolling(window=ma_period_1).mean().loc[next_date]
                    next_day_ma2 = stock_data['收盘'].rolling(window=ma_period_2).mean().loc[next_date]
                    next_day_ma3 = stock_data['收盘'].rolling(window=ma_period_3).mean().loc[next_date]
                    next_day_boll_up = stock_data['收盘'].rolling(window=boll_period).mean().loc[next_date] + boll_std * stock_data['收盘'].rolling(window=boll_period).std().loc[next_date]
                    next_day_boll_down = stock_data['收盘'].rolling(window=boll_period).mean().loc[next_date] - boll_std * stock_data['收盘'].rolling(window=boll_period).std().loc[next_date]
                else:
                    next_day_ma1 = next_day_ma2 = next_day_ma3 = next_day_boll_up = next_day_boll_down = None

                st.write("均线和布林线参数计算信息")
                ma_boll_data = {
                    "参数名称": [f"MA{ma_period_1}", f"MA{ma_period_2}", f"MA{ma_period_3}", "布林线上轨", "布林线下轨"],
                    "当日值": [today_ma1, today_ma2, today_ma3, today_boll_up, today_boll_down],
                    "下一交易日值": [next_day_ma1, next_day_ma2, next_day_ma3, next_day_boll_up, next_day_boll_down]
                }
                st.table(pd.DataFrame(ma_boll_data))

            # 绘制K线图及均线和布林线
            fig1 = go.Figure()
            fig1.add_trace(go.Candlestick(
                x=stock_data.index,
                open=stock_data['开盘'],
                high=stock_data['最高'],
                low=stock_data['最低'],
                close=stock_data['收盘'],
                increasing_line_color='red',
                decreasing_line_color='green',
                name='K线'
            ))
            stock_data[f'MA{ma_period_1}'] = stock_data['收盘'].rolling(window=ma_period_1).mean()
            stock_data[f'MA{ma_period_2}'] = stock_data['收盘'].rolling(window=ma_period_2).mean()
            stock_data[f'MA{ma_period_3}'] = stock_data['收盘'].rolling(window=ma_period_3).mean()
            stock_data['Bollinger_up'] = stock_data[f'MA{ma_period_3}'] + boll_std * stock_data['收盘'].rolling(window=boll_period).std()
            stock_data['Bollinger_down'] = stock_data[f'MA{ma_period_3}'] - boll_std * stock_data['收盘'].rolling(window=boll_period).std()
            fig1.add_trace(go.Scatter(x=stock_data.index, y=stock_data[f'MA{ma_period_1}'], mode='lines', name=f'MA{ma_period_1}'))
            fig1.add_trace(go.Scatter(x=stock_data.index, y=stock_data[f'MA{ma_period_2}'], mode='lines', name=f'MA{ma_period_2}'))
            fig1.add_trace(go.Scatter(x=stock_data.index, y=stock_data[f'MA{ma_period_3}'], mode='lines', name=f'MA{ma_period_3}'))
            fig1.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Bollinger_up'], mode='lines', name='布林线上轨', line=dict(dash='dot', color='purple')))
            fig1.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Bollinger_down'], mode='lines', name='布林线下轨', line=dict(dash='dot', color='purple')))
            fig1.update_layout(title=f"{symbol} K线图", xaxis_title="日期", yaxis_title="价格", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig1)

    except Exception as e:
        st.write(f"发生错误: {e}")

    # 获取股票热度排名数据
    try:
        hot_data = ak.stock_hot_rank_detail_em(symbol=full_code)
        hot_data['时间'] = pd.to_datetime(hot_data['时间'])
        hot_data.set_index('时间', inplace=True)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=hot_data.index, y=-hot_data['排名'], mode='lines+markers', line=dict(color='purple'), name='热度排名 (倒数)'))
        fig2.update_layout(title="热度排名变化", xaxis_title="时间", yaxis_title="排名（倒数）", hovermode="x")
        st.plotly_chart(fig2)

        # MACD参数设置
        short_period = st.slider("MACD短期周期", 5, 20, 12)
        long_period = st.slider("MACD长期周期", 20, 50, 26)
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


