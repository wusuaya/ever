import streamlit as st
import base64
import re
import requests
import json
from datetime import datetime

# ====================================
# 配置
# ====================================
API_KEY = "sk-wBuUIEArjm2BoTQBCQgzf2bhzksx87xg3pQ3cPsvccmULhAk"
BASE_URL = "https://api.sydney-ai.com/v1"
MODEL_NAME = "gemini-2.5-flash-image-vip"

# ====================================
# 辅助函数
# ====================================

def encode_image_to_base64(uploaded_file):
    """将上传的文件转换为base64"""
    bytes_data = uploaded_file.getvalue()
    encoded_data = base64.b64encode(bytes_data).decode("utf-8")
    return f"data:image/png;base64,{encoded_data}"

def extract_images_from_response(content):
    """从响应中提取base64图片和URL"""
    images = []
    
    # 提取base64图片
    base64_pattern = r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)'
    base64_matches = re.finditer(base64_pattern, content)
    
    for match in base64_matches:
        try:
            base64_data = match.group(1)
            images.append(('base64', base64_data))
        except:
            pass
    
    # 提取URL图片
    url_pattern = r'https?://[^\s<>"]+\.(png|jpg|jpeg|gif)'
    url_matches = re.finditer(url_pattern, content, re.IGNORECASE)
    
    for match in url_matches:
        images.append(('url', match.group(0)))
    
    return images

def call_api(messages, use_stream=True):
    """调用API"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": use_stream
    }
    
    url = f"{BASE_URL}/chat/completions"
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=120, stream=use_stream)
        response.raise_for_status()
        
        if use_stream:
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
        else:
            json_response = response.json()
            return json_response['choices'][0]['message']['content']
            
    except Exception as e:
        st.error(f"API调用失败: {str(e)}")
        return None

# ====================================
# Streamlit 应用
# ====================================

st.set_page_config(page_title="AI 图片对话助手", page_icon="🤖", layout="wide")

st.title("🤖 AI 图片对话助手")
st.markdown("支持文字和图片的多模态对话")

# 初始化session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# 侧边栏 - 上传图片
with st.sidebar:
    st.header("📤 上传图片")
    uploaded_files = st.file_uploader(
        "选择图片文件", 
        type=['png', 'jpg', 'jpeg', 'gif'],
        accept_multiple_files=True,
        key="file_uploader"
    )
    
    if uploaded_files:
        st.success(f"已选择 {len(uploaded_files)} 张图片")
        for idx, file in enumerate(uploaded_files):
            st.image(file, caption=f"图片 {idx+1}", use_column_width=True)
    
    st.divider()
    
    if st.button("🗑️ 清空对话历史"):
        st.session_state.messages = []
        st.rerun()

# 显示对话历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # 显示文本
        if message.get("text"):
            st.markdown(message["text"])
        
        # 显示用户上传的图片
        if message.get("images") and message["role"] == "user":
            cols = st.columns(min(len(message["images"]), 3))
            for idx, img_data in enumerate(message["images"]):
                with cols[idx % 3]:
                    st.image(img_data, use_column_width=True)
        
        # 显示AI返回的图片
        if message.get("response_images") and message["role"] == "assistant":
            for img_type, img_data in message["response_images"]:
                if img_type == 'base64':
                    try:
                        st.image(base64.b64decode(img_data), use_column_width=True)
                    except:
                        pass
                elif img_type == 'url':
                    st.image(img_data, use_column_width=True)

# 用户输入
prompt = st.chat_input("输入你的问题...")

if prompt:
    # 构建消息内容
    content_list = [{"type": "text", "text": prompt}]
    
    # 处理上传的图片
    uploaded_images = []
    if uploaded_files:
        for uploaded_file in uploaded_files:
            image_data = encode_image_to_base64(uploaded_file)
            content_list.append({
                "type": "image_url",
                "image_url": {"url": image_data}
            })
            uploaded_images.append(uploaded_file.getvalue())
    
    # 添加用户消息到历史
    st.session_state.messages.append({
        "role": "user",
        "text": prompt,
        "images": uploaded_images if uploaded_images else None
    })
    
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_images:
            cols = st.columns(min(len(uploaded_images), 3))
            for idx, img_data in enumerate(uploaded_images):
                with cols[idx % 3]:
                    st.image(img_data, use_column_width=True)
    
    # 调用API
    with st.chat_message("assistant"):
        with st.spinner("AI正在思考..."):
            # 构建API消息
            api_messages = [{"role": "user", "content": content_list}]
            
            # 调用API
            response_content = call_api(api_messages)
            
            if response_content:
                # 提取图片
                response_images = extract_images_from_response(response_content)
                
                # 清理文本内容（移除base64数据）
                clean_text = re.sub(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+', '', response_content)
                clean_text = re.sub(r'https?://[^\s<>"]+\.(png|jpg|jpeg|gif)', '', clean_text, flags=re.IGNORECASE)
                clean_text = clean_text.strip()
                
                # 显示文本
                if clean_text:
                    st.markdown(clean_text)
                
                # 显示图片
                if response_images:
                    st.success(f"生成了 {len(response_images)} 张图片")
                    for img_type, img_data in response_images:
                        if img_type == 'base64':
                            try:
                                st.image(base64.b64decode(img_data), use_column_width=True)
                            except Exception as e:
                                st.error(f"图片显示失败: {str(e)}")
                        elif img_type == 'url':
                            st.image(img_data, use_column_width=True)
                
                # 添加助手消息到历史
                st.session_state.messages.append({
                    "role": "assistant",
                    "text": clean_text if clean_text else "已生成图片",
                    "response_images": response_images if response_images else None
                })

# 页脚信息
st.divider()
st.caption(f"💡 提示: 可以上传多张图片并输入问题，AI将基于图片内容进行回答或生成新图片")
