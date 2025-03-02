import streamlit as st
import akshare as ak
import pandas as pd

# 获取A股数据的函数
def get_a_stock_data(symbol, start_date, end_date, period, adjust):
    df = ak.stock_zh_a_hist_min_em(symbol=symbol, start_date=start_date, end_date=end_date, period=period, adjust=adjust)
    df['时间'] = pd.to_datetime(df['时间'])  # 确保时间列为日期时间格式
    return df.reset_index(drop=True)

# 生成数列的函数
def generate_sequence(sequence_type, depth):
    if sequence_type == "斐波那契":
        fibonacci = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
        return fibonacci[:depth]
    elif sequence_type == "等差数列":
        return list(range(1, depth + 1))
    elif sequence_type == "等分数列":
        return [5] * depth
    elif sequence_type == "对数数列":
        return [round(0.69 + 0.2 * i, 2) for i in range(depth)]

# 挂单生成函数
def generate_hangdan_table(mid_price, step_percentage, max_deviation, total_funds, trade_unit, sequence_depth):
    lower_bound = mid_price * (1 - max_deviation / 100)
    upper_bound = mid_price * (1 + max_deviation / 100)
    levels = []
    level = mid_price
    while level >= lower_bound:
        levels.append(round(level, 2))
        level *= (1 - step_percentage / 100)
    level = mid_price
    while level <= upper_bound:
        levels.append(round(level, 2))
        level *= (1 + step_percentage / 100)
    levels = sorted(set(levels))
    if mid_price not in levels:
        levels.append(mid_price)
    levels.sort()
    print("生成的档位：", levels)

    total_sell_units = (total_funds / 2) // mid_price // trade_unit * trade_unit
    fibonacci_sell = generate_sequence(sequence_type_sell, sequence_depth)
    print(f"卖单斐波那契数列（深度{sequence_depth}）: {fibonacci_sell}")
    sell_orders = []
    sell_start_idx = len([level for level in levels if level <= mid_price])  # 卖单数列起始索引
    for i in range(len([level for level in levels if level > mid_price]) - 1):
        sell_orders.append(fibonacci_sell[i % len(fibonacci_sell)])
    print("卖单数列分配：", sell_orders)

    total_sell_sum = sum(sell_orders) * 100
    scale_factor_sell = total_sell_units / total_sell_sum
    sell_orders = [max(1, round(order * scale_factor_sell)) for order in sell_orders]
    print(f"调整后的卖单数列：{sell_orders}")
    sell_orders = [order * trade_unit for order in sell_orders]
    print(f"乘以100后的卖单数列：{sell_orders}")
    total_sell_after_adjustment = sum(sell_orders)
    if total_sell_after_adjustment != total_sell_units:
        difference = total_sell_units - total_sell_after_adjustment
        sell_orders[sell_orders.index(max(sell_orders))] += difference
        print(f"微调后的卖单数列：{sell_orders}")

    fibonacci_buy = generate_sequence(sequence_type_buy, sequence_depth)
    print(f"买单斐波那契数列（深度{sequence_depth}）: {fibonacci_buy}")
    buy_orders = []
    buy_start_idx = 0  # 买单数列起始索引（最低价）
    for i in range(len([level for level in levels if level < mid_price])):
        buy_orders.append(fibonacci_buy[i % len(fibonacci_buy)])
    print("买单数列分配：", buy_orders)

    buy_order_values = [buy_orders[i] * levels[i] * trade_unit for i in range(len(buy_orders))]
    total_buy_amount = sum(buy_order_values)
    print(f"买单金额总和：{total_buy_amount}")
    remaining_funds = total_funds - sum(sell_orders) * mid_price
    scale_factor_buy = remaining_funds / total_buy_amount
    buy_orders = [max(1, round(order * scale_factor_buy)) for order in buy_orders]
    print(f"调整后的买单数列（缩放前）：{buy_orders}")
    total_buy_after_adjustment = sum(buy_orders) / 100
    if total_buy_after_adjustment != sum(buy_orders) / 100:
        difference = sum(buy_orders) / 100 - total_buy_after_adjustment
        buy_orders[buy_orders.index(max(buy_orders))] += difference
        print(f"微调后的买单数列：{buy_orders}")
    buy_orders = [order * trade_unit for order in buy_orders]
    print(f"乘以100后的买单数列：{buy_orders}")

    if len(buy_orders) != len(levels) or len(sell_orders) != len(levels):
        max_len = max(len(buy_orders), len(sell_orders), len(levels))
        sell_orders = sell_orders[::-1] + [0] * (max_len - len(sell_orders))
        buy_orders = [0] * (max_len - len(buy_orders)) + buy_orders

        
    print("买单最终数量：", buy_orders)
    print("卖单最终数量：", sell_orders)
    buy_orders = buy_orders[::-1]
    sell_orders = sell_orders[::-1]
    print("倒序后的买单数量：", buy_orders)
    print("倒序后的卖单数量：", sell_orders)

    table = pd.DataFrame({
        "档位价格": levels,
        "原始买单": buy_orders,
        "原始卖单": sell_orders,
    }).sort_values(by="档位价格", ascending=False).reset_index(drop=True)

    market_value = sum(sell_orders) * df.iloc[0]["开盘"]
    total_assets = market_value + total_buy_amount
    table.at["总卖出", "原始卖单"] = sum(sell_orders)
    table.at["总买入", "原始买单"] = sum(buy_orders)
    table.at["总单数", "原始卖单"] = sum(sell_orders) + sum(buy_orders)
    table.at["总单数", "原始买单"] = sum(sell_orders) + sum(buy_orders)
    table.at["总市值", "原始卖单"] = sum(sell_orders) * mid_price
    table.at["总市值", "原始买单"] = sum(sell_orders) * mid_price
    buy_order_values2 = [buy_orders[i] * levels[i] * trade_unit for i in range(len(buy_orders))]
    sell_order_values2 = [sell_orders[i] * levels[i] * trade_unit for i in range(len(sell_orders))]
    table.at["挂单资金", "原始买单"] = sum(buy_order_values2) / 100
    table.at["挂单资金", "原始卖单"] = sum(buy_order_values2) / 100
    table.at["总资金", "原始买单"] = total_funds - (total_sell_units * mid_price)
    table.at["总资金", "原始卖单"] = total_funds - (total_sell_units * mid_price)
    table.at["盈余", "原始买单"] = table.at["总资金", "原始买单"] - table.at["挂单资金", "原始买单"]
    table.at["盈余", "原始卖单"] = table.at["总资金", "原始买单"] - table.at["挂单资金", "原始买单"]
    table.at["总资产", "原始卖单"] = table.at["总资金", "原始买单"] + table.at["总市值", "原始卖单"]
    table.at["总资产", "原始买单"] = table.at["总资金", "原始买单"] + table.at["总市值", "原始卖单"]

    return table, buy_start_idx, sell_start_idx, buy_orders, sell_orders  # 返回标记索引和原始挂单

