# NC1.py - Cherry风格聊天界面版本（修复版）
import os
import base64
import requests
import json
import streamlit as st
from datetime import datetime
from io import BytesIO

# ====================================
# API配置
# ====================================
API_KEY = "sk-wBuUIEArjm2BoTQBCQgzf2bhzksx87xg3pQ3cPsvccmULhAk"
BASE_URL = "https://api.sydney-ai.com/v1"
MODEL_NAME = "gemini-2.5-flash-image-vip"
API_TIMEOUT = 120

# ====================================
# 系统提示词
# ====================================
SYSTEM_PROMPT = """你是筑博AI设计助手，专业的建筑效果图生成专家。
**你的核心能力：**
- 基于用户上传的建筑模型图或草图，生成高质量的建筑可视化效果图
- 理解建筑设计语言和国际主流建筑事务所的视觉风格
- 根据用户描述精准控制图像的氛围、材质、光影和细节
**工作流程：**
1. 接收用户上传的建筑图片和文字描述
2. 理解用户的设计意图、风格偏好和具体要求
3. 生成符合要求的效果图
4. 简要说明设计思路和关键视觉元素的处理方式
**注意事项：**
- 保持原始构图和建筑主体不变
- 重点优化材质、光影、配景和氛围
- 生成图像后简要说明设计要点（1-2句话即可）
- 如果用户需求不明确，主动询问细节偏好
请以专业、友好的方式与用户交流，帮助他们获得理想的建筑可视化效果。"""

# ====================================
# 辅助函数
# ====================================

def prepare_image_data(image_file):
    """将上传的图片转换为base64格式"""
    try:
        image_bytes = image_file.getvalue()
        encoded_data = base64.b64encode(image_bytes).decode("utf-8")
        return "data:image/png;base64," + encoded_data
    except Exception as e:
        st.error(f"图片处理错误: {e}")
        return None

def image_to_bytes(image_file):
    """将上传的图片转换为bytes用于显示"""
    try:
        return image_file.getvalue()
    except:
        return None

