import streamlit as st
import base64
import re
import requests
import json
from datetime import datetime
import time

# ====================================
# 配置
# ====================================
API_KEY = "sk-wBuUIEArjm2BoTQBCQgzf2bhzksx87xg3pQ3cPsvccmULhAk"
BASE_URL = "https://api.sydney-ai.com/v1"
MODEL_NAME = "gemini-2.5-flash-image-hd"

# 新增：轮询配置
MAX_POLLING_ROUNDS = 30  # 最多轮询30次（从10次延长）
POLLING_INTERVAL = 3  # 每次间隔3秒（从2秒延长）

# ====================================
# 辅助函数
# ====================================

def encode_image_to_base64(uploaded_file):
    """将上传的文件转换为base64 - 不进行压缩，保持原始大小"""
    bytes_data = uploaded_file.getvalue()
    encoded_data = base64.b64encode(bytes_data).decode("utf-8")
    
    # 根据文件类型设置正确的MIME类型
    file_type = uploaded_file.type
    if not file_type:
        # 如果无法获取类型，根据扩展名判断
        if uploaded_file.name.lower().endswith('.png'):
            file_type = 'image/png'
        elif uploaded_file.name.lower().endswith(('.jpg', '.jpeg')):
            file_type = 'image/jpeg'
        elif uploaded_file.name.lower().endswith('.gif'):
            file_type = 'image/gif'
        else:
            file_type = 'image/png'  # 默认
    
    return f"data:{file_type};base64,{encoded_data}"

def extract_images_from_response(content):
    """从响应中提取base64图片和URL - 修改：同时返回URL和base64"""
    images = []
    
    # 提取base64图片
    base64_pattern = r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)'
    base64_matches = re.finditer(base64_pattern, content)
    
    for match in base64_matches:
        try:
            base64_data = match.group(1)
            images.append(('base64', base64_data, None))  # 添加None作为URL占位符
        except:
            pass
    
    # 提取URL图片 - 修改：同时保存URL用于备用显示
    url_pattern = r'https?://[^\s<>"]+\.(png|jpg|jpeg|gif|webp)'
    url_matches = re.finditer(url_pattern, content, re.IGNORECASE)
    
    for match in url_matches:
        url = match.group(0)
        images.append(('url', None, url))  # URL类型，保存URL
    
    return images

def call_api(messages, use_stream=True):
    """调用API - 支持上下文 - 延长超时时间"""
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
        # 延长超时时间到180秒
        response = requests.post(url, headers=headers, json=data, timeout=180, stream=use_stream)
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

def build_api_messages():
    """构建包含完整上下文的API消息列表"""
    api_messages = []
    
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            # 构建用户消息
            content_list = [{"type": "text", "text": msg["text"]}]
            
            # 添加图片（原始大小base64编码）
            if msg.get("image_base64"):
                for img_b64 in msg["image_base64"]:
                    content_list.append({
                        "type": "image_url",
                        "image_url": {"url": img_b64}
                    })
            
            api_messages.append({
                "role": "user",
                "content": content_list
            })
        else:
            # 助手消息
            api_messages.append({
                "role": "assistant",
                "content": msg["text"]
            })
    
    return api_messages

def wait_for_images_with_polling(response_images, placeholder):
    """轮询等待图片加载 - 延长等待时间和轮次"""
    if not response_images:
        return response_images
    
    updated_images = []
    
    for img_type, img_data, img_url in response_images:
        if img_type == 'url' and img_url:
            # 对URL图片进行轮询检查
            placeholder.info(f"⏳ 正在等待图片加载... (最多等待 {MAX_POLLING_ROUNDS * POLLING_INTERVAL} 秒)")
            
            image_loaded = False
            for round_num in range(MAX_POLLING_ROUNDS):
                try:
                    response = requests.head(img_url, timeout=5)
                    if response.status_code == 200:
                        image_loaded = True
                        placeholder.success(f"✅ 图片加载成功！(第 {round_num + 1} 次尝试)")
                        break
                except:
                    pass
                
                if round_num < MAX_POLLING_ROUNDS - 1:
                    time.sleep(POLLING_INTERVAL)
            
            if not image_loaded:
                placeholder.warning(f"⚠️ 图片可能需要更长时间加载，已提供URL备用")
            
            updated_images.append(('url', img_data, img_url))
        else:
            updated_images.append((img_type, img_data, img_url))
    
    return updated_images

# ====================================
# Streamlit 应用
# ====================================

st.set_page_config(page_title="AI 图片对话助手", page_icon="🤖", layout="wide")