# Streamlit 页面部分
st.title("股票分钟布林线与挂单生成器（按开盘价重新挂单）")

symbol = st.text_input('请输入股票代码', '600036')
start_date = st.text_input("选择开始日期 (格式: YYYY-MM-DD HH:MM:SS)", "2025-02-01 09:30:00")
end_date = st.text_input("选择结束日期 (格式: YYYY-MM-DD HH:MM:SS)", "2025-02-20 15:00:00")
period = st.selectbox("选择时间周期", ['1', '5', '15', '30', '60'], index=2)
adjust = st.selectbox("选择复权类型", ['', 'qfq', 'hfq'], index=1)

df = get_a_stock_data(symbol, start_date, end_date, period, adjust)
st.write("K线数据：")
st.dataframe(df)

mid_price = st.number_input("请输入中枢价格：", min_value=0.01, value=38.50, step=0.01)
step_percentage = st.number_input("请输入档位极差（%）：", min_value=0.01, max_value=10.0, value=1.20, step=0.01)
max_deviation = st.number_input("请输入最大偏差范围（%）：", min_value=0.01, max_value=50.0, value=15.00, step=0.01)
total_funds = st.number_input("请输入总资金（元）：", min_value=1000, value=1000000, step=1000)
trade_unit = st.number_input("请输入交易单位（股）：", min_value=1, value=100, step=1)
sequence_type_buy = st.selectbox("选择买单数列类型", ["斐波那契", "等差数列", "等分数列", "对数数列"])
sequence_type_sell = st.selectbox("选择卖单数列类型", ["斐波那契", "等差数列", "等分数列", "对数数列"])
sequence_depth = st.slider("选择数列深度", min_value=1, max_value=15, value=5)

table, buy_start_idx, sell_start_idx, original_buy_orders, original_sell_orders  = generate_hangdan_table(mid_price, step_percentage, max_deviation, total_funds, trade_unit, sequence_depth)
st.write("1. 原始挂单表格：")
st.dataframe(table)

open_price = df.iloc[0]['开盘']
close_price = df.iloc[0]['收盘']
period_time = df.iloc[0]['时间'].strftime("%H:%M")

new_buy = table['原始买单'].iloc[:-8].copy().tolist()
new_sell = table['原始卖单'].iloc[:-8].copy().tolist()
levels = table['档位价格'].tolist()

sell_indices = [i for i, price in enumerate(levels) if price > mid_price]
buy_indices = [i for i, price in enumerate(levels) if price <= mid_price]
sum_buy = 0
sum_sell = 0

if open_price > mid_price:
    moved_indices = [i for i in sell_indices if levels[i] < open_price]
    moved_qty = [(i, new_sell[i]) for i in moved_indices]
    for i in moved_indices:
        new_sell[i] = 0
    sum_sell = sum(qty * levels[i] for i, qty in moved_qty)
    moved_qty = [(idx, qty) for idx, qty in zip([idx for idx, _ in moved_qty], [qty for _, qty in moved_qty[::-1]])]
    for idx, (original_idx, qty) in enumerate(moved_qty):
        target_idx = original_idx + 1
        target_global_idx = target_idx
        if target_global_idx < len(new_buy):
            new_buy[target_global_idx] += qty
        else:
            print(f"警告：目标索引 {target_global_idx} 超出 new_buy 范围")
else:
    moved_indices = [i for i in buy_indices if levels[i] > open_price]
    moved_qty = [(i, new_buy[i]) for i in moved_indices]
    for i in moved_indices:
        new_buy[i] = 0
    sum_buy = sum(qty * levels[i] for i, qty in moved_qty)
    moved_qty = [(idx, qty) for idx, qty in zip([idx for idx, _ in moved_qty], [qty for _, qty in moved_qty[::-1]])]
    for idx, (original_idx, qty) in enumerate(moved_qty):
        target_idx = original_idx - 1
        target_global_idx = target_idx
        if target_global_idx < len(new_sell):
            new_sell[target_global_idx] += qty
        else:
            print(f"警告：目标索引 {target_global_idx} 超出 new_sell 范围")

extended_new_buy = new_buy + [0] * (len(table) - len(new_buy))
extended_new_sell = new_sell + [0] * (len(table) - len(new_sell))

table[f"{period_time}买单"] = extended_new_buy
table[f"{period_time}卖单"] = extended_new_sell

table.at['总卖出', f"{period_time}卖单"] = 0
table.at['总卖出', f"{period_time}买单"] = 0
table.at['总买入', f"{period_time}买单"] = 0
table.at['总买入', f"{period_time}卖单"] = 0
table.at['总单数', f"{period_time}卖单"] = 0
table.at['总单数', f"{period_time}买单"] = 0
table.at['总市值', f"{period_time}卖单"] = 0
table.at['总市值', f"{period_time}买单"] = 0
table.at['挂单资金', f"{period_time}买单"] = 0
table.at['挂单资金', f"{period_time}卖单"] = 0
table.at['总资金', f"{period_time}买单"] = 0
table.at['总资金', f"{period_time}卖单"] = 0
table.at['盈余', f"{period_time}买单"] = 0
table.at['盈余', f"{period_time}卖单"] = 0
table.at['总资产', f"{period_time}买单"] = 0
table.at['总资产', f"{period_time}卖单"] = 0

total_sell_new = sum(new_sell)
total_buy_new = sum(new_buy)
table.at['总卖出', f"{period_time}卖单"] = total_sell_new
table.at['总卖出', f"{period_time}买单"] = total_sell_new
table.at['总买入', f"{period_time}买单"] = total_buy_new
table.at['总买入', f"{period_time}卖单"] = total_buy_new
table.at['总单数', f"{period_time}卖单"] = total_sell_new + total_buy_new
table.at['总单数', f"{period_time}买单"] = total_sell_new + total_buy_new
table.at['总市值', f"{period_time}卖单"] = total_sell_new * close_price
table.at['总市值', f"{period_time}买单"] = total_sell_new * close_price
table.at['挂单资金', f"{period_time}买单"] = sum([qty * price for qty, price in zip(new_buy, levels)])
table.at['挂单资金', f"{period_time}卖单"] = sum([qty * price for qty, price in zip(new_buy, levels)])
original_capital = table.at["总资金", "原始买单"]
table.at['总资金', f"{period_time}买单"] = original_capital + sum_sell - sum_buy
table.at['总资金', f"{period_time}卖单"] = original_capital + sum_sell - sum_buy
table.at['盈余', f"{period_time}买单"] = table.at['总资金', f"{period_time}买单"] - table.at['挂单资金', f"{period_time}买单"]
table.at['盈余', f"{period_time}卖单"] = table.at['总资金', f"{period_time}买单"] - table.at['挂单资金', f"{period_time}买单"]
table.at['总资产', f"{period_time}卖单"] = table.at['总资金', f"{period_time}买单"] + table.at['总市值', f"{period_time}卖单"]
table.at['总资产', f"{period_time}买单"] = table.at['总资金', f"{period_time}买单"] + table.at['总市值', f"{period_time}卖单"]

