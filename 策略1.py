import streamlit as st
import akshare as ak
import pandas as pd

# 获取A股数据的函数
def get_a_stock_data(symbol, start_date, end_date, period, adjust):
    df = ak.stock_zh_a_hist_min_em(symbol=symbol, start_date=start_date, end_date=end_date, period=period, adjust=adjust)
    df['时间'] = pd.to_datetime(df['时间'])  # 确保时间列为日期时间格式
    return df.reset_index(drop=True)

# 挂单生成函数
def generate_hangdan_table(mid_price, step_percentage, max_deviation, total_funds, trade_unit):
    lower_bound = mid_price * (1 - max_deviation / 100)
    upper_bound = mid_price * (1 + max_deviation / 100)
    step_ratio = step_percentage / 100
    levels = [round(mid_price * (1 + step_ratio * i), 2) for i in range(-int(max_deviation / step_percentage), int(max_deviation / step_percentage) + 1)]
    if mid_price not in levels:
        levels.append(mid_price)
    levels.sort()
    if len(levels) % 2 != 0:
        levels.pop()
    total_shares = total_funds // mid_price // trade_unit * trade_unit
    half_shares = total_shares // 2
    fibonacci = [1, 2]
    while len(fibonacci) < len(levels) // 2:
        fibonacci.append(fibonacci[-1] + fibonacci[-2])
    buy_orders = adjust_fibonacci_to_scale(fibonacci[::-1], half_shares, adjust_for="buy")
    sell_orders = adjust_fibonacci_to_scale(fibonacci, half_shares, adjust_for="sell")
    buy_orders += [0] * (len(levels) - len(buy_orders))
    sell_orders = [0] * (len(levels) - len(sell_orders)) + sell_orders
    table = pd.DataFrame({
        "档位价格": levels,
        "第一天买单数量": buy_orders,
        "第一天卖单数量": sell_orders,
    }).sort_values(by="档位价格", ascending=False).reset_index(drop=True)
    return table

# 调整斐波那契数列
def adjust_fibonacci_to_scale(fibonacci, total_shares, adjust_for="buy"):
    fibonacci_sum = sum(fibonacci)
    scale_factor = total_shares / fibonacci_sum
    scaled_fibonacci = [max(round(x * scale_factor), 0) for x in fibonacci]
    diff = total_shares - sum(scaled_fibonacci)
    if adjust_for == "buy":
        scaled_fibonacci[-1] += diff
    elif adjust_for == "sell":
        scaled_fibonacci[0] += diff
    return scaled_fibonacci

# 根据开盘价标注成交
def mark_transactions_by_open_price(df, table, mid_price):
    """
    标注成交区域（仅根据开盘价，不更改表格数据）。
    """
    # 获取第一个时间周期的开盘价
    open_price = df.iloc[0]["开盘"]

    # 标注成交区域
    updated_table = table.copy()
    updated_table["成交备注"] = None
    if open_price >= mid_price:
        affected_rows = updated_table[(updated_table["档位价格"] >= mid_price) & (updated_table["档位价格"] <= open_price)].index
    else:
        affected_rows = updated_table[(updated_table["档位价格"] < mid_price) & (updated_table["档位价格"] >= open_price)].index

    for index in affected_rows:
        updated_table.at[index, "成交备注"] = "成交"

    return updated_table

