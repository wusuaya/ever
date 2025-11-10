import streamlit as st
import pandas as pd
import requests
from pathlib import Path
import time
from datetime import datetime

# 页面配置
st.set_page_config(page_title="A股板块热度分析", layout="wide")
st.title("🔥 A股板块热度分析与NTTS关联")

# NTTS文件完整路径（固定文件名）
NTTS_FILE = Path(__file__).parent / "NTTS筛选统计.xlsx"

# ==================== 数据获取函数 ====================

@st.cache_data(ttl=300)  # 缓存5分钟
def get_board_data_direct():
    """直接调用东方财富网API获取板块数据"""
    
    # 概念板块排名API
    concept_url = "http://push2.eastmoney.com/api/qt/clist/get?fid=f3&po=1&pz=100&pn=1&np=1&fltt=2&invt=2&fs=m:90+t:3&fields=f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124,f1,f13"
    
    # 行业板块排名API
    industry_url = "http://push2.eastmoney.com/api/qt/clist/get?fid=f3&po=1&pz=100&pn=1&np=1&fltt=2&invt=2&fs=m:90+t:2&fields=f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124,f1,f13"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        # 获取概念板块
        concept_response = requests.get(concept_url, headers=headers, timeout=10)
        concept_data = concept_response.json()
        
        if 'data' in concept_data and concept_data['data'] and 'diff' in concept_data['data']:
            concept_list = concept_data['data']['diff']
            concept_df = pd.DataFrame(concept_list)
            concept_df.rename(columns={
                'f12': '板块代码',
                'f14': '板块名称',
                'f2': '最新价',
                'f3': '涨跌幅',
                'f62': '主力净流入',
                'f66': '成交额',
                'f184': '总市值'
            }, inplace=True)
        else:
            st.error("概念板块数据返回格式异常")
            concept_df = pd.DataFrame()
        
        time.sleep(0.5)  # 避免请求过快
        
        # 获取行业板块
        industry_response = requests.get(industry_url, headers=headers, timeout=10)
        industry_data = industry_response.json()
        
        if 'data' in industry_data and industry_data['data'] and 'diff' in industry_data['data']:
            industry_list = industry_data['data']['diff']
            industry_df = pd.DataFrame(industry_list)
            industry_df.rename(columns={
                'f12': '板块代码',
                'f14': '板块名称',
                'f2': '最新价',
                'f3': '涨跌幅',
                'f62': '主力净流入',
                'f66': '成交额',
                'f184': '总市值'
            }, inplace=True)
        else:
            st.error("行业板块数据返回格式异常")
            industry_df = pd.DataFrame()
        
        return concept_df, industry_df, 'success'
    
    except Exception as e:
        st.error(f"❌ 数据获取失败: {e}")
        return pd.DataFrame(), pd.DataFrame(), 'failed'


def get_board_stocks_direct(board_code, board_type='concept'):
    """直接获取板块成分股"""
    
    # 根据板块类型构建URL
    if board_type == 'concept':
        url = f"http://push2.eastmoney.com/api/qt/clist/get?fid=f62&po=1&pz=500&pn=1&np=1&fltt=2&invt=2&fs=b:{board_code}&fields=f12,f14,f2,f3,f62,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124,f1,f13"
    else:
        url = f"http://push2.eastmoney.com/api/qt/clist/get?fid=f62&po=1&pz=500&pn=1&np=1&fltt=2&invt=2&fs=b:{board_code}&fields=f12,f14,f2,f3,f62,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124,f1,f13"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if 'data' in data and data['data'] and 'diff' in data['data']:
            stock_list = data['data']['diff']
            df = pd.DataFrame(stock_list)
            
            # 字段映射
            df.rename(columns={
                'f12': '代码',
                'f14': '名称',
                'f2': '最新价',
                'f3': '涨跌幅',
                'f62': '主力净流入',
                'f66': '成交额'
            }, inplace=True)
            
            # 转换数据类型
            df['涨跌幅'] = pd.to_numeric(df['涨跌幅'], errors='coerce')
            df['成交额'] = pd.to_numeric(df['成交额'], errors='coerce')
            
            return df
        else:
            return pd.DataFrame()
    
    except Exception as e:
        st.warning(f"获取板块 {board_code} 成分股失败: {e}")
        return pd.DataFrame()


# ==================== NTTS关联分析 ====================

