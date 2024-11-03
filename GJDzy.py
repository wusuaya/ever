import streamlit as st
import pandas as pd
import akshare as ak
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# 读取数据文件
data_file_path = 'modified_chat_records.xlsx'

# 检查文件是否存在，如果不存在则要求用户上传
if not os.path.exists(data_file_path):
    uploaded_file = st.file_uploader("上传聊天记录文件", type="xlsx")
    if uploaded_file is not None:
        with open(data_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("文件上传成功！")
    else:
        st.stop()

data = pd.read_excel(data_file_path)

# 清理和过滤有效股票代码
data = data[pd.to_numeric(data['First 6 Digits'], errors='coerce').notna()]
data['First 6 Digits'] = data['First 6 Digits'].astype(int).astype(str).str.zfill(6)

# Streamlit 界面
st.title("股票聊天记录和K线图分析")

# 自定义日期输入
custom_date = st.date_input("输入日期", datetime.today())
selected_date = custom_date.strftime('%Y-%m-%d')

# 根据选择的日期筛选股票代码
filtered_data = data[data['Date'] == selected_date]
valid_codes = filtered_data['First 6 Digits'].unique()

# 自定义股票代码输入
custom_code = st.text_input("输入股票代码（6位数字）", "")
selected_code = custom_code.zfill(6)  # 确保输入为6位数字

if selected_code in valid_codes:
    # 获取选择的行
    selected_row = filtered_data[filtered_data['First 6 Digits'] == selected_code]
    
    # 获取聊天信息并显示原文
    message_content = selected_row['Message'].values[0]
    st.write("聊天信息:", message_content)

    # 转换日期格式
    date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
    start_date = (date_obj - timedelta(days=60)).strftime('%Y%m%d')
    end_date = (date_obj + timedelta(days=10)).strftime('%Y%m%d')

    # 获取股票数据
    symbol = selected_code
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

                # 使用当日数据计算下一日的枢轴点、支撑/阻力位和斐波那契水平
                H = today['最高']
                L = today['最低']
                C = today['收盘']

                # 计算枢轴点和支撑/阻力位
                P = (H + L + C) / 3
                R1 = 2 * P - L
                R2 = P + (H - L)
                S1 = 2 * P - H
                S2 = P - (H - L)

                # 计算斐波那契回撤或扩展水平
                fibonacci_38_2 = L + 0.382 * (H - L)
                fibonacci_61_8 = L + 0.618 * (H - L)

                # 在表格中展示这些计算信息
                st.write("基于当前日期计算的下一日支撑位和阻力位")
                pivot_data = {
                    "枢轴点 (P)": [P],
                    "阻力位1 (R1)": [R1],
                    "阻力位2 (R2)": [R2],
                    "支撑位1 (S1)": [S1],
                    "支撑位2 (S2)": [S2],
                    "斐波那契 38.2%": [fibonacci_38_2],
                    "斐波那契 61.8%": [fibonacci_61_8],
                }
                st.table(pd.DataFrame(pivot_data))

                # 计算七分位信息，包括零轴和负数部分七档
                prev_close = C
                high_limit = prev_close * 1.1 if symbol.startswith("6") or symbol.startswith("0") else prev_close * 1.2
                high_limit = round(high_limit, 2)  # 考虑到可能的9.95%涨停情况
                range_size = (high_limit - prev_close) / 7
                positive_segments = [prev_close + i * range_size for i in range(1, 8)]
                negative_segments = [prev_close - i * range_size for i in range(1, 8)]
                seven_segments = negative_segments[::-1] + [prev_close] + positive_segments

                # 七分位信息表格展示
                st.write("基于当前日期收盘价的下一日七分位信息")
                seven_segment_data = {
                    "位置": ["负七分位", "负六分位", "负五分位", "负四分位", "负三分位", "负二分位", "负一分位", "零轴（前收）", "正一分位", "正二分位", "正三分位", "正四分位", "正五分位", "正六分位", "正七分位"],
                    "价格": seven_segments
                }
                st.table(pd.DataFrame(seven_segment_data))

            # 均线和布林线参数调节 - 增加输入框和滑块
            ma_period_1 = st.number_input("输入第一个均线周期参数", min_value=1, max_value=250, value=5)
            ma_period_2 = st.number_input("输入第二个均线周期参数", min_value=1, max_value=250, value=10)
            ma_period_3 = st.number_input("输入第三个均线周期参数", min_value=1, max_value=250, value=20)
            boll_period = st.number_input("输入布林线周期参数", min_value=1, max_value=250, value=20)
            boll_std = st.number_input("输入布林线标准差参数", min_value=0.1, max_value=5.0, value=2.5)

            # 将计算的均线和布林线值展示为图表
            st.write("均线和布林线参数计算信息")
            ma_boll_data = {
                "参数名称": ["第一个均线周期", "第二个均线周期", "第三个均线周期", "布林线周期", "布林线标准差"],
                "输入值": [ma_period_1, ma_period_2, ma_period_3, boll_period, boll_std],
            }
            st.table(pd.DataFrame(ma_boll_data))

            # 绘制交互式K线图
            fig = go.Figure()

            # 添加K线数据
            fig.add_trace(go.Candlestick(x=stock_data.index,
                                         open=stock_data['开盘'],
                                         high=stock_data['最高'],
                                         low=stock_data['最低'],
                                         close=stock_data['收盘'],
                                         name='K线'))

            # 绘制均线
            for period in [ma_period_1, ma_period_2, ma_period_3]:
                stock_data[f'MA{period}'] = stock_data['收盘'].rolling(window=period).mean()
                fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data[f'MA{period}'], mode='lines', name=f'MA{period}'))

            # 绘制布林线
            stock_data['MA'] = stock_data['收盘'].rolling(window=boll_period).mean()
            stock_data['Upper'] = stock_data['MA'] + (stock_data['收盘'].rolling(window=boll_period).std() * boll_std)
            stock_data['Lower'] = stock_data['MA'] - (stock_data['收盘'].rolling(window=boll_period).std() * boll_std)
            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Upper'], mode='lines', name='Upper Band', line=dict(color='red', width=1)))
            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Lower'], mode='lines', name='Lower Band', line=dict(color='red', width=1)))

            # 更新布局和展示
            fig.update_layout(title=f'{symbol} 股票 K线图', xaxis_title='日期', yaxis_title='价格', xaxis_rangeslider_visible=False)
            st.plotly_chart(fig)

    except Exception as e:
        st.error(f"出现错误: {e}")