st.write("2. 调整后的挂单表格：")
st.dataframe(table)

# 修改后的成交区间计算函数
def find_traded_range(original_buy, original_sell, new_buy, new_sell, levels):
    """找出发生变化的档位并生成成交区间"""
    changed_buy_indices = [i for i in range(len(levels)-8) if original_buy[i] != new_buy[i]]
    changed_sell_indices = [i for i in range(len(levels)-8) if original_sell[i] != new_sell[i]]

    # 买单变化的最低档位（索引最大，因为 levels 是价格降序排列）
    if changed_buy_indices:
        buy_min_idx = max(changed_buy_indices)  # 有变化时，取最大索引（最低价格）
    else:
        # 没有成交买单时，取 new_buy 中值为 0 的档位中价格最低的索引（最大索引）
        zero_buy_indices = [i for i in range(len(new_buy)) if new_buy[i] == 0]
        buy_min_idx = max(zero_buy_indices) if zero_buy_indices else -1  # 如果没有零值买单，仍返回 -1

    # 卖单变化的最高档位（索引最小，因为 levels 是价格降序排列）
    if changed_sell_indices:
        sell_max_idx = min(changed_sell_indices)  # 有变化时，取最小索引（最高价格）
    else:
        # 没有成交卖单时，取 new_sell 中值为 0 的档位中价格最高的索引（最小索引）
        zero_sell_indices = [i for i in range(len(new_sell)) if new_sell[i] == 0]
        sell_max_idx = min(zero_sell_indices) if zero_sell_indices else len(levels)  # 如果没有零值卖单，仍返回 len(levels)

    # 确定成交区间边界
    if not changed_buy_indices and not changed_sell_indices:
        return [], []  # 无变化

    # 生成实际成交区间（包含所有中间档位）
    if buy_min_idx != -1 and sell_max_idx != len(levels):
        start_idx = min(buy_min_idx, sell_max_idx)
        end_idx = max(buy_min_idx, sell_max_idx)
        traded_indices = list(range(start_idx, end_idx + 1))
    elif buy_min_idx != -1:
        traded_indices = [buy_min_idx] if buy_min_idx in zero_buy_indices else changed_buy_indices
    else:
        traded_indices = [sell_max_idx] if sell_max_idx in zero_sell_indices else changed_sell_indices

    traded_levels = [(i, levels[i]) for i in traded_indices]
    traded_indices_only = [i for i in traded_indices]
    
    return traded_levels, traded_indices_only

original_buy = table['原始买单'].tolist()[:-8]
original_sell = table['原始卖单'].tolist()[:-8]
new_buy = table[f"{period_time}买单"].tolist()[:-8]
new_sell = table[f"{period_time}卖单"].tolist()[:-8]

traded_range, traded_range_indices = find_traded_range(original_buy, original_sell, new_buy, new_sell, levels[:-6])
if traded_range:
    traded_indices_str = ", ".join([f"({idx},{price})" for idx, price in traded_range])
    traded_indices_only_str = ", ".join([str(idx) for idx in traded_range_indices])
else:
    traded_indices_str = "无成交"
    traded_indices_only_str = "无成交"
print(traded_indices_str)
print(traded_indices_only_str)



# 进一步调整挂单
updated_sell = new_sell.copy()
updated_buy = new_buy.copy()
high_price = df.iloc[0]['最高'] - 0.01
low_price = df.iloc[0]['最低'] + 0.01
period_time = df.iloc[0]['时间'].strftime("%m/%d %H:%M")

traded_sell = []
total_sell_volume = 0
sell_amount = 0
for i, price in enumerate(levels[:-8]):
    if price <= high_price and updated_sell[i] > 0:
        traded_sell.append((i, price, updated_sell[i]))
        total_sell_volume += updated_sell[i]
        sell_amount += updated_sell[i] * price
print(f"成交卖单: {traded_sell}")
print(f"总卖单数量: {total_sell_volume}")
print(f"卖出金额: {sell_amount}")

traded_buy = []
total_buy_volume = 0
buy_amount = 0
for i, price in enumerate(levels[:-8]):
    if price >= low_price and updated_buy[i] > 0:
        traded_buy.append((i, price, updated_buy[i]))
        total_buy_volume += updated_buy[i]
        buy_amount += updated_buy[i] * price
print(f"成交买单: {traded_buy}")
print(f"总买单数量: {total_buy_volume}")
print(f"买入金额: {buy_amount}")

# 计算 high_idx
price_high_idx = min([i for i, price in enumerate(levels[:-8]) if price <= high_price], default=0)
zero_sell_indices = [i for i in range(len(new_sell)) if new_sell[i] == 0]
sell_zero_high_idx = min(zero_sell_indices) if zero_sell_indices else len(new_sell) - 1
high_idx = min(price_high_idx, sell_zero_high_idx)
print(f"价格小于等于 high_price 的最低索引: {price_high_idx}")
print(f"卖单值为零的最大价格索引: {sell_zero_high_idx}")
print(f"最终 high_idx: {high_idx}")

# 计算 low_idx
price_low_idx = max([i for i, price in enumerate(levels[:-8]) if price >= low_price], default=len(levels[:-8])-1)
zero_buy_indices = [i for i in range(len(new_buy)) if new_buy[i] == 0]
buy_zero_low_idx = max(zero_buy_indices) if zero_buy_indices else 0
low_idx = max(price_low_idx, buy_zero_low_idx)
print(f"价格大于等于 low_price 的最高索引: {price_low_idx}")
print(f"买单值为零的最小价格索引: {buy_zero_low_idx}")
print(f"最终 low_idx: {low_idx}")

# 生成本轮成交区间
round_traded_indices = list(range(high_idx, low_idx + 1))
print(f"本轮成交区间位置: {round_traded_indices}")

