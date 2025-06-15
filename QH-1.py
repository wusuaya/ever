import streamlit as st
import pandas as pd
import akshare as ak
import mplfinance as mpf
from datetime import datetime, timedelta
import numpy as np

# 初始化会话状态
if 'current_index' not in st.session_state:
    st.session_state.current_index = 50  # 初始显示50根K线
if 'cash' not in st.session_state:
    st.session_state.cash = 10000  # 初始资金
if 'position' not in st.session_state:  # 持仓量(正数表示多头,负数表示空头)
    st.session_state.position = 0
if 'position_price' not in st.session_state:  # 开仓价格
    st.session_state.position_price = 0.0
if 'portfolio_value' not in st.session_state:
    st.session_state.portfolio_value = []
if 'actions' not in st.session_state:
    st.session_state.actions = []
if 'margin_ratio' not in st.session_state:  # 保证金比例
    st.session_state.margin_ratio = 0.1  # 默认10%保证金

# 设置页面标题
st.title("期货交互式K线模拟交易系统")

# 用户输入参数
with st.sidebar:
    st.header("期货合约参数")
    symbol = st.text_input("输入期货代码 (例如: AO2509)", value="AO2509")
    period = st.selectbox("选择K线周期", ["1", "5", "15", "30", "60"], index=1)
    contract_multiplier = st.number_input("合约乘数 (元/点)", min_value=1, value=10)
    st.session_state.margin_ratio = st.slider("保证金比例", min_value=0.05, max_value=0.5, value=0.1, step=0.05)
    
    st.header("时间范围")
    end_date = datetime.today()
    start_date = st.date_input("选择开始日期", value=(end_date - timedelta(days=10)))
    end_date = st.date_input("选择结束日期", value=end_date)

# 加载期货数据
@st.cache_data
def load_futures_data(symbol, period, start_date, end_date):
    try:
        df = ak.futures_zh_minute_sina(symbol=symbol, period=period)
        if df.empty:
            return pd.DataFrame()
        
        # 转换日期格式
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        
        # 筛选日期范围
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date) + pd.Timedelta(days=1)
        df = df[(df.index >= start_date) & (df.index < end_date)]
        
        # 确保数据按时间排序
        df.sort_index(inplace=True)
        
        return df
    except Exception as e:
        st.error(f"数据加载错误: {str(e)}")
        return pd.DataFrame()

df = load_futures_data(symbol, period, start_date, end_date)

# 如果没有数据，提示用户
if df.empty:
    st.error("无法获取期货数据，请检查合约代码或时间范围。")
