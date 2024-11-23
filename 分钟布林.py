import streamlit as st
import akshare as ak
import pandas as pd
import plotly.graph_objects as go

# 判断股票代码是否为港股
def is_hk_stock(symbol):
    return len(symbol) == 5 and symbol.isdigit()

# 获取A股数据的函数
def get_a_stock_data(symbol, start_date, end_date, period, adjust):
    df = ak.stock_zh_a_hist_min_em(symbol=symbol, start_date=start_date, end_date=end_date, period=period, adjust=adjust)
    df['时间'] = pd.to_datetime(df['时间'])  # 确保时间列为日期时间格式
    return df.reset_index(drop=True)

# 获取港股数据的函数
def get_hk_stock_data(symbol, start_date, end_date, period, adjust):
    df = ak.stock_hk_hist_min_em(symbol=symbol, start_date=start_date, end_date=end_date, period=period, adjust=adjust)
    df['时间'] = pd.to_datetime(df['时间'])  # 确保时间列为日期时间格式
    return df.reset_index(drop=True)

# 计算布林线
def calculate_bollinger_bands(df, window, std_dev1, std_dev2, std_dev3, ma_type='ma'):
    if ma_type == 'expma':
        df['中轨'] = df['收盘'].ewm(span=window, adjust=False).mean()
    else:
        df['中轨'] = df['收盘'].rolling(window=window).mean()

    for i, std_dev in enumerate([std_dev1, std_dev2, std_dev3], start=1):
        df[f'上轨_{i}'] = df['中轨'] + std_dev * df['收盘'].rolling(window=window).std()
        df[f'下轨_{i}'] = df['中轨'] - std_dev * df['收盘'].rolling(window=window).std()

    return df

# 压缩K线间距的函数
def compress_spacing(df):
    df['标准索引'] = range(len(df))  # 添加标准索引
    return df

# 绘制K线图与布林线
def plot_kline_with_bollinger(df, markers):
    fig = go.Figure()

    # 定义悬停信息
    hover_text = [
        f"时间: {row['时间']}<br>开盘: {row['开盘']}<br>最高: {row['最高']}<br>最低: {row['最低']}<br>收盘: {row['收盘']}"
        for _, row in df.iterrows()
    ]

    # 绘制K线图
    fig.add_trace(go.Candlestick(
        x=df['标准索引'],
        open=df['开盘'],
        high=df['最高'],
        low=df['最低'],
        close=df['收盘'],
        increasing_line_color='red',
        decreasing_line_color='green',
        name="K线图",
        hovertext=hover_text,
        hoverinfo="text"
    ))

    # 绘制布林线
    for i in range(1, 4):
        fig.add_trace(go.Scatter(x=df['标准索引'], y=df[f'上轨_{i}'], line=dict(color='blue', width=1), name=f"上轨_{i}倍标准差"))
        fig.add_trace(go.Scatter(x=df['标准索引'], y=df[f'下轨_{i}'], line=dict(color='blue', width=1), name=f"下轨_{i}倍标准差"))
    fig.add_trace(go.Scatter(x=df['标准索引'], y=df['中轨'], line=dict(color='orange', width=1), name="中轨"))

    # 添加匹配标记
    for marker in markers:
        fig.add_trace(go.Scatter(
            x=[marker['标准索引']],
            y=[marker['值']],
            mode='markers',
            marker=dict(symbol=marker['符号'], size=8, line=dict(width=1, color=marker['颜色']), opacity=0.7),
            name=marker['名称']
        ))

    fig.update_layout(
        title="K线图与布林线",
        xaxis_title="索引",
        yaxis_title="价格",
        hovermode="x unified",
        template="plotly_dark"
    )

    return fig