# 初始化 total_traded_indices
total_traded_indices = traded_range_indices.copy()
print(f"初始 total_traded_indices: {total_traded_indices}")
total_traded_indices = sorted(set(round_traded_indices + total_traded_indices))
print(f"总成交区间位置: {total_traded_indices}")

# 提取本轮成交区间内所有买单数量（包括 0），生成元组
convert_to_sell = [(i, updated_buy[i]) for i in round_traded_indices]
print(f"转化卖单（原始）: {convert_to_sell}")

# 清零本轮成交区间内的买单
for i in round_traded_indices:
    updated_buy[i] = 0

# 提取本轮成交区间内所有卖单数量（包括 0），生成元组
convert_to_buy = [(i, updated_sell[i]) for i in round_traded_indices]
print(f"转化买单（原始）: {convert_to_buy}")

# 清零本轮成交区间内的卖单
for i in round_traded_indices:
    updated_sell[i] = 0

# 提取数量并倒序
convert_to_sell_values = [qty for _, qty in convert_to_sell][::-1]
# 将倒序数量与原始索引重新配对
convert_to_sell = [(idx, qty) for (idx, _), qty in zip(convert_to_sell, convert_to_sell_values)]

# 提取数量并倒序
convert_to_buy_values = [qty for _, qty in convert_to_buy][::-1]
# 将倒序数量与原始索引重新配对
convert_to_buy = [(idx, qty) for (idx, _), qty in zip(convert_to_buy, convert_to_buy_values)]

print(f"倒序后的转化卖单: {convert_to_sell}")
print(f"倒序后的转化买单: {convert_to_buy}")

# 将转化卖单加到 updated_sell
for idx, qty in convert_to_sell:
    updated_sell[idx] += qty

# 将转化买单加到 updated_buy
for idx, qty in convert_to_buy:
    updated_buy[idx] += qty

# 计算卖单中值为零的最大价格档位索引（最小索引）
zero_sell_indices = [i for i in range(len(updated_sell)) if updated_sell[i] == 0]
first_sell_idx = min(zero_sell_indices) if zero_sell_indices else len(updated_sell) - 1

# 计算买单中值为零的最小价格档位索引（最大索引）
zero_buy_indices = [i for i in range(len(updated_buy)) if updated_buy[i] == 0]
first_buy_idx = max(zero_buy_indices) if zero_buy_indices else 0 + 1

ideal_open_range = (first_sell_idx - 1, first_buy_idx + 1)
print(f"理想开盘区间索引: {ideal_open_range}")
has_two_levels = abs(first_buy_idx - first_sell_idx) >= 1
print(f"理想开盘区间是否有两个档位: {has_two_levels}")
print(updated_buy)
print(updated_sell)