def ntts_association_analysis(ntts_file_path, top_n=10):
    """NTTS股票与热门板块关联分析"""
    
    st.subheader("🔍 NTTS股票热度分析")
    
    # 检查文件是否存在
    if not Path(ntts_file_path).exists():
        st.error(f"❌ 文件不存在: {ntts_file_path}")
        return
    
    # 读取NTTS文件
    try:
        ntts_df = pd.read_excel(ntts_file_path)
        st.info(f"📊 NTTS文件包含 {len(ntts_df)} 只股票")
        
        # 处理合并单元格：使用前向填充(forward fill)
        # 对code列进行前向填充
        if len(ntts_df.columns) >= 2:
            code_column = ntts_df.columns[1]  # 第二列是code
            ntts_df[code_column] = ntts_df[code_column].fillna(method='ffill')
            
            # 清洗股票代码（提取6位数字）
            ntts_df['code_clean'] = ntts_df[code_column].astype(str).str.extract(r'(\d{6})')[0]
        else:
            st.error("❌ NTTS文件格式不正确")
            return
        
    except Exception as e:
        st.error(f"❌ 读取NTTS文件失败: {e}")
        import traceback
        st.code(traceback.format_exc())
        return
    
    # 获取板块数据
    with st.spinner("正在获取板块数据..."):
        concept_df, industry_df, status = get_board_data_direct()
    
    if status != 'success' or concept_df.empty:
        st.error("❌ 无法获取板块数据")
        return
    
    # 分析热门板块
    hot_stocks_map = {}  # {股票代码: [板块列表]}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 取涨幅前N的概念板块
    top_concepts = concept_df.nlargest(top_n, '涨跌幅')
    
    for idx, (_, board) in enumerate(top_concepts.iterrows()):
        board_code = board['板块代码']
        board_name = board['板块名称']
        
        status_text.text(f"正在分析板块: {board_name} ({idx+1}/{top_n})")
        
        # 获取板块成分股
        stocks_df = get_board_stocks_direct(board_code, 'concept')
        
        if stocks_df.empty:
            continue
        
        # 筛选成交额TOP10和涨幅TOP10
        top_amount = stocks_df.nlargest(10, '成交额')
        top_pct = stocks_df.nlargest(10, '涨跌幅')
        
        # 合并并去重
        selected_stocks = pd.concat([top_amount, top_pct]).drop_duplicates('代码')
        
        # 记录股票所属板块
        for _, stock in selected_stocks.iterrows():
            code = stock['代码']
            if code not in hot_stocks_map:
                hot_stocks_map[code] = []
            hot_stocks_map[code].append(board_name)
        
        progress_bar.progress((idx + 1) / top_n)
        time.sleep(0.3)  # 避免请求过快
    
    status_text.empty()
    progress_bar.empty()
    
    # 匹配NTTS股票
    ntts_df['所属热门板块'] = ntts_df['code_clean'].map(
        lambda x: ', '.join(hot_stocks_map.get(x, []))
    )
    
    # 筛选有匹配的股票
    matched_df = ntts_df[ntts_df['所属热门板块'] != ''].copy()
    matched_df['板块数量'] = matched_df['所属热门板块'].str.count(',') + 1
    
    # 显示结果
    st.success(f"✅ 在 {len(ntts_df)} 只NTTS股票中，有 **{len(matched_df)}** 只处于热门板块")
    
    if not matched_df.empty:
        # 按板块数量排序
        matched_df = matched_df.sort_values('板块数量', ascending=False)
        
        # 显示NTTS文件的所有原始列（排除临时列code_clean）
        display_columns = [col for col in matched_df.columns if col != 'code_clean']
        
        st.dataframe(
            matched_df[display_columns],
            use_container_width=True,
            height=400
        )
        
        # 导出功能
        csv = matched_df[display_columns].to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下载匹配结果",
            data=csv,
            file_name=f"NTTS热门板块匹配_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ 未找到匹配的股票")


# ==================== 主程序 ====================

def main():
    # 侧边栏
    st.sidebar.header("⚙️ 设置")
    
    # 数据更新
    if st.sidebar.button("🔄 刷新数据", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    top_n = st.sidebar.slider("分析前N个热门板块", 5, 30, 10)
    
    st.sidebar.markdown("---")
    st.sidebar.info(f"📁 NTTS文件:\n`{NTTS_FILE}`")
    
    # 显示板块排名
    tab1, tab2, tab3 = st.tabs(["📈 概念板块", "🏢 行业板块", "🎯 NTTS关联分析"])
    
    with tab1:
        st.subheader("概念板块涨幅排名")
        with st.spinner("正在加载概念板块数据..."):
            concept_df, _, status = get_board_data_direct()
        
        if status == 'success' and not concept_df.empty:
            concept_df['涨跌幅'] = pd.to_numeric(concept_df['涨跌幅'], errors='coerce')
            display_df = concept_df[['板块名称', '涨跌幅', '成交额', '主力净流入']].head(30)
            st.dataframe(display_df, use_container_width=True, height=600)
        else:
            st.error("无法加载概念板块数据")
    
    with tab2:
        st.subheader("行业板块涨幅排名")
        with st.spinner("正在加载行业板块数据..."):
            _, industry_df, status = get_board_data_direct()
        
        if status == 'success' and not industry_df.empty:
            industry_df['涨跌幅'] = pd.to_numeric(industry_df['涨跌幅'], errors='coerce')
            display_df = industry_df[['板块名称', '涨跌幅', '成交额', '主力净流入']].head(30)
            st.dataframe(display_df, use_container_width=True, height=600)
        else:
            st.error("无法加载行业板块数据")
    
    with tab3:
        # 检查NTTS文件
        if Path(NTTS_FILE).exists():
            st.success(f"✅ 找到文件: NTTS筛选统计.xlsx")
            if st.button("🚀 开始分析", type="primary", use_container_width=True):
                ntts_association_analysis(NTTS_FILE, top_n)
        else:
            st.error(f"❌ 文件不存在: {NTTS_FILE}")
    
    # 页脚
    st.sidebar.markdown("---")
    st.sidebar.caption(f"⏰ 数据缓存时间: 5分钟")
    st.sidebar.caption(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
