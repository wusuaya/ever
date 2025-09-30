import os
import base64
import requests
import json
import re
from datetime import datetime
import streamlit as st

# ====================================
# 用户配置变量 - 请根据需要修改以下设置
# ====================================

# API配置
API_KEY = "sk-wBuUIEArjm2BoTQBCQgzf2bhzksx87xg3pQ3cPsvccmULhAk"  # 请替换为你的实际API密钥
BASE_URL = "https://api.sydney-ai.com/v1"  
MODEL_NAME = "gemini-2.5-flash-image"  # 使用的模型名称

# 提示词选项


PROMPT_OPTIONS = {
    "黄昏商业街": "你是lead8的设计总监，这是一张我简单渲染的图片，我需要你将他变成能够赢得国际竞赛的精致效果图，表达一个夜市热闹的氛围，丰富的人物活动，餐饮外摆，霓虹灯的延时摄影风格，所有材质变为PBR材质效果，玻璃极具质感，店铺内布置也非常时尚与具有设计感，时刻定在偏黄昏的时刻，但是整体色调注意不要整体泛黄，需要有丰富的层次对比，针对近景的店铺可以改为完全打开的开放式设计，类似非常有个性的咖啡厅，形成非常舒适的室内外联通环境。外面的人行道可以增加来往的人群，路边可以增加一些行道树及绿植，但是树木不要对建筑形成大面积的遮挡，还是要突出建筑。目前的铺地还是太单调，需要增加质感及细节，可以考虑雨后湿润，有点反光的感觉",
    "实景合成": """将图片转化为建筑实景合成效果图，需要非常真实地表达周边环境，可以适当增加人，车，植物，等配景组合，使画面生动活泼，不同功能类型的建筑内部可以隐约看到室内的布置，修改后的效果图需要达到可以赢得国际竞赛的水平""",
    "吉卜力风格": """将图片转化为为吉卜力动画风格的一张插画，充满幻想与温暖的色彩。使用柔和的亮色调，营造出温馨、梦幻般的氛围。模型细节以卡通化的方式呈现，轮廓清晰且流畅，背景富有层次，色彩丰富且不失自然感。加入一些细腻的阴影和光线效果，增强其三维感和梦境般的感觉。""",
    "赛博风格": """将图片转化为未来赛博朋克风格，突出金属质感和高科技元素。使用冷色调如蓝色、银色和灰色，营造出现代、未来感的氛围。加强光泽、反射效果，模型表面展示极致细节，配合几何形状和流线型设计。背景中加入虚拟数字或虚拟光线，增加科技感和科幻效果。""",
     "妹岛风格": """Based on the input architectural model image, transform it into a SANAA, Kazuyo Sejima style architectural analysis diagram. 
Minimalist design, large areas of white space, soft delicate lines, semi-transparent layers, low-saturation colors (white, light gray, pale blue, soft green). 
Show analysis arrows, circulation lines, semi-transparent color blocks to indicate functions. 
Add small minimalist human figures and trees for scale. 
Output as a professional architectural analysis drawing, not an art illustration, highlighting spatial relationships and analysis logic.""",

    "MIR风格": """Transform the input architectural model image into a high-end visualization in the style of MIR. 
Cinematic, poetic atmosphere, storytelling mood. 
Soft light and shadow, cloudy or dawn lighting, low saturation cool tones, subtle warm accents. 
Minimalist yet emotional composition, large white space, realistic but painterly feeling. 
Include small everyday human figures blending naturally with the environment. 
Output as a high-end atmospheric architectural visualization.""",

    "SOM风格": """Transform the input architectural model image into an SOM-style visualization. 
Ultra-clear, modern international city atmosphere. 
Strong contrast, bright daylight or urban night lighting. 
Precise materials: reflective glass curtain walls, steel, concrete. 
Large-scale urban perspective, strong order and grid logic. 
Include professional business people, international metropolitan context. 
Output as a sleek, modernist architectural visualization emphasizing clarity and precision.""",

    "KPF风格": """Transform the input architectural model image into a KPF-style visualization. 
Futuristic, grand metropolitan scale. 
Dynamic perspective, aerial or oblique city view. 
Cool blue tones, glowing night lights, high-tech glass and LED facades. 
Emphasize skyscrapers and urban skyline. 
Include dynamic crowds, traffic, and vibrant city life. 
Output as a futuristic metropolitan architectural visualization with dramatic impact."""
}