# 根据成交量重新生成挂单表格
def regenerate_hangdan_table_v8(table, mid_price, transaction_volume, open_price):
    """
    根据成交量重新生成挂单表格。
    修复多余单问题，并确保按照新中枢原则分布挂单。
    """
    new_table = table.copy()

    if open_price is None or pd.isna(open_price):  # 如果开盘价为空，返回原始表格
        return new_table

    # 1. 确定成交区域
    if open_price >= mid_price:
        # 成交区域为中枢到开盘价之间
        affected_rows = new_table[(new_table["档位价格"] >= mid_price) & (new_table["档位价格"] <= open_price)].index
        affected_prices = new_table.loc[affected_rows, "档位价格"].sort_values(ascending=False)
        if len(affected_prices) > 1:
            new_mid_price = affected_prices.iloc[1]  # 第二高档位作为新中枢
        else:
            new_mid_price = affected_prices.iloc[0]  # 如果只有一个成交档位
    else:
        # 成交区域为开盘价到中枢之间
        affected_rows = new_table[(new_table["档位价格"] < mid_price) & (new_table["档位价格"] >= open_price)].index
        affected_prices = new_table.loc[affected_rows, "档位价格"].sort_values(ascending=True)
        if len(affected_prices) > 1:
            new_mid_price = affected_prices.iloc[0]  # 最低档位作为新中枢
        else:
            new_mid_price = affected_prices.iloc[0]  # 如果只有一个成交档位

    # 显示新中枢和改动档位区间
    st.write(f"新的中枢价格: {new_mid_price}")
    st.write(f"需要改动的档位区间数量: {len(affected_rows)}")

    # 判断成交区域是买单还是卖单
    if open_price >= mid_price:
        # 第二步成交了卖单
        transaction_type = "sell_to_buy"
    else:
        # 第二步成交了买单
        transaction_type = "buy_to_sell"

    # 2. 清空成交区域的所有买卖单
    transaction_volume = new_table.loc[affected_rows, f"第一天{'卖' if transaction_type == 'sell_to_buy' else '买'}单数量"].sum()

    for idx in affected_rows:
        new_table.at[idx, "第一天买单数量"] = 0
        new_table.at[idx, "第一天卖单数量"] = 0

    # 3. 将成交的总量进行买卖单转换，并重新分布
    if transaction_type == "sell_to_buy":
        # 卖单转化为买单
        fibonacci = [1, 2]
        while len(fibonacci) < len(affected_rows) - 1:  # 长度为 len - 1
            fibonacci.append(fibonacci[-1] + fibonacci[-2])
        buy_fibonacci = adjust_fibonacci_to_scale(fibonacci, transaction_volume, "buy")

        # 分布买单到成交区域中小于等于新中枢的档位
        lower_rows = new_table[(new_table["档位价格"] <= new_mid_price) & (new_table.index.isin(affected_rows))].index
        for idx, vol in zip(lower_rows, buy_fibonacci):
            new_table.at[idx, "第一天买单数量"] = vol

    elif transaction_type == "buy_to_sell":
        # 买单转化为卖单
        fibonacci = [1, 2]
        while len(fibonacci) < len(affected_rows) - 1:  # 长度为 len - 1
            fibonacci.append(fibonacci[-1] + fibonacci[-2])
        sell_fibonacci = adjust_fibonacci_to_scale(fibonacci[::-1], transaction_volume, "sell")  # 倒序分布

        # 分布卖单到成交区域中大于新中枢的档位
        upper_rows = new_table[(new_table["档位价格"] > new_mid_price) & (new_table.index.isin(affected_rows))].index
        for idx, vol in zip(upper_rows, sell_fibonacci):
            new_table.at[idx, "第一天卖单数量"] = vol

    return new_table

# Streamlit 应用
st.title("股票分钟布林线与挂单生成器（按开盘价重新挂单）")

# 获取股票数据
symbol = st.text_input('请输入股票代码', '600036')
start_date = st.text_input("选择开始日期 (格式: YYYY-MM-DD HH:MM:SS)", "2024-12-01 09:30:00")
end_date = st.text_input("选择结束日期 (格式: YYYY-MM-DD HH:MM:SS)", "2024-12-31 15:00:00")
period = st.selectbox("选择时间周期", ['1', '5', '15', '30', '60'], index=2)  # 默认选择15分钟
adjust = st.selectbox("选择复权类型", ['', 'qfq', 'hfq'], index=1)  # 默认选择qfq

