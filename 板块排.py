import streamlit as st
import pandas as pd
import os
from collections import defaultdict
import akshare as ak

# 保留板块排.py的所有原始功能（假设已经包含所有绘图和交互功能）

# 新增：NTTS关联按钮功能
def ntts_association(concept_df, industry_df, ntts_file_path):
    try:
        # 读取 NTTS 文件
        ntts_data = pd.read_excel(ntts_file_path, sheet_name=0)
        ntts_data['code_clean'] = ntts_data['code'].astype(str).str.extract(r'(\d{6})')[0]  # 提取后六位数字

        # 获取所有概念板块和行业板块的成交量前十和涨幅前十的股票代码
        all_codes = defaultdict(list)  # 存储股票代码与对应的板块信息

        # 处理概念板块和行业板块数据
        for board_df, board_type in zip([concept_df, industry_df], ["概念板块", "行业板块"]):
            for _, row in board_df.head(10).iterrows():
                board_name = row['板块名称']
                if board_type == "概念板块":
                    cons_em_df = ak.stock_board_concept_cons_em(symbol=board_name)
                else:
                    cons_em_df = ak.stock_board_industry_cons_em(symbol=board_name)
                # 获取成交量前十和涨幅前十
                top_10_volume = cons_em_df.sort_values(by='成交额', ascending=False).head(10)
                top_10_change = cons_em_df.sort_values(by='涨跌幅', ascending=False).head(10)
                # 添加到 all_codes 中
                for _, stock_row in pd.concat([top_10_volume, top_10_change]).drop_duplicates().iterrows():
                    stock_code = stock_row['代码']
                    stock_name = stock_row['名称']
                    all_codes[stock_code].append(f"{board_name}（{board_type}）")

        # 匹配 NTTS 数据中的代码
        matched_data = ntts_data[ntts_data['code_clean'].isin(all_codes.keys())]

        # 展示匹配结果
        if not matched_data.empty:
            st.subheader("NTTS 筛选统计关联的股票信息")

            # 为匹配的股票添加所属板块信息
            matched_data['所属板块'] = matched_data['code_clean'].apply(
                lambda x: ', '.join(all_codes.get(x, []))
            )

            # 展开合并单元格的所有行
            expanded_data = []
            for _, group in matched_data.groupby('code_clean'):
                for _, row in group.iterrows():
                    expanded_data.append(row)

            expanded_df = pd.DataFrame(expanded_data)

            # 展示最终结果
            st.dataframe(expanded_df)
        else:
            st.write("没有匹配的股票信息。")
    except Exception as e:
        st.error(f"关联失败：{e}")

# Streamlit 主界面
def main():
    st.title("板块和行业排名图表展示")
    # 保留原有的概念板块和行业板块加载逻辑
    concept_df = ak.stock_board_concept_name_em()
    industry_df = ak.stock_board_industry_name_em()

    # 显示行业和概念板块排名（板块排.py 的原始功能）
    option = st.selectbox("选择功能", ["行业板块排名", "概念板块排名", "NTTS关联"])
    if option == "行业板块排名":
        # 原始行业板块逻辑
        pass  # 替换为板块排.py中行业板块的函数调用
    elif option == "概念板块排名":
        # 原始概念板块逻辑
        pass  # 替换为板块排.py中概念板块的函数调用
    elif option == "NTTS关联":
        # 新增NTTS关联逻辑
        ntts_file_path = "./NTTS筛选统计.xlsx"  # 默认根目录路径
        ntts_association(concept_df, industry_df, ntts_file_path)

if __name__ == "__main__":
    main()