def call_api_stream(api_key, base_url, model, messages, timeout=API_TIMEOUT):
    """调用API并处理流式响应"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": messages,
        "stream": True
    }
    
    url = f"{base_url}/chat/completions"
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=timeout, stream=True)
        response.raise_for_status()
        
        full_content = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    if data_str != '[DONE]':
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    full_content += delta['content']
                        except json.JSONDecodeError:
                            pass
        
        return full_content
    except Exception as e:
        raise Exception(f"API调用失败: {e}")

def extract_image_url(content):
    """从响应内容中提取图像URL"""
    if "![image](" in content:
        try:
            start_idx = content.index("![image](") + len("![image](")
            end_idx = content.index(")", start_idx)
            return content[start_idx:end_idx]
        except:
            pass
    return None

# ====================================
# Streamlit界面配置
# ====================================

st.set_page_config(
    page_title="筑博AI工作室 - Cherry Chat",
    page_icon="🏗️",
    layout="wide"
)

# 初始化session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "system",
        "content": SYSTEM_PROMPT
    })

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ====================================
# 页面标题
# ====================================
st.title("🏗️ 筑博AI工作室 - Cherry Chat")
st.caption("支持多轮对话的AI建筑效果图生成助手")

# ====================================
# 侧边栏 - 快捷提示词
# ====================================
with st.sidebar:
    st.header("⚙️ 设置")
    
    st.subheader("📝 快捷提示词")
    prompt_templates = {
        "黄昏街景": "将这张图片转化为夜市热闹的黄昏街景效果图，丰富人物活动，餐饮外摆，PBR材质，玻璃质感，时尚店铺，开放式咖啡厅设计，增加行道树和绿植，雨后湿润铺地效果。",
        "写实风格": "将图片转化为建筑实景合成效果图，真实表达周边环境，适当增加人、车、植物等配景，使画面生动活泼，达到国际竞赛水平。",
        "冷淡风格": "MIR风格高端可视化：电影感、诗意氛围、柔和光影、低饱和度冷色调、极简构图、大面积留白、写实但富有画意。",
        "城市日景": "SOM风格专业效果图：超清晰现代都市氛围、强对比度、明亮日光、精准材质细节、大尺度城市透视感、国际一流设计水准。",
        "人文暖调": "KPF风格：温暖人文都市氛围、柔和自然光、暖色调黄昏光影、细腻材质层次、雕塑感、生动城市生活场景、多元文化语境。"
    }
    
    selected_template = st.selectbox("选择风格模板", ["自定义"] + list(prompt_templates.keys()))
    
    if st.button("🗑️ 清空对话历史"):
        st.session_state.messages = [{
            "role": "system",
            "content": SYSTEM_PROMPT
        }]
        st.session_state.chat_history = []
        st.rerun()
    
    st.divider()
    st.caption(f"模型: {MODEL_NAME}")
    st.caption(f"对话轮数: {len(st.session_state.chat_history)}")

# ====================================
# 聊天历史显示区域
# ====================================
chat_container = st.container()

with chat_container:
    for chat in st.session_state.chat_history:
        # 用户消息
        with st.chat_message("user"):
            if chat.get("user_text"):
                st.write(chat["user_text"])
            if chat.get("user_images"):
                cols = st.columns(len(chat["user_images"]))
                for idx, img_bytes in enumerate(chat["user_images"]):
                    with cols[idx]:
                        st.image(img_bytes, caption=f"上传图片 {idx+1}", use_container_width=True)
        
        # 助手回复
        with st.chat_message("assistant"):
            if chat.get("assistant_text"):
                st.write(chat["assistant_text"])
            if chat.get("assistant_image"):
                st.image(chat["assistant_image"], caption="生成的效果图", use_container_width=True)

# ====================================
# 用户输入区域
# ====================================
st.divider()

col1, col2 = st.columns([3, 1])

with col1:
    # 文本输入
    if selected_template != "自定义":
        default_text = prompt_templates[selected_template]
    else:
        default_text = ""
    
    user_input = st.text_area(
        "💬 输入您的需求",
        value=default_text,
        height=100,
        placeholder="描述您想要生成的建筑效果图...",
        key="user_input_area"
    )

with col2:
    # 图片上传
    uploaded_files = st.file_uploader(
        "📷 上传图片",
        accept_multiple_files=True,
        type=["png", "jpg", "jpeg"],
        label_visibility="visible",
        key="file_uploader"
    )
    
    send_button = st.button("🚀 发送", type="primary", use_container_width=True)

# ====================================
# 处理发送逻辑
# ====================================
if send_button:
    if not user_input and not uploaded_files:
        st.warning("⚠️ 请输入文字或上传图片")
    else:
        # 准备用户消息内容
        content_list = []
        user_images_bytes = []  # 改为存储bytes数据
        
        # 添加文本
        if user_input:
            content_list.append({
                "type": "text",
                "text": user_input
            })
        
        # 添加图片
        if uploaded_files:
            for uploaded_file in uploaded_files:
                image_data = prepare_image_data(uploaded_file)
                if image_data:
                    content_list.append({
                        "type": "image_url",
                        "image_url": {"url": image_data}
                    })
                    # 保存图片的bytes数据用于显示
                    img_bytes = image_to_bytes(uploaded_file)
                    if img_bytes:
                        user_images_bytes.append(img_bytes)
        
        # 添加到消息历史
        st.session_state.messages.append({
            "role": "user",
            "content": content_list
        })
        
        # 显示用户消息
        with st.chat_message("user"):
            if user_input:
                st.write(user_input)
            if user_images_bytes:
                cols = st.columns(len(user_images_bytes))
                for idx, img_bytes in enumerate(user_images_bytes):
                    with cols[idx]:
                        st.image(img_bytes, caption=f"上传图片 {idx+1}", use_container_width=True)
        
        # 调用API并显示响应
        with st.chat_message("assistant"):
            with st.spinner("🎨 正在生成效果图..."):
                try:
                    response_content = call_api_stream(
                        api_key=API_KEY,
                        base_url=BASE_URL,
                        model=MODEL_NAME,
                        messages=st.session_state.messages,
                        timeout=API_TIMEOUT
                    )
                    
                    # 提取图像URL
                    image_url = extract_image_url(response_content)
                    
                    # 提取文本（去除图像markdown）
                    text_content = response_content
                    if image_url:
                        text_content = response_content.replace(f"![image]({image_url})", "").strip()
                    
                    # 显示文本
                    if text_content:
                        st.write(text_content)
                    
                    # 显示图像
                    if image_url:
                        st.image(image_url, caption="生成的效果图", use_container_width=True)
                    
                    # 添加到消息历史
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_content
                    })
                    
                    # 保存到聊天历史（用于显示）
                    st.session_state.chat_history.append({
                        "user_text": user_input,
                        "user_images": user_images_bytes,  # 保存bytes数据
                        "assistant_text": text_content,
                        "assistant_image": image_url
                    })
                    
                    st.success("✅ 生成完成！")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ 生成失败: {e}")

# ====================================
# 页脚
# ====================================
st.divider()
st.caption("💡 提示：可以连续对话，AI会记住之前的上下文。支持同时上传多张图片。")