else:
    total_bars = len(df)
    current_data = df.iloc[st.session_state.current_index]
    current_price = current_data['close']
    
    # 计算账户信息
    position_value = abs(st.session_state.position) * st.session_state.position_price * contract_multiplier
    used_margin = position_value * st.session_state.margin_ratio
    
    # 计算浮动盈亏
    if st.session_state.position > 0:  # 多头持仓
        floating_pnl = (current_price - st.session_state.position_price) * st.session_state.position * contract_multiplier
    elif st.session_state.position < 0:  # 空头持仓
        floating_pnl = (st.session_state.position_price - current_price) * abs(st.session_state.position) * contract_multiplier
    else:
        floating_pnl = 0
    
    total_equity = st.session_state.cash + floating_pnl
    
    # 显示账户信息
    st.sidebar.header("账户信息")
    st.sidebar.write(f"可用资金: ¥{st.session_state.cash:.2f}")
    st.sidebar.write(f"持仓: {abs(st.session_state.position)}手 ({'多头' if st.session_state.position > 0 else '空头' if st.session_state.position < 0 else '无持仓'})")
    st.sidebar.write(f"开仓价格: ¥{st.session_state.position_price:.2f}")
    st.sidebar.write(f"占用保证金: ¥{used_margin:.2f}")
    st.sidebar.write(f"浮动盈亏: ¥{floating_pnl:.2f}")
    st.sidebar.write(f"总权益: ¥{total_equity:.2f}")
    st.sidebar.write(f"当前价格: ¥{current_price:.2f}")

    # 显示K线图，保持50根K线宽度
    start_idx = max(0, st.session_state.current_index - 50)
    end_idx = min(total_bars, st.session_state.current_index + 1)
    plot_data = df.iloc[start_idx:end_idx]
    
    # 添加标记显示当前持仓位置
    apds = []
    if st.session_state.position != 0:
        # 找到持仓开始位置
        position_start_idx = max(0, st.session_state.current_index - 50)
        position_data = df.iloc[position_start_idx:st.session_state.current_index]
        
        # 创建标记
        marker_color = 'green' if st.session_state.position > 0 else 'red'
        markers = [np.nan] * len(plot_data)
        if not position_data.empty:
            # 找到持仓开始位置在plot_data中的索引
            pos_idx = position_data.index.get_loc(df.index[st.session_state.current_index - abs(st.session_state.position)])
            markers[pos_idx] = position_data.iloc[pos_idx]['low'] * 0.99
            
            apd = mpf.make_addplot(
                markers,
                type='scatter',
                markersize=100,
                marker='^' if st.session_state.position > 0 else 'v',
                color=marker_color
            )
            apds.append(apd)


    # 绘制K线图
    fig, axlist = mpf.plot(
        plot_data,
        type='candle',
        volume=True,
        style='yahoo',
        mav=(5,20),
        addplot=apds,
        returnfig=True
    )
    st.pyplot(fig)

    # 显示当前K线信息
    current_time = df.index[st.session_state.current_index]
    st.header(f"第 {st.session_state.current_index + 1}/{total_bars} 根K线: {current_time.strftime('%Y-%m-%d %H:%M')}")
    st.write(f"最新价: ¥{current_price:.2f}")

    # 创建交易按钮
    st.subheader("交易操作")
    col1, col2, col3, col4, col5 = st.columns(5)

    # 计算最大可开仓手数
    max_position = int(total_equity // (current_price * contract_multiplier * st.session_state.margin_ratio))

    with col1:
        if st.button("开多仓(全仓)"):
            if max_position > 0:
                # 计算保证金
                margin_required = current_price * max_position * contract_multiplier * st.session_state.margin_ratio
                
                if st.session_state.position < 0:
                    st.error("已有空头持仓，请先平仓")
                else:
                    st.session_state.position = max_position
                    st.session_state.position_price = current_price
                    st.session_state.cash -= margin_required
                    st.session_state.actions.append(
                        f"[{current_time.strftime('%Y-%m-%d %H:%M')}] 开多仓 {max_position}手 @ ¥{current_price:.2f}"
                    )
                    st.success(f"开多仓 {max_position}手")
            else:
                st.error("资金不足")

    with col2:
        if st.button("开多仓(半仓)"):
            if max_position > 0:
                position_size = max(1, max_position // 2)
                margin_required = current_price * position_size * contract_multiplier * st.session_state.margin_ratio
                
                if st.session_state.position < 0:
                    st.error("已有空头持仓，请先平仓")
                else:
                    st.session_state.position = position_size
                    st.session_state.position_price = current_price
                    st.session_state.cash -= margin_required
                    st.session_state.actions.append(
                        f"[{current_time.strftime('%Y-%m-%d %H:%M')}] 开多仓 {position_size}手 @ ¥{current_price:.2f}"
                    )
                    st.success(f"开多仓 {position_size}手")
            else:
                st.error("资金不足")

    with col3:
        if st.button("开空仓(全仓)"):
            if max_position > 0:
                margin_required = current_price * max_position * contract_multiplier * st.session_state.margin_ratio
                
                if st.session_state.position > 0:
                    st.error("已有多头持仓，请先平仓")
                else:
                    st.session_state.position = -max_position
                    st.session_state.position_price = current_price
                    st.session_state.cash -= margin_required
                    st.session_state.actions.append(
                        f"[{current_time.strftime('%Y-%m-%d %H:%M')}] 开空仓 {max_position}手 @ ¥{current_price:.2f}"
                    )
                    st.success(f"开空仓 {max_position}手")
            else:
                st.error("资金不足")

    with col4:
        if st.button("开空仓(半仓)"):
            if max_position > 0:
                position_size = max(1, max_position // 2)
                margin_required = current_price * position_size * contract_multiplier * st.session_state.margin_ratio
                
                if st.session_state.position > 0:
                    st.error("已有多头持仓，请先平仓")
                else:
                    st.session_state.position = -position_size
                    st.session_state.position_price = current_price
                    st.session_state.cash -= margin_required
                    st.session_state.actions.append(
                        f"[{current_time.strftime('%Y-%m-%d %H:%M')}] 开空仓 {position_size}手 @ ¥{current_price:.2f}"
                    )
                    st.success(f"开空仓 {position_size}手")
            else:
                st.error("资金不足")

    col6, col7, col8, col9, col10 = st.columns(5)

    with col6:
        if st.button("平多仓(全仓)"):
            if st.session_state.position > 0:
                # 计算盈亏
                pnl = (current_price - st.session_state.position_price) * st.session_state.position * contract_multiplier
                # 释放保证金
                margin_released = st.session_state.position_price * st.session_state.position * contract_multiplier * st.session_state.margin_ratio
                
                st.session_state.cash += margin_released + pnl
                st.session_state.actions.append(
                    f"[{current_time.strftime('%Y-%m-%d %H:%M')}] 平多仓 {st.session_state.position}手 @ ¥{current_price:.2f} | 盈亏: ¥{pnl:.2f}"
                )
                st.success(f"平多仓 {st.session_state.position}手, 盈亏: ¥{pnl:.2f}")
                st.session_state.position = 0
                st.session_state.position_price = 0.0
            else:
                st.error("没有多头持仓")

    with col7:
        if st.button("平多仓(半仓)"):
            if st.session_state.position > 0:
                close_size = max(1, st.session_state.position // 2)
                # 计算盈亏
                pnl = (current_price - st.session_state.position_price) * close_size * contract_multiplier
                # 释放保证金
                margin_released = st.session_state.position_price * close_size * contract_multiplier * st.session_state.margin_ratio
                
                st.session_state.cash += margin_released + pnl
                st.session_state.position -= close_size
                st.session_state.actions.append(
                    f"[{current_time.strftime('%Y-%m-%d %H:%M')}] 平多仓 {close_size}手 @ ¥{current_price:.2f} | 盈亏: ¥{pnl:.2f}"
                )
                st.success(f"平多仓 {close_size}手, 盈亏: ¥{pnl:.2f}")
            else:
                st.error("没有多头持仓")

    with col8:
        if st.button("平空仓(全仓)"):
            if st.session_state.position < 0:
                position_size = abs(st.session_state.position)
                # 计算盈亏
                pnl = (st.session_state.position_price - current_price) * position_size * contract_multiplier
                # 释放保证金
                margin_released = st.session_state.position_price * position_size * contract_multiplier * st.session_state.margin_ratio
                
                st.session_state.cash += margin_released + pnl
                st.session_state.actions.append(
                    f"[{current_time.strftime('%Y-%m-%d %H:%M')}] 平空仓 {position_size}手 @ ¥{current_price:.2f} | 盈亏: ¥{pnl:.2f}"
                )
                st.success(f"平空仓 {position_size}手, 盈亏: ¥{pnl:.2f}")
                st.session_state.position = 0
                st.session_state.position_price = 0.0
            else:
                st.error("没有空头持仓")

    with col9:
        if st.button("平空仓(半仓)"):
            if st.session_state.position < 0:
                position_size = abs(st.session_state.position)
                close_size = max(1, position_size // 2)
                # 计算盈亏
                pnl = (st.session_state.position_price - current_price) * close_size * contract_multiplier
                # 释放保证金
                margin_released = st.session_state.position_price * close_size * contract_multiplier * st.session_state.margin_ratio
                
                st.session_state.cash += margin_released + pnl
                st.session_state.position += close_size  # 因为是负数，所以加
                st.session_state.actions.append(
                    f"[{current_time.strftime('%Y-%m-%d %H:%M')}] 平空仓 {close_size}手 @ ¥{current_price:.2f} | 盈亏: ¥{pnl:.2f}"
                )
                st.success(f"平空仓 {close_size}手, 盈亏: ¥{pnl:.2f}")
            else:
                st.error("没有空头持仓")

    with col10:
        if st.button("不操作"):
            st.session_state.actions.append(
                f"[{current_time.strftime('%Y-%m-%d %H:%M')}] 不操作"
            )
            st.info("保持不变")

    # 下一根K线按钮
    if st.session_state.current_index < total_bars - 1:
        if st.button("下一根K线"):
            st.session_state.current_index += 1
            # 记录当前权益
            st.session_state.portfolio_value.append(total_equity)
    else:
        st.success("已到最后一根K线")

    # 显示交易记录
    st.header("交易记录")
    for action in st.session_state.actions[-20:]:  # 显示最近20条记录
        st.write(action)

    # 显示权益曲线
    if len(st.session_state.portfolio_value) > 1:
        st.header("账户权益曲线")
        equity_df = pd.DataFrame({
            '时间': df.index[50:50+len(st.session_state.portfolio_value)],
            '权益': st.session_state.portfolio_value
        })
        st.line_chart(equity_df.set_index('时间'))

    # 显示最终收益
    if st.session_state.current_index == total_bars - 1:
        initial_capital = 10000
        profit = total_equity - initial_capital
        roi = (profit / initial_capital) * 100
        st.header("交易总结")
        st.write(f"初始资金: ¥{initial_capital:.2f}")
        st.write(f"最终权益: ¥{total_equity:.2f}")
        st.write(f"总收益: ¥{profit:.2f}")
        st.write(f"收益率: {roi:.2f}%")
        st.write(f"总交易次数: {len(st.session_state.actions)}")
        
        # 计算胜率 (如果有交易)
        if st.session_state.actions:
            wins = 0
            for action in st.session_state.actions:
                if "盈亏: ¥" in action and float(action.split("盈亏: ¥")[1].split(" ")[0]) > 0:
                    wins += 1
            win_rate = (wins / len(st.session_state.actions)) * 100 if st.session_state.actions else 0
            st.write(f"胜率: {win_rate:.2f}%")

# 添加重置按钮
if st.sidebar.button("重置交易"):
    st.session_state.current_index = 50
    st.session_state.cash = 10000
    st.session_state.position = 0
    st.session_state.position_price = 0.0
    st.session_state.portfolio_value = []
    st.session_state.actions = []
    st.experimental_rerun()