# 获取股票数据
df = get_a_stock_data(symbol, start_date, end_date, period, adjust)
st.write("K线数据：")
st.dataframe(df)

# 挂单生成参数
mid_price = st.number_input("请输入中枢价格：", min_value=0.01, value=36.50, step=0.01)
step_percentage = st.number_input("请输入档位极差（%）：", min_value=0.01, max_value=10.0, value=1.97, step=0.01)
max_deviation = st.number_input("请输入最大偏差范围（%）：", min_value=0.01, max_value=50.0, value=10.00, step=0.01)
total_funds = st.number_input("请输入总资金（元）：", min_value=1000, value=1000000, step=1000)
trade_unit = st.number_input("请输入交易单位（股）：", min_value=1, value=100, step=1)

# 生成挂单表格
table = generate_hangdan_table(mid_price, step_percentage, max_deviation, total_funds, trade_unit)
st.write("1. 原始挂单表格：")
st.dataframe(table)

# 标注成交
updated_table = mark_transactions_by_open_price(df, table, mid_price)
st.write("2. 标注成交后的表格（仅标注，无数据改动）：")
st.dataframe(updated_table)

# 根据成交量重新生成挂单表格
new_table = regenerate_hangdan_table_v8(updated_table, mid_price, None, df.iloc[0]["开盘"])
st.write("3. 重新生成挂单表格（仅对成交区域调整）：")
st.dataframe(new_table)

# 新功能：获取第一个时间周期的高低点，并计算新的成交区间
if len(df) > 0:
    first_period = df.iloc[0]  # 获取第一个周期的数据
    highest_price = first_period['最高']
    lowest_price = first_period['最低']
    transaction_range = (lowest_price + 0.01, highest_price - 0.01)  # 新的成交区间
    mid_price = first_period['收盘']
    st.write(f"新的成交区间：{transaction_range[0]} - {transaction_range[1]}")
    st.write(f"新的中枢价格：{mid_price}")
else:
    st.write("未能获取有效数据")

# 4. 第一次盘中成交：直接基于表格调整成交备注
final_table = new_table.copy()  # 复制表格
final_table["成交备注"] = None  # 清空成交备注

# 更新成交备注，位于成交区间内的档位
final_table["成交备注"] = final_table.apply(
    lambda row: "成交" if transaction_range[0] <= row["档位价格"] <= transaction_range[1] else row["成交备注"],
    axis=1
)

st.write("5. 第一次盘中成交：")
st.dataframe(final_table)

adjusted_table = final_table.copy()

# 遍历每一行，检查成交备注，并进行买卖单转换
for index, row in adjusted_table.iterrows():
    if row["成交备注"] == "成交":  # 只处理成交备注为"成交"的档位
        if row["第一天卖单数量"] > 0:  # 如果卖单数量大于0
            adjusted_table.at[index, "第一天买单数量"] = row["第一天卖单数量"]  # 将卖单数量移到买单
            adjusted_table.at[index, "第一天卖单数量"] = 0  # 清空卖单数量
        elif row["第一天买单数量"] > 0:  # 如果买单数量大于0
            adjusted_table.at[index, "第一天卖单数量"] = row["第一天买单数量"]  # 将买单数量移到卖单
            adjusted_table.at[index, "第一天买单数量"] = 0  # 清空买单数量

st.write("6. 调整买卖单后表格：")
st.dataframe(adjusted_table)

# 1. 将旧代码的成交区间和新功能的成交区间求出一个并集，作为第一循环区间
# 获取新功能中的成交区间
if len(df) > 0:
    first_period = df.iloc[0]  # 获取第一个周期的数据
    highest_price = first_period['最高']
    lowest_price = first_period['最低']
    transaction_range = (round(lowest_price + 0.01, 2), round(highest_price - 0.01, 2))  # 新的成交区间，四舍五入至两位小数
    mid_price = first_period['收盘']
    st.write(f"新的成交区间：{transaction_range[0]} - {transaction_range[1]}")