next_open_price = df.iloc[1]['开盘'] if len(df) > 1 else None
if next_open_price:
    ideal_open_prices = (levels[ideal_open_range[0]], levels[ideal_open_range[1]])
    is_in_ideal_range = ideal_open_prices[1] <= next_open_price <= ideal_open_prices[0]  # 修复顺序
    print(f"下一日开盘价 {next_open_price} 是否在理想开盘区间 {ideal_open_prices}: {is_in_ideal_range}")

    if is_in_ideal_range:
        # 计算总成交区间的总量
        total_sell_in_traded = sum(updated_sell[i] for i in total_traded_indices)
        total_buy_in_traded = sum(updated_buy[i] for i in total_traded_indices)
        print(f"总成交区间内的卖单总量: {total_sell_in_traded}")
        print(f"总成交区间内的买单总量: {total_buy_in_traded}")

        # 清零总成交区间内的挂单
        for i in total_traded_indices:
            updated_sell[i] = 0
            updated_buy[i] = 0
        print(f"清零后卖单: {updated_sell}")
        print(f"清零后买单: {updated_buy}")

        # 卖单分配区间：total_traded_indices 内小于 first_sell_idx 的档位
        sell_dist_range = [i for i in total_traded_indices if i < first_sell_idx]
        if sell_dist_range:
            sell_sequence = generate_sequence(sequence_type_sell, len(sell_dist_range))[::-1]  # 倒序
            scale_factor = total_sell_in_traded / sum(sell_sequence) if sum(sell_sequence) > 0 else 0
            sell_dist = [max(trade_unit, round(x * scale_factor // trade_unit) * trade_unit) for x in sell_sequence]
            if sum(sell_dist) != total_sell_in_traded:
                sell_dist[0] += total_sell_in_traded - sum(sell_dist)  # 调整第一个值（最高价档位）
            for i, qty in zip(sell_dist_range, sell_dist):
                updated_sell[i] = qty


        # 买单分配区间：total_traded_indices 内大于 first_buy_idx 的档位
        buy_dist_range = [i for i in total_traded_indices if i > first_buy_idx]
        if buy_dist_range:
            buy_sequence = generate_sequence(sequence_type_buy, len(buy_dist_range))  # 不倒序
            scale_factor = total_buy_in_traded / sum(buy_sequence) if sum(buy_sequence) > 0 else 0
            buy_dist = [max(trade_unit, round(x * scale_factor // trade_unit) * trade_unit) for x in buy_sequence]
            if sum(buy_dist) != total_buy_in_traded:
                buy_dist[-1] += total_buy_in_traded - sum(buy_dist)  # 调整最后一个值（最低价档位）
            for i, qty in zip(buy_dist_range, buy_dist):
                updated_buy[i] = qty
    

        print(f"调整后的最终卖单: {updated_sell}")
        print(f"调整后的最终买单: {updated_buy}")
    else:
        # 计算需要重新分配的总量
        total_sell_in_traded = sum(updated_sell[i] for i in total_traded_indices)
        total_buy_in_traded = sum(updated_buy[i] for i in total_traded_indices)
        print(f"总成交区间内的卖单总量: {total_sell_in_traded}")
        print(f"总成交区间内的买单总量: {total_buy_in_traded}")

        # 清零总成交区间内的所有买单和卖单
        for i in total_traded_indices:
            updated_sell[i] = 0
            updated_buy[i] = 0
        print(f"清零后卖单: {updated_sell}")
        print(f"清零后买单: {updated_buy}")

        if next_open_price > ideal_open_prices[1]:
            # 卖单分配区间
            max_traded_idx = min(total_traded_indices)
            first_above_open_idx = next((i for i, price in enumerate(levels) if price >= next_open_price), 0)
            sell_dist_range = list(range(max_traded_idx, first_above_open_idx + 1))
            if not sell_dist_range:
                first_below_open_idx = next((i for i, price in enumerate(levels) if price <=next_open_price), len(levels)-1)
                updated_sell[first_below_open_idx] = total_sell_in_traded  # 直接赋值
            else:
                sell_sequence = generate_sequence(sequence_type_sell, len(sell_dist_range))[::-1]
                scale_factor = (total_sell_in_traded  / trade_unit) / sum(sell_sequence) if sum(sell_sequence) > 0 else 0
                sell_dist = [max(1, round(x * scale_factor)) for x in sell_sequence]
                if sum(sell_dist) != total_sell_in_traded / trade_unit:
                    sell_dist[-1] += total_sell_in_traded / trade_unit - sum(sell_dist)
                for i, qty in zip(sell_dist_range, sell_dist):
                    updated_buy[i] = qty * trade_unit  # 直接赋值而非累加

            # 买单分配区间
          
            buy_dist_range = list(range(first_below_open_idx + 1, total_traded_indices[-1] + 1))
            buy_sequence = generate_sequence(sequence_type_buy, len(buy_dist_range))
            scale_factor = (total_buy_in_traded  / trade_unit)/ sum(buy_sequence) if sum(buy_sequence) > 0 else 0
            buy_dist = [max(1, round(x * scale_factor)) for x in buy_sequence]
            if sum(buy_dist) != total_buy_in_traded / trade_unit:
                buy_dist[-1] += total_buy_in_traded / trade_unit - sum(buy_dist)
            for i, qty in zip(buy_dist_range, buy_dist):
                updated_buy[i] = qty * trade_unit  # 直接赋值而非累加

        else:  # next_open_price < ideal_open_prices[0]
            # 买单分配区间
            min_traded_idx = max(total_traded_indices)
            first_below_open_idx = next((i for i, price in enumerate(levels) if price <= next_open_price), len(levels)-1)
            buy_dist_range = list(range(min_traded_idx, first_below_open_idx + 1))
            if not buy_dist_range:
                first_above_open_idx = next((i for i, price in enumerate(levels) if price > next_open_price), 0)
                updated_buy[first_below_open_idx] = total_buy_in_traded
            else:
                buy_sequence = generate_sequence(sequence_type_buy, len(buy_dist_range))
                scale_factor = (total_buy_in_traded  / trade_unit)/ sum(buy_sequence) if sum(buy_sequence) > 0 else 0
                buy_dist = [max(1, round(x * scale_factor)) for x in buy_sequence]
                if sum(buy_dist) != total_buy_in_traded  / trade_unit:
                    buy_dist[-1] += total_buy_in_traded  / trade_unit - sum(buy_dist)
                for i, qty in zip(buy_dist_range, buy_dist):
                    updated_buy[i] = qty * trade_unit

            # 卖单分配区间
            
            sell_dist_range = list(range(first_below_open_idx - 1, total_traded_indices[0] + 1))
            sell_sequence = generate_sequence(sequence_type_sell, len(sell_dist_range))[::-1]
            scale_factor = (total_sell_in_traded  / trade_unit)/ sum(sell_sequence) if sum(sell_sequence) > 0 else 0
            sell_dist = [max(1, round(x * scale_factor)) for x in sell_sequence]
            if sum(sell_dist) != total_buy_in_traded  / trade_unit:
                sell_dist[-1] += total_buy_in_traded  / trade_unit - sum(sell_dist)
            for i, qty in zip(sell_dist_range, sell_dist):
                updated_sell[i] = qty * trade_unit

        print(f"调整后的最终卖单: {updated_sell}")
        print(f"调整后的最终买单: {updated_buy}")

# 更新表格
extended_updated_sell = updated_sell + [0] * (len(table) - len(updated_sell))
extended_updated_buy = updated_buy + [0] * (len(table) - len(updated_buy))
table[f"{period_time}_调整后买单"] = extended_updated_buy
table[f"{period_time}_调整后卖单"] = extended_updated_sell


table.at['总卖出', f"{period_time}_调整后卖单"] = 0
table.at['总卖出', f"{period_time}_调整后买单"] = 0
table.at['总买入', f"{period_time}_调整后买单"] = 0
table.at['总买入', f"{period_time}_调整后卖单"] = 0
table.at['总单数', f"{period_time}_调整后卖单"] = 0
table.at['总单数', f"{period_time}_调整后买单"] = 0
table.at['总市值', f"{period_time}_调整后卖单"] = 0
table.at['总市值', f"{period_time}_调整后买单"] = 0
table.at['挂单资金', f"{period_time}_调整后买单"] = 0
table.at['挂单资金', f"{period_time}_调整后卖单"] = 0
table.at['总资金', f"{period_time}_调整后买单"] = 0
table.at['总资金', f"{period_time}_调整后卖单"] = 0
table.at['盈余', f"{period_time}_调整后买单"] = 0
table.at['盈余', f"{period_time}_调整后卖单"] = 0
table.at['总资产', f"{period_time}_调整后买单"] = 0
table.at['总资产', f"{period_time}_调整后卖单"] = 0

total_sell_updated = sum(updated_sell)
total_buy_updated = sum(updated_buy)
table.at['总卖出', f"{period_time}_调整后卖单"] = total_sell_updated
table.at['总卖出', f"{period_time}_调整后买单"] = total_sell_updated
table.at['总买入', f"{period_time}_调整后买单"] = total_buy_updated
table.at['总买入', f"{period_time}_调整后卖单"] = total_buy_updated
table.at['总单数', f"{period_time}_调整后卖单"] = total_sell_updated + total_buy_updated
table.at['总单数', f"{period_time}_调整后买单"] = total_sell_updated + total_buy_updated
table.at['总市值', f"{period_time}_调整后卖单"] = total_sell_updated * close_price
table.at['总市值', f"{period_time}_调整后买单"] = total_sell_updated * close_price
table.at['挂单资金', f"{period_time}_调整后买单"] = sum([qty * price for qty, price in zip(updated_buy, levels[:-6])])
table.at['挂单资金', f"{period_time}_调整后卖单"] = sum([qty * price for qty, price in zip(updated_buy, levels[:-6])])
original_capital1 = original_capital + sum_sell - sum_buy
table.at['总资金', f"{period_time}_调整后买单"] = original_capital1 + sell_amount - buy_amount
table.at['总资金', f"{period_time}_调整后卖单"] = original_capital1 + sell_amount - buy_amount
table.at['盈余', f"{period_time}_调整后买单"] = table.at['总资金', f"{period_time}_调整后买单"] - table.at['挂单资金', f"{period_time}_调整后买单"]
table.at['盈余', f"{period_time}_调整后卖单"] = table.at['总资金', f"{period_time}_调整后卖单"] - table.at['挂单资金', f"{period_time}_调整后卖单"]
table.at['总资产', f"{period_time}_调整后卖单"] = table.at['总资金', f"{period_time}_调整后卖单"] + table.at['总市值', f"{period_time}_调整后卖单"]
table.at['总资产', f"{period_time}_调整后买单"] = table.at['总资金', f"{period_time}_调整后买单"] + table.at['总市值', f"{period_time}_调整后买单"]
original_capital2 = table.at['总资金', f"{period_time}_调整后买单"]

st.write("3. 调整后的最终挂单表格：")
st.dataframe(table)

# 新增循环段：遍历每一行K线信息
for k in range(1, len(df)):  # 从 df.iloc[1] 开始
    period_time = df.iloc[k]['时间'].strftime("%Y-%m-%d %H:%M")
    print(f"\n开始处理第 {k+1} 轮K线，时间: {period_time}")

    # 使用上一轮的 updated_sell 和 updated_buy
    updated_sell = updated_sell.copy()
    updated_buy = updated_buy.copy()
    high_price = df.iloc[k]['最高'] - 0.01
    low_price = df.iloc[k]['最低'] + 0.01
    open_price = df.iloc[k]['开盘']
    close_price = df.iloc[k]['收盘']

    traded_sell = []
    total_sell_volume = 0
    sell_amount = 0
    for i, price in enumerate(levels[:-8]):
        if price <= high_price and updated_sell[i] > 0:
            traded_sell.append((i, price, updated_sell[i]))
            total_sell_volume += updated_sell[i]
            sell_amount += updated_sell[i] * price
    print(f"成交卖单: {traded_sell}")
    print(f"总卖单数量: {total_sell_volume}")
    print(f"卖出金额: {sell_amount}")

    traded_buy = []
    total_buy_volume = 0
    buy_amount = 0
    for i, price in enumerate(levels[:-8]):
        if price >= low_price and updated_buy[i] > 0:
            traded_buy.append((i, price, updated_buy[i]))
            total_buy_volume += updated_buy[i]
            buy_amount += updated_buy[i] * price
    print(f"成交买单: {traded_buy}")
    print(f"总买单数量: {total_buy_volume}")
    print(f"买入金额: {buy_amount}")

    # 计算 high_idx
    price_high_idx = min([i for i, price in enumerate(levels[:-8]) if price <= high_price], default=0)
    zero_sell_indices = [i for i in range(len(updated_sell)) if updated_sell[i] == 0]
    sell_zero_high_idx = min(zero_sell_indices) if zero_sell_indices else len(updated_sell) - 1
    high_idx = min(price_high_idx, sell_zero_high_idx)
    print(f"价格小于等于 high_price 的最低索引: {price_high_idx}")
    print(f"卖单值为零的最大价格索引: {sell_zero_high_idx}")
    print(f"最终 high_idx: {high_idx}")

    # 计算 low_idx
    price_low_idx = max([i for i, price in enumerate(levels[:-8]) if price >= low_price], default=len(levels[:-8])-1)
    zero_buy_indices = [i for i in range(len(updated_buy)) if updated_buy[i] == 0]
    buy_zero_low_idx = max(zero_buy_indices) if zero_buy_indices else 0
    low_idx = max(price_low_idx, buy_zero_low_idx)
    print(f"价格大于等于 low_price 的最高索引: {price_low_idx}")
    print(f"买单值为零的最小价格索引: {buy_zero_low_idx}")
    print(f"最终 low_idx: {low_idx}")

    # 生成本轮成交区间
    round_traded_indices = list(range(high_idx, low_idx + 1))
    print(f"本轮成交区间位置: {round_traded_indices}")

    # 更新 total_traded_indices（使用上一轮的结果）
    print(f"上一轮 total_traded_indices: {total_traded_indices}")
    total_traded_indices = sorted(set(round_traded_indices + total_traded_indices))
    print(f"更新后的总成交区间位置: {total_traded_indices}")

    # 提取本轮成交区间内所有买单数量（包括 0），生成元组
    convert_to_sell = [(i, updated_buy[i]) for i in round_traded_indices]
    print(f"转化卖单（原始）: {convert_to_sell}")

    # 清零本轮成交区间内的买单
    for i in round_traded_indices:
        updated_buy[i] = 0

    # 提取本轮成交区间内所有卖单数量（包括 0），生成元组
    convert_to_buy = [(i, updated_sell[i]) for i in round_traded_indices]
    print(f"转化买单（原始）: {convert_to_buy}")

    # 清零本轮成交区间内的卖单
    for i in round_traded_indices:
        updated_sell[i] = 0

    # 提取数量并倒序
    convert_to_sell_values = [qty for _, qty in convert_to_sell][::-1]
    convert_to_sell = [(idx, qty) for (idx, _), qty in zip(convert_to_sell, convert_to_sell_values)]

    convert_to_buy_values = [qty for _, qty in convert_to_buy][::-1]
    convert_to_buy = [(idx, qty) for (idx, _), qty in zip(convert_to_buy, convert_to_buy_values)]

    print(f"倒序后的转化卖单: {convert_to_sell}")
    print(f"倒序后的转化买单: {convert_to_buy}")

    # 将转化卖单加到 updated_sell
    for idx, qty in convert_to_sell:
        updated_sell[idx] += qty

    # 将转化买单加到 updated_buy
    for idx, qty in convert_to_buy:
        updated_buy[idx] += qty

    # 计算理想开盘区间
    zero_sell_indices = [i for i in range(len(updated_sell)) if updated_sell[i] == 0]
    first_sell_idx = min(zero_sell_indices) if zero_sell_indices else len(updated_sell) - 1

    zero_buy_indices = [i for i in range(len(updated_buy)) if updated_buy[i] == 0]
    first_buy_idx = max(zero_buy_indices) if zero_buy_indices else 0 + 1

    ideal_open_range = (first_sell_idx - 1, first_buy_idx + 1)
    print(f"理想开盘区间索引: {ideal_open_range}")
    has_two_levels = abs(first_buy_idx - first_sell_idx) >= 1
    print(f"理想开盘区间是否有两个档位: {has_two_levels}")
    print(updated_buy)
    print(updated_sell)

    next_open_price = df.iloc[k+1]['开盘'] if k+1 < len(df) else None
    if next_open_price:
        ideal_open_prices = (levels[ideal_open_range[0]], levels[ideal_open_range[1]])
        is_in_ideal_range = ideal_open_prices[1] <= next_open_price <= ideal_open_prices[0]
        print(f"下一日开盘价 {next_open_price} 是否在理想开盘区间 {ideal_open_prices}: {is_in_ideal_range}")

        if is_in_ideal_range:
            total_sell_in_traded = sum(updated_sell[i] for i in total_traded_indices)
            total_buy_in_traded = sum(updated_buy[i] for i in total_traded_indices)
            print(f"总成交区间内的卖单总量: {total_sell_in_traded}")
            print(f"总成交区间内的买单总量: {total_buy_in_traded}")

            for i in total_traded_indices:
                updated_sell[i] = 0
                updated_buy[i] = 0
            print(f"清零后卖单: {updated_sell}")
            print(f"清零后买单: {updated_buy}")

            # 卖单分配逻辑
            sell_dist_range = [i for i in total_traded_indices if i < first_sell_idx]
            if sell_dist_range:
                # 检查是否包含标记档位
                if sell_start_idx in sell_dist_range:
                    fixed_sell_range = [i for i in sell_dist_range if i >= sell_start_idx and i < max(total_traded_indices)]
                    remaining_sell_range = [i for i in sell_dist_range if i not in fixed_sell_range]
                    fixed_sell_total = 0
                    # 设置固定部分的原始值
                    for i in fixed_sell_range:
                        orig_idx = i - sell_start_idx
                        if 0 <= orig_idx < len(original_sell_orders):
                            updated_sell[i] = original_sell_orders[orig_idx]
                            fixed_sell_total += updated_sell[i]
                    # 调整剩余总量和区间
                    remaining_sell_total = total_sell_in_traded - fixed_sell_total
                    if remaining_sell_range and remaining_sell_total > 0:
                        sell_sequence = generate_sequence(sequence_type_sell, len(remaining_sell_range))[::-1]
                        scale_factor = remaining_sell_total / sum(sell_sequence) if sum(sell_sequence) > 0 else 0
                        sell_dist = [max(trade_unit, round(x * scale_factor // trade_unit) * trade_unit) for x in sell_sequence]
                        if sum(sell_dist) != remaining_sell_total:
                            sell_dist[0] += remaining_sell_total - sum(sell_dist)
                        for i, qty in zip(remaining_sell_range, sell_dist):
                            updated_sell[i] = qty
                else:
                    sell_sequence = generate_sequence(sequence_type_sell, len(sell_dist_range))[::-1]
                    scale_factor = total_sell_in_traded / sum(sell_sequence) if sum(sell_sequence) > 0 else 0
                    sell_dist = [max(trade_unit, round(x * scale_factor // trade_unit) * trade_unit) for x in sell_sequence]
                    if sum(sell_dist) != total_sell_in_traded:
                        sell_dist[0] += total_sell_in_traded - sum(sell_dist)
                    for i, qty in zip(sell_dist_range, sell_dist):
                        updated_sell[i] = qty

            # 买单分配逻辑
            buy_dist_range = [i for i in total_traded_indices if i > first_buy_idx]
            if buy_dist_range:
                # 检查是否包含标记档位
                if buy_start_idx in buy_dist_range:
                    fixed_buy_range = [i for i in buy_dist_range if i <= buy_start_idx + len(original_buy_orders) - 1 and i > min(total_traded_indices)]
                    remaining_buy_range = [i for i in buy_dist_range if i not in fixed_buy_range]
                    fixed_buy_total = 0
                    # 设置固定部分的原始值
                    for i in fixed_buy_range:
                        orig_idx = i - buy_start_idx
                        if 0 <= orig_idx < len(original_buy_orders):
                            updated_buy[i] = original_buy_orders[orig_idx]
                            fixed_buy_total += updated_buy[i]
                    # 调整剩余总量和区间
                    remaining_buy_total = total_buy_in_traded - fixed_buy_total
                    if remaining_buy_range and remaining_buy_total > 0:
                        buy_sequence = generate_sequence(sequence_type_buy, len(remaining_buy_range))
                        scale_factor = remaining_buy_total / sum(buy_sequence) if sum(buy_sequence) > 0 else 0
                        buy_dist = [max(trade_unit, round(x * scale_factor // trade_unit) * trade_unit) for x in buy_sequence]
                        if sum(buy_dist) != remaining_buy_total:
                            buy_dist[-1] += remaining_buy_total - sum(buy_dist)
                        for i, qty in zip(remaining_buy_range, buy_dist):
                            updated_buy[i] = qty
                else:
                    buy_sequence = generate_sequence(sequence_type_buy, len(buy_dist_range))
                    scale_factor = total_buy_in_traded / sum(buy_sequence) if sum(buy_sequence) > 0 else 0
                    buy_dist = [max(trade_unit, round(x * scale_factor // trade_unit) * trade_unit) for x in buy_sequence]
                    if sum(buy_dist) != total_buy_in_traded:
                        buy_dist[-1] += total_buy_in_traded - sum(buy_dist)
                    for i, qty in zip(buy_dist_range, buy_dist):
                        updated_buy[i] = qty

            print(f"调整后的最终卖单: {updated_sell}")
            print(f"调整后的最终买单: {updated_buy}")
        else:
            total_sell_in_traded = sum(updated_sell[i] for i in total_traded_indices)
            total_buy_in_traded = sum(updated_buy[i] for i in total_traded_indices)
            print(f"总成交区间内的卖单总量: {total_sell_in_traded}")
            print(f"总成交区间内的买单总量: {total_buy_in_traded}")

            for i in total_traded_indices:
                updated_sell[i] = 0
                updated_buy[i] = 0
            print(f"清零后卖单: {updated_sell}")
            print(f"清零后买单: {updated_buy}")

            if next_open_price > ideal_open_prices[1]:
                max_traded_idx = min(total_traded_indices)
                first_above_open_idx = next((i for i, price in enumerate(levels) if price >= next_open_price), 0)
                sell_dist_range = list(range(max_traded_idx, first_above_open_idx + 1))
                if not sell_dist_range:
                    first_below_open_idx = next((i for i, price in enumerate(levels) if price <= next_open_price), len(levels)-1)
                    updated_sell[first_below_open_idx] = total_sell_in_traded
                else:
                    sell_sequence = generate_sequence(sequence_type_sell, len(sell_dist_range))[::-1]
                    scale_factor = (total_sell_in_traded / trade_unit) / sum(sell_sequence) if sum(sell_sequence) > 0 else 0
                    sell_dist = [max(1, round(x * scale_factor)) for x in sell_sequence]
                    if sum(sell_dist) != total_sell_in_traded / trade_unit:
                        sell_dist[-1] += total_sell_in_traded / trade_unit - sum(sell_dist)
                    for i, qty in zip(sell_dist_range, sell_dist):
                        updated_sell[i] = qty * trade_unit

                first_below_open_idx = next((i for i, price in enumerate(levels) if price < next_open_price), len(levels)-1)
                buy_dist_range = list(range(first_below_open_idx + 1, total_traded_indices[-1] + 1))
                buy_sequence = generate_sequence(sequence_type_buy, len(buy_dist_range))
                scale_factor = (total_buy_in_traded / trade_unit) / sum(buy_sequence) if sum(buy_sequence) > 0 else 0
                buy_dist = [max(1, round(x * scale_factor)) for x in buy_sequence]
                if sum(buy_dist) != total_buy_in_traded / trade_unit:
                    buy_dist[-1] += total_buy_in_traded / trade_unit - sum(buy_dist)
                for i, qty in zip(buy_dist_range, buy_dist):
                    updated_buy[i] = qty * trade_unit

            else:
                min_traded_idx = max(total_traded_indices)
                first_below_open_idx = next((i for i, price in enumerate(levels) if price <= next_open_price), len(levels)-1)
                buy_dist_range = list(range(min_traded_idx, first_below_open_idx + 1))
                if not buy_dist_range:
                    first_above_open_idx = next((i for i, price in enumerate(levels) if price > next_open_price), 0)
                    updated_buy[first_below_open_idx] = total_buy_in_traded
                else:
                    buy_sequence = generate_sequence(sequence_type_buy, len(buy_dist_range))
                    scale_factor = (total_buy_in_traded / trade_unit) / sum(buy_sequence) if sum(buy_sequence) > 0 else 0
                    buy_dist = [max(1, round(x * scale_factor)) for x in buy_sequence]
                    if sum(buy_dist) != total_buy_in_traded / trade_unit:
                        buy_dist[-1] += total_buy_in_traded / trade_unit - sum(buy_dist)
                    for i, qty in zip(buy_dist_range, buy_dist):
                        updated_buy[i] = qty * trade_unit

                sell_dist_range = list(range(first_below_open_idx - 1, total_traded_indices[0] + 1))
                sell_sequence = generate_sequence(sequence_type_sell, len(sell_dist_range))[::-1]
                scale_factor = (total_sell_in_traded / trade_unit) / sum(sell_sequence) if sum(sell_sequence) > 0 else 0
                sell_dist = [max(1, round(x * scale_factor)) for x in sell_sequence]
                if sum(sell_dist) != total_sell_in_traded / trade_unit:
                    sell_dist[-1] += total_sell_in_traded / trade_unit - sum(sell_dist)
                for i, qty in zip(sell_dist_range, sell_dist):
                    updated_sell[i] = qty * trade_unit

            print(f"调整后的最终卖单: {updated_sell}")
            print(f"调整后的最终买单: {updated_buy}")

    # 更新表格
    extended_updated_sell = updated_sell + [0] * (len(table) - len(updated_sell))
    extended_updated_buy = updated_buy + [0] * (len(table) - len(updated_buy))
    table[f"{period_time}_调整后买单"] = extended_updated_buy
    table[f"{period_time}_调整后卖单"] = extended_updated_sell

    table.at['总卖出', f"{period_time}_调整后卖单"] = 0
    table.at['总卖出', f"{period_time}_调整后买单"] = 0
    table.at['总买入', f"{period_time}_调整后买单"] = 0
    table.at['总买入', f"{period_time}_调整后卖单"] = 0
    table.at['总单数', f"{period_time}_调整后卖单"] = 0
    table.at['总单数', f"{period_time}_调整后买单"] = 0
    table.at['总市值', f"{period_time}_调整后卖单"] = 0
    table.at['总市值', f"{period_time}_调整后买单"] = 0
    table.at['挂单资金', f"{period_time}_调整后买单"] = 0
    table.at['挂单资金', f"{period_time}_调整后卖单"] = 0
    table.at['总资金', f"{period_time}_调整后买单"] = 0
    table.at['总资金', f"{period_time}_调整后卖单"] = 0
    table.at['盈余', f"{period_time}_调整后买单"] = 0
    table.at['盈余', f"{period_time}_调整后卖单"] = 0
    table.at['总资产', f"{period_time}_调整后买单"] = 0
    table.at['总资产', f"{period_time}_调整后卖单"] = 0

    total_sell_updated = sum(updated_sell)
    total_buy_updated = sum(updated_buy)
    table.at['总卖出', f"{period_time}_调整后卖单"] = total_sell_updated
    table.at['总卖出', f"{period_time}_调整后买单"] = total_sell_updated
    table.at['总买入', f"{period_time}_调整后买单"] = total_buy_updated
    table.at['总买入', f"{period_time}_调整后卖单"] = total_buy_updated
    table.at['总单数', f"{period_time}_调整后卖单"] = total_sell_updated + total_buy_updated
    table.at['总单数', f"{period_time}_调整后买单"] = total_sell_updated + total_buy_updated
    table.at['总市值', f"{period_time}_调整后卖单"] = total_sell_updated * close_price
    table.at['总市值', f"{period_time}_调整后买单"] = total_sell_updated * close_price
    table.at['挂单资金', f"{period_time}_调整后买单"] = sum([qty * price for qty, price in zip(updated_buy, levels[:-6])])
    table.at['挂单资金', f"{period_time}_调整后卖单"] = sum([qty * price for qty, price in zip(updated_buy, levels[:-6])])
    table.at['总资金', f"{period_time}_调整后买单"] = original_capital2 + sell_amount - buy_amount
    table.at['总资金', f"{period_time}_调整后卖单"] = original_capital2 + sell_amount - buy_amount
    original_capital2 = table.at['总资金', f"{period_time}_调整后卖单"]
    table.at['盈余', f"{period_time}_调整后买单"] = table.at['总资金', f"{period_time}_调整后买单"] - table.at['挂单资金', f"{period_time}_调整后买单"]
    table.at['盈余', f"{period_time}_调整后卖单"] = table.at['总资金', f"{period_time}_调整后卖单"] - table.at['挂单资金', f"{period_time}_调整后卖单"]
    table.at['总资产', f"{period_time}_调整后卖单"] = table.at['总资金', f"{period_time}_调整后卖单"] + table.at['总市值', f"{period_time}_调整后卖单"]
    table.at['总资产', f"{period_time}_调整后买单"] = table.at['总资金', f"{period_time}_调整后买单"] + table.at['总市值', f"{period_time}_调整后买单"]

st.write("最终挂单表格：")
st.dataframe(table)

