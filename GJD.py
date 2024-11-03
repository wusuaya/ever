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

# 日期选择
dates = data['Date'].dropna().unique()
selected_date = st.selectbox("选择日期", options=sorted(dates))

# 根据选择的日期筛选股票代码
filtered_data = data[data['Date'] == selected_date]
valid_codes = filtered_data['First 6 Digits'].unique()

# 股票代码选择
selected_code = st.selectbox("选择股票代码", options=sorted(valid_codes))

# 获取选择的行
selected_row = filtered_data[filtered_data['First 6 Digits'] == selected_code]

if not selected_row.empty:
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

            # 均线和布林线参数调节
            ma_period_1_slider = st.slider("选择第一个均线周期参数 (滑块)", 1, 250, 5)
            ma_period_2_slider = st.slider("选择第二个均线周期参数 (滑块)", 1, 250, 10)
            ma_period_3_slider = st.slider("选择第三个均线周期参数 (滑块)", 1, 250, 20)
            boll_period_slider = st.slider("选择布林线周期参数 (滑块)", 1, 250, 20)
            boll_std_slider = st.slider("选择布林线标准差参数 (滑块)", 0.1, 5.0, 2.5)

            # 计算均线
            stock_data[f"MA{ma_period_1_slider}"] = stock_data['收盘'].rolling(window=ma_period_1_slider).mean()
            stock_data[f"MA{ma_period_2_slider}"] = stock_data['收盘'].rolling(window=ma_period_2_slider).mean()
            stock_data[f"MA{ma_period_3_slider}"] = stock_data['收盘'].rolling(window=ma_period_3_slider).mean()

            # 计算布林线
            stock_data['MA20'] = stock_data['收盘'].rolling(window=boll_period_slider).mean()
            stock_data['Bollinger_up'] = stock_data['MA20'] + boll_std_slider * stock_data['收盘'].rolling(window=boll_period_slider).std()
            stock_data['Bollinger_down'] = stock_data['MA20'] - boll_std_slider * stock_data['收盘'].rolling(window=boll_period_slider).std()

            # 选择显示的日期
            dates_to_display = [date_obj, date_obj + timedelta(days=1), date_obj + timedelta(days=2)]

            # 创建展示数据的表格
            ma_boll_data = {
                "日期": [],
                "第一个均线周期": [],
                "第二个均线周期": [],
                "第三个均线周期": [],
                "布林线上轨": [],
                "布林线下轨": []
            }

            for date in dates_to_display:
                if date in stock_data.index:
                    row = stock_data.loc[date]
                    ma_boll_data["日期"].append(date.strftime('%Y-%m-%d'))
                    ma_boll_data["第一个均线周期"].append(row[f"MA{ma_period_1_slider}"] if f"MA{ma_period_1_slider}" in row else None)
                    ma_boll_data["第二个均线周期"].append(row[f"MA{ma_period_2_slider}"] if f"MA{ma_period_2_slider}" in row else None)
                    ma_boll_data["第三个均线周期"].append(row[f"MA{ma_period_3_slider}"] if f"MA{ma_period_3_slider}" in row else None)
                    ma_boll_data["布林线上轨"].append(row['Bollinger_up'] if 'Bollinger_up' in row else None)
                    ma_boll_data["布林线下轨"].append(row['Bollinger_down'] if 'Bollinger_down' in row else None)

            # 转换为DataFrame并展示
            st.table(pd.DataFrame(ma_boll_data))

            # 绘制交互式K线图
            fig = go.Figure()

            # 添加K线数据
            fig.add_trace(go.Candlestick(x=stock_data.index,
                                         open=stock_data['开盘'],
                                         high=stock_data['最高'],
                                         low=stock_data['最低'],
                                         close=stock_data['收盘'],
                                         name='K线',
                                         increasing_line_color='red',
                                         decreasing_line_color='green'))

            # 添加均线数据
            for ma_period in [ma_period_1_slider, ma_period_2_slider, ma_period_3_slider]:
                fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data[f"MA{ma_period}"],
                                         mode='lines', name=f'MA{ma_period}'))

            # 添加布林线数据
            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Bollinger_up'],
                                     mode='lines', name='布林线上轨', line=dict(dash='dot', color='purple')))
            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Bollinger_down'],
                                     mode='lines', name='布林线下轨', line=dict(dash='dot', color='purple')))

            # 提取并标记价格信息
            if isinstance(message_content, str):
                prices = [float(p) for p in message_content.split() if p.replace('.', '', 1).isdigit()]
                for price in prices:
                    fig.add_hline(y=price, line_dash='dash', line_color='blue')

            # 图表布局调整
            fig.update_layout(
                title=f"{symbol} 股票K线图",
                xaxis_title="日期",
                yaxis_title="价格",
                xaxis_rangeslider_visible=False
            )

            # 显示图表
            st.plotly_chart(fig)

    except Exception as e:
        st.write(f"获取股票数据失败：{e}")
else:
    st.write("无数据可展示")