# API调用设置
MAX_RETRIES = 10  # 最大重试次数
RETRY_DELAY = 0  # 重试延迟时间（秒），0表示立即重试
API_TIMEOUT = 120  # API调用超时时间（秒），建议120秒以等待图片生成
USE_STREAM = True  # 必须使用流式响应才能获取完整的图片数据！

# ====================================
# 以下为功能代码，一般情况下无需修改
# ====================================

def prepare_image_data(image_file):
    """准备上传的图片数据，转换为base64格式"""
    try:
        # 将Streamlit上传的文件保存到本地
        temp_path = os.path.join("temp", image_file.name)
        os.makedirs("temp", exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(image_file.getbuffer())

        # 读取文件并转换为base64
        with open(temp_path, "rb") as img_file:
            encoded_data = base64.b64encode(img_file.read()).decode("utf-8")
            return "data:image/png;base64," + encoded_data

    except Exception as e:
        st.write(f"准备图片数据时出错: {e}")
        return None

def call_api_raw(api_key, base_url, model, messages, image_data, timeout=API_TIMEOUT, use_stream=False):
    """使用原始HTTP请求调用API，获取完整响应"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": messages,
        "image": image_data,  # 将图像数据（base64）添加到请求中
        "stream": use_stream
    }

    url = f"{base_url}/chat/completions"

    try:
        st.write(f"读取中")
        if use_stream:
            st.write("使用流式响应模式...")

        response = requests.post(url, headers=headers, json=data, timeout=timeout, stream=use_stream)
        response.raise_for_status()

        if use_stream:
            # 处理流式响应
            full_content = ""
            all_chunks = []

            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str != '[DONE]':
                            try:
                                chunk = json.loads(data_str)
                                all_chunks.append(chunk)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        full_content += delta['content']
                            except json.JSONDecodeError:
                                pass

            # 构造标准响应格式
            json_response = {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": full_content
                    }
                }],
                "stream_chunks": all_chunks
            }
        else:
            # 获取完整的JSON响应
            json_response = response.json()

        return json_response
    except requests.exceptions.RequestException as e:
        st.write(f"HTTP请求失败: {e}")
        raise

# Streamlit用户交互界面
st.title("筑博AI工作室 ZHUAI 内测-001")
st.write("请上传图片并选择风格:")

# 图片上传
uploaded_images = st.file_uploader("上传图片", accept_multiple_files=True, type=["png", "jpg", "jpeg"])

if uploaded_images:
    for img in uploaded_images:
        st.image(img, caption="上传的图片", use_container_width=True)

# 提示词选择
selected_prompt = st.selectbox("选择图像风格", list(PROMPT_OPTIONS.keys()))
PROMPT_TEXT = PROMPT_OPTIONS[selected_prompt]

# 创建生成图像按钮
if st.button("生成效果图"):
    if uploaded_images:
        # 构建消息内容（包含所有图片）
        content_list = [{"type": "text", "text": PROMPT_TEXT}]
        image_contents = []

        # 处理上传的图片
        for uploaded_image in uploaded_images:
            try:
                image_data = prepare_image_data(uploaded_image)  # 获取图像的Base64编码
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": image_data,
                    },
                })
            except Exception as e:
                st.write(f"处理图片时出错: {uploaded_image} - {e}")
                continue

        # 构建消息对象
        messages = [
            {
                "role": "user",
                "content": content_list + image_contents,
            }
        ]

        # 发送请求
        try:
            # 将图像数据与消息一起传递给API
            raw_response = call_api_raw(
                api_key=API_KEY,
                base_url=BASE_URL,
                model=MODEL_NAME,
                messages=messages,
                image_data=image_contents,  # 将图像数据作为基础图像传给API
                timeout=API_TIMEOUT,
                use_stream=USE_STREAM
            )

            # 提取图像URL并显示
            response_content = raw_response['choices'][0]['message']['content']
            
            # 从API响应中提取图像URL
            if "![image](" in response_content:
                start_idx = response_content.index("![image](") + len("![image](")
                end_idx = response_content.index(")", start_idx)
                image_url = response_content[start_idx:end_idx]

                # 在Streamlit中显示图像
                st.image(image_url, caption="生成的图像", use_container_width=True)
            else:
                st.write("未能找到生成的图像")

        except Exception as e:
            st.write(f"请求失败: {e}")
    else:
        st.write("请先上传图片并选择风格")