# 自定义CSS
st.markdown("""
<style>
    .thumbnail-container img {
        max-width: 80px !important;
        max-height: 80px !important;
        object-fit: cover;
        border-radius: 8px;
    }
    
    [data-testid="stFileUploader"] {
        padding: 8px 0px;
    }
    
    .stChatFloatingInputContainer {
        bottom: 0;
        position: sticky;
    }
    
    .image-url-box {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        font-family: monospace;
        font-size: 12px;
        word-break: break-all;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 AI 图片对话助手HD测试")
st.markdown("支持文字和图片的多模态对话，保留完整上下文 | 原始图片质量上传")

# 初始化session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "temp_images" not in st.session_state:
    st.session_state.temp_images = []

# 侧边栏
with st.sidebar:
    st.header("⚙️ 设置")
    
    if st.button("🗑️ 清空对话历史", use_container_width=True):
        st.session_state.messages = []
        st.session_state.temp_images = []
        st.rerun()
    
    st.divider()
    st.caption(f"💬 当前对话轮数: {len(st.session_state.messages)}")
    st.caption(f"🤖 模型: {MODEL_NAME}")
    st.caption(f"⏱️ 图片等待: {MAX_POLLING_ROUNDS}轮 × {POLLING_INTERVAL}秒")

# 显示对话历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # 显示文本
        if message.get("text"):
            st.markdown(message["text"])
        
        # 显示用户上传的图片（正常大小）
        if message.get("images") and message["role"] == "user":
            cols = st.columns(min(len(message["images"]), 3))
            for idx, img_data in enumerate(message["images"]):
                with cols[idx % 3]:
                    st.image(img_data, use_column_width=True)
        
        # 显示AI返回的图片 - 修改：同时显示URL
        if message.get("response_images") and message["role"] == "assistant":
            for img_type, img_data, img_url in message["response_images"]:
                if img_type == 'base64' and img_data:
                    try:
                        st.image(base64.b64decode(img_data), use_column_width=True)
                    except:
                        st.error("图片解码失败")
                elif img_type == 'url' and img_url:
                    # 显示图片
                    st.image(img_url, use_column_width=True)
                    # 显示URL作为备用
                    st.markdown(f'<div class="image-url-box">🔗 图片URL: {img_url}</div>', unsafe_allow_html=True)

# 创建底部容器
st.markdown("---")

# 图片上传区域
col1, col2 = st.columns([4, 1])

with col1:
    uploaded_files = st.file_uploader(
        "📎 上传图片（原始质量）", 
        type=['png', 'jpg', 'jpeg', 'gif'],
        accept_multiple_files=True,
        key="file_uploader",
        label_visibility="visible"
    )

with col2:
    if uploaded_files:
        st.caption(f"✅ {len(uploaded_files)} 张")

# 显示缩略图预览
if uploaded_files:
    st.markdown('<div class="thumbnail-container">', unsafe_allow_html=True)
    cols = st.columns(min(len(uploaded_files), 8))
    for idx, file in enumerate(uploaded_files):
        with cols[idx % 8]:
            st.image(file, width=80)
    st.markdown('</div>', unsafe_allow_html=True)

# 用户输入
prompt = st.chat_input("💬 输入你的问题...")

if prompt:
    # 构建消息内容
    content_list = [{"type": "text", "text": prompt}]
    
    # 处理上传的图片 - 修改：不压缩，原始大小编码
    uploaded_images = []
    image_base64_list = []
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # 原始大小编码，不压缩
            image_data = encode_image_to_base64(uploaded_file)
            image_base64_list.append(image_data)
            uploaded_images.append(uploaded_file.getvalue())
    
    # 添加用户消息到历史
    st.session_state.messages.append({
        "role": "user",
        "text": prompt,
        "images": uploaded_images if uploaded_images else None,
        "image_base64": image_base64_list if image_base64_list else None
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
        status_placeholder = st.empty()
        
        with st.spinner("AI正在思考..."):
            # 构建包含上下文的API消息
            api_messages = build_api_messages()
            
            # 调用API
            response_content = call_api(api_messages)
            
            if response_content:
                # 提取图片
                response_images = extract_images_from_response(response_content)
                
                # 如果有图片，进行轮询等待
                if response_images:
                    response_images = wait_for_images_with_polling(response_images, status_placeholder)
                
                status_placeholder.empty()
                
                # 清理文本内容
                clean_text = re.sub(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+', '', response_content)
                clean_text = re.sub(r'https?://[^\s<>"]+\.(png|jpg|jpeg|gif|webp)', '', clean_text, flags=re.IGNORECASE)
                clean_text = clean_text.strip()
                
                # 显示文本
                if clean_text:
                    st.markdown(clean_text)
                
                # 显示图片和URL
                if response_images:
                    st.success(f"生成了 {len(response_images)} 张图片")
                    for img_type, img_data, img_url in response_images:
                        if img_type == 'base64' and img_data:
                            try:
                                st.image(base64.b64decode(img_data), use_column_width=True)
                            except Exception as e:
                                st.error(f"图片显示失败: {str(e)}")
                        elif img_type == 'url' and img_url:
                            # 显示图片
                            st.image(img_url, use_column_width=True)
                            # 显示URL作为备用
                            st.markdown(f'<div class="image-url-box">🔗 图片URL: {img_url}</div>', unsafe_allow_html=True)
                
                # 添加助手消息到历史
                st.session_state.messages.append({
                    "role": "assistant",
                    "text": clean_text if clean_text else "已生成图片",
                    "response_images": response_images if response_images else None
                })
    
    # 重新运行以刷新页面
    st.rerun()

# 页脚信息
st.caption("💡 提示: 可以上传原始质量图片配合文字提问，AI会记住之前的所有对话内容")
