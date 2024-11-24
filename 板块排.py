import pandas as pd
from collections import defaultdict
import streamlit as st
import akshare as ak

# 定义读取概念板块和行业板块数据的函数
def get_boards():
    excluded_boards = ['昨日连板', '昨日涨停', '昨日连板_含一字', '昨日涨停_含一字', '百元股']
    concept_df = ak.stock_board_concept_name_em()
    concept_df = concept_df[~concept_df['板块名称'].str.contains('|'.join(excluded_boards))]
    industry_df = ak.stock_board_industry_name_em()
    industry_df = industry_df[~industry_df['板块名称'].str.contains('|'.join(excluded_boards))]
    return concept_df, industry_df

# 重复个股统计，添加股票代码
def show_repeated_stocks_with_code(concept_df, industry_df, ntts_file_path):
    concept_boards = concept_df.head(10)['板块名称'].tolist()
    industry_boards = industry_df.head(10)['板块名称'].tolist()
    stock_count = defaultdict(lambda: {'count': 0, 'boards': [], 'codes': []})

    for board_name in concept_boards:
        stock_board_concept_cons_em_df = ak.stock_board_concept_cons_em(symbol=board_name)
        for _, row in stock_board_concept_cons_em_df.iterrows():
            stock_name = row['名称']
            stock_code = row['代码']
            stock_count[stock_name]['count'] += 1
            stock_count[stock_name]['boards'].append(f"{board_name}（概念板块）")
            stock_count[stock_name]['codes'].append(stock_code)

    for board_name in industry_boards:
        stock_board_industry_cons_em_df = ak.stock_board_industry_cons_em(symbol=board_name)
        for _, row in stock_board_industry_cons_em_df.iterrows():
            stock_name = row['名称']
            stock_code = row['代码']
            stock_count[stock_name]['count'] += 1
            stock_count[stock_name]['boards'].append(f"{board_name}（行业板块）")
            stock_count[stock_name]['codes'].append(stock_code)

    repeated_stocks = pd.DataFrame([
        {'个股名称': stock, '股票代码': ', '.join(set(info['codes'])),
         '重复次数': info['count'], '所属板块': ', '.join(set(info['boards']))}
        for stock, info in stock_count.items() if info['count'] > 1
    ]).sort_values(by='重复次数', ascending=False)

    st.subheader("重复出现的个股（按重复次数排序，带股票代码）")
    if not repeated_stocks.empty:
        st.dataframe(repeated_stocks)
    else:
        st.write("没有重复出现的个股。")

    # 读取 NTTS 筛选统计.xlsx 并比较代码
    ntts_data = pd.read_excel(ntts_file_path)
    ntts_data['code_clean'] = ntts_data['code'].astype(str).str.extract(r'(\d{6})')[0]  # 提取后六位数字

    # 找出重复代码并展示
    repeated_codes = []
    for _, row in repeated_stocks.iterrows():
        stock_codes = row['股票代码'].split(', ')
        for code in stock_codes:
            if code in ntts_data['code_clean'].values:
                matching_rows = ntts_data[ntts_data['code_clean'] == code]
                repeated_codes.append({
                    'code': code,
                    '个股名称': row['个股名称'],
                    '所属板块': row['所属板块'],
                    'NTTS 信息': matching_rows.to_dict('records')
                })

    # 展示重复代码及相关信息
    if repeated_codes:
        st.subheader("NTTS 筛选统计中重复的股票代码信息")
        for repeated_code in repeated_codes:
            st.write(f"股票代码: {repeated_code['code']}")
            st.write(f"个股名称: {repeated_code['个股名称']}")
            st.write(f"所属板块: {repeated_code['所属板块']}")
            st.write("NTTS 信息:")
            for record in repeated_code['NTTS 信息']:
                st.write(record)
    else:
        st.write("没有重复的股票代码。")

# Streamlit 应用主界面
def main():
    st.title("板块和行业排名图表展示")
    concept_df, industry_df = get_boards()
    
    # 获取 NTTS 文件路径
    ntts_file_path = st.text_input("输入 NTTS 筛选统计.xlsx 文件路径", value="NTTS筛选统计.xlsx")
    
    # 显示重复个股的统计信息
    if st.button("统计重复个股"):
        show_repeated_stocks_with_code(concept_df, industry_df, ntts_file_path)

if __name__ == "__main__":
    main()