# 统计布林线匹配次数并生成标记
def count_and_mark_bollinger_hits(df, tolerance):
    counts = {'上下轨_1': 0, '上下轨_2': 0, '上下轨_3': 0, '中轨': 0}
    markers = []

    for idx, row in df.iterrows():
        for i in range(1, 4):
            upper_band = row[f'上轨_{i}']
            lower_band = row[f'下轨_{i}']
            # 检查高点与上轨匹配
            if abs(row['最高'] - upper_band) <= upper_band * tolerance:
                counts[f'上下轨_{i}'] += 1
                markers.append({'标准索引': row['标准索引'], '值': upper_band, '符号': 'triangle-down-open', '颜色': 'red', '名称': f'上轨_{i}'})
            # 检查低点与下轨匹配
            if abs(row['最低'] - lower_band) <= lower_band * tolerance:
                counts[f'上下轨_{i}'] += 1
                markers.append({'标准索引': row['标准索引'], '值': lower_band, '符号': 'triangle-up-open', '颜色': 'green', '名称': f'下轨_{i}'})
        # 检查中轨匹配
        if abs(row['最高'] - row['中轨']) <= row['中轨'] * tolerance or abs(row['最低'] - row['中轨']) <= row['中轨'] * tolerance:
            counts['中轨'] += 1
            markers.append({'标准索引': row['标准索引'], '值': row['中轨'], '符号': 'circle-open', '颜色': 'orange', '名称': '中轨'})

    total_hits = sum(counts.values())
    return counts, markers, total_hits

# Streamlit 应用
st.title("股票K线图与布林线（A股与港股支持）")

# 输入参数
symbol = st.text_input('请输入股票代码', '300033')
start_date = st.text_input("选择开始日期 (格式: YYYY-MM-DD HH:MM:SS)", "2024-03-01 09:30:00")
end_date = st.text_input("选择结束日期 (格式: YYYY-MM-DD HH:MM:SS)", "2024-03-20 15:00:00")
period = st.selectbox("选择时间周期", ['1', '5', '15', '30', '60'])
adjust = st.selectbox("选择复权类型", ['', 'qfq', 'hfq'])

# 判断股票类型并获取数据
if is_hk_stock(symbol):
    st.write("识别为港股代码，正在获取港股数据...")
    df = get_hk_stock_data(symbol, start_date, end_date, period, adjust)
else:
    st.write("识别为A股代码，正在获取A股数据...")
    df = get_a_stock_data(symbol, start_date, end_date, period, adjust)

# 布林线设置
window = st.slider('选择布林线窗口大小', min_value=3, max_value=120, value=20)
std_dev1 = st.slider('选择第1标准差倍数', min_value=0.0, max_value=5.0, value=2.0)
std_dev2 = st.slider('选择第2标准差倍数', min_value=0.0, max_value=5.0, value=2.5)
std_dev3 = st.slider('选择第3标准差倍数', min_value=0.0, max_value=5.0, value=3.0)
ma_type = st.radio("选择中轨类型", ['ma', 'expma'])
tolerance = st.slider('设置偏差比例 (%)', 0.0, 5.0, 0.5) / 100

# 计算布林线
df = calculate_bollinger_bands(df, window, std_dev1, std_dev2, std_dev3, ma_type)
df = compress_spacing(df)

# 统计匹配并生成标记
counts, markers, total_hits = count_and_mark_bollinger_hits(df, tolerance)

# 绘制K线图与布林线
st.plotly_chart(plot_kline_with_bollinger(df, markers))

# 显示统计结果
st.write("布林线匹配统计结果：")
total_k_lines = len(df)
for key, count in counts.items():
    st.write(f"{key} 匹配次数: {count}")
st.write(f"总匹配次数: {total_hits}")

# 按钮1：寻找最佳窗口大小
if st.button('寻找最佳窗口大小'):
    best_window = None
    max_matches = 0
    for w in range(3, 121):
        temp_df = calculate_bollinger_bands(df, w, std_dev1, std_dev2, std_dev3, ma_type)
        temp_counts, _, _ = count_and_mark_bollinger_hits(temp_df, tolerance)
        if temp_counts['中轨'] > max_matches:
            max_matches = temp_counts['中轨']
            best_window = w
    st.write(f"最佳窗口大小: {best_window}, 中轨匹配次数: {max_matches}")

# 按钮2：寻找最佳标准差
if st.button('寻找最佳单一标准差'):
    results = []
    for s in [x * 0.1 for x in range(0, 51)]:
        temp_df = calculate_bollinger_bands(df, window, s, std_dev2, std_dev3, ma_type)
        _, _, total_hits = count_and_mark_bollinger_hits(temp_df, tolerance)
        results.append((s, total_hits))
    top_5 = sorted(results, key=lambda x: x[1], reverse=True)[:5]
    st.write("最佳标准差参数及匹配次数：")
    for param, hits in top_5:
        st.write(f"标准差: {param:.1f}, 匹配次数: {hits}")

