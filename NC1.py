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
MODEL_NAME = "gemini-2.5-flash-image-vip"  # 使用的模型名称

# 提示词选项


PROMPT_OPTIONS = {
    "黄昏街景": "你是lead8的设计总监，这是一张我简单渲染的图片，我需要你将他变成能够赢得国际竞赛的精致效果图，表达一个夜市热闹的氛围，丰富的人物活动，餐饮外摆，所有材质变为PBR材质效果，玻璃极具质感，店铺内布置也非常时尚与具有设计感，时刻定在偏黄昏的时刻，但是整体色调注意不要整体泛黄，需要有丰富的层次对比，针对近景的店铺可以改为完全打开的开放式设计，类似非常有个性的咖啡厅，形成非常舒适的室内外联通环境。外面的人行道可以增加来往的人群，路边可以增加一些行道树及绿植，但是树木不要对建筑形成大面积的遮挡，还是要突出建筑。目前的铺地还是太单调，需要增加质感及细节，可以考虑雨后湿润，有点反光的感觉",
    "写实风格": """将图片转化为建筑实景合成效果图，需要非常真实地表达周边环境，可以适当增加人，车，植物，等配景组合，使画面生动活泼，不同功能类型的建筑内部可以隐约看到室内的布置，修改后的效果图需要达到可以赢得国际竞赛的水平""",
    "实景照片": """将图片转化为建筑摄影实景照片，需要达到可以登上世界建筑杂志的水平""",

    "冷淡风格": """Transform the input architectural model image into a high-end visualization in the style of MIR. 
Cinematic, poetic atmosphere, storytelling mood. 
Soft light and shadow, cloudy or dawn lighting, low saturation cool tones, subtle warm accents. 
Minimalist yet emotional composition, large white space, realistic but painterly feeling. 
Include small everyday human figures blending naturally with the environment. 
Output as a high-end atmospheric architectural visualization.""",
    "城市日景": """将输入的建筑模型截图转化为 SOM 风格的专业效果图。保持原有构图和视角完全不变。生成超清晰的现代国际都市氛围视觉效果。采用强对比度构图，采用明亮日光或都市夜景灯光渲染。精准表现材质细节：玻璃幕墙的反射效果、钢结构线条感、混凝土质感。呈现大尺度城市透视感，强化秩序感与网格逻辑的视觉组织。融入专业商务人士形象与国际大都市背景元素。最终输出为简洁极简主义的建筑可视化效果，强调清晰度、精准性与国际一流设计水准。""",

    "人文暖调": """将输入的建筑模型截图转化为 KPF 风格的专业效果图。保持原有构图和视角完全不变。呈现温暖而富有人文气息的都市氛围，采用柔和自然光线或暖色调黄昏光影。注重材质的层次与细腻质感：哑光与高光玻璃的组合、石材肌理、金属暖色调表面。强调建筑的雕塑感与立体层次，展现优雅的体块关系与韵律变化。融入生动的城市生活场景：行人互动、街道活力、绿化景观细节。背景呈现多元文化的国际都市语境，强调场所精神与人性化尺度。最终输出为精致、富有叙事性的建筑可视化效果，平衡技术精度与艺术表现力。"""
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