# 获取旧代码中的成交区间，基于新计算的 mid_price 作为中枢价格
open_price = df.iloc[0]['开盘']  # 获取开盘价
old_transaction_range = (round(open_price, 2), round(mid_price, 2))  # 旧成交区间：open_price 和 mid_price之间

# 计算并集作为第一循环区间
first_cycle_range = (
    min(transaction_range[0], old_transaction_range[0]), 
    max(transaction_range[1], old_transaction_range[1])
)
first_cycle_range = (round(first_cycle_range[0], 2), round(first_cycle_range[1], 2))  # 四舍五入至两位小数
st.write(f"第一循环区间：{first_cycle_range[0]} - {first_cycle_range[1]}")

# 2. 计算adjusted_table在第一循环区间内的买单和卖单的总和
buy_total = adjusted_table[(adjusted_table["档位价格"] >= first_cycle_range[0]) & 
                           (adjusted_table["档位价格"] <= first_cycle_range[1])]["第一天买单数量"].sum()
sell_total = adjusted_table[(adjusted_table["档位价格"] >= first_cycle_range[0]) & 
                            (adjusted_table["档位价格"] <= first_cycle_range[1])]["第一天卖单数量"].sum()

st.write(f"第一循环区间内的买单总和：{buy_total}")
st.write(f"第一循环区间内的卖单总和：{sell_total}")

# 3. 读取前面获取的K线信息的第一周期的行，找到第一时间周期的收盘价，定义为第一循环中枢
first_period = df.iloc[0]  # 获取第一时间周期的行
first_cycle_mid_price = first_period['收盘']  # 取收盘价作为中枢
st.write(f"第一循环中枢价格：{first_cycle_mid_price}")

# 4. 将卖单在第一循环区间内大于第一循环中枢的档位中按照斐波那契数列比例的原则重新分布
sell_rows = adjusted_table[(adjusted_table["档位价格"] > first_cycle_mid_price) & 
                           (adjusted_table["档位价格"] >= first_cycle_range[0]) & 
                           (adjusted_table["档位价格"] <= first_cycle_range[1])]
sell_fibonacci = [1, 2]
while len(sell_fibonacci) < len(sell_rows) - 1:
    sell_fibonacci.append(sell_fibonacci[-1] + sell_fibonacci[-2])

# 分配卖单数量到重新分布的档位
sell_fibonacci = adjust_fibonacci_to_scale(sell_fibonacci, sell_total, adjust_for="sell")
sell_rows["第一天卖单数量"] = sell_fibonacci

# 5. 将买单在第一循环区间内大于等于第一循环中枢的档位中按照斐波那契数列比例的原则重新分布
buy_rows = adjusted_table[(adjusted_table["档位价格"] >= first_cycle_mid_price) & 
                          (adjusted_table["档位价格"] >= first_cycle_range[0]) & 
                          (adjusted_table["档位价格"] <= first_cycle_range[1])]
buy_fibonacci = [1, 2]
while len(buy_fibonacci) < len(buy_rows) - 1:
    buy_fibonacci.append(buy_fibonacci[-1] + buy_fibonacci[-2])

# 分配买单数量到重新分布的档位
buy_fibonacci = adjust_fibonacci_to_scale(buy_fibonacci, buy_total, adjust_for="buy")
buy_rows["第一天买单数量"] = buy_fibonacci


# 6. 输出最终表格 "7. 第一循环结果"
# 复制 adjusted_table 来创建一个新的副本
final_table = adjusted_table.copy()

# 更新调整后的表格数据
final_table.loc[sell_rows.index, "第一天卖单数量"] = sell_rows["第一天卖单数量"]
final_table.loc[buy_rows.index, "第一天买单数量"] = buy_rows["第一天买单数量"]

# 输出最终的表格
st.write("7. 第一循环结果：")
st.dataframe(final_table)


