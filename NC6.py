import os
import base64
import requests
import json
from datetime import datetime
import streamlit as st
from PIL import Image, ImageDraw
import io
import streamlit.components.v1 as components

# 安装: pip install streamlit-javascript
try:
    from streamlit_js_eval import streamlit_js_eval, get_page_location
except ImportError:
    st.error("❌ 请先安装依赖: pip install streamlit-javascript")
    st.stop()

# ====================================
# 用户配置变量
# ====================================

API_KEY = "sk-wBuUIEArjm2BoTQBCQgzf2bhzksx87xg3pQ3cPsvccmULhAk"
BASE_URL = "https://api.sydney-ai.com/v1"  
MODEL_NAME = "gemini-2.5-flash-image-vip"
API_TIMEOUT = 120

# ====================================
# 功能函数
# ====================================

def image_to_base64(image):
    """将PIL图像转换为base64格式"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return "data:image/png;base64," + img_str

def create_polygon_selector_with_clipboard(image_base64, height=750):
    """创建支持自动复制的多边形选择器"""
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                font-family: Arial, sans-serif;
                background: #f0f0f0;
            }}
            .container {{
                max-width: 100%;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            #canvas {{
                border: 2px solid #4CAF50;
                cursor: crosshair;
                display: block;
                margin: 0 auto;
                max-width: 100%;
            }}
            .controls {{
                margin-top: 15px;
                text-align: center;
            }}
            button {{
                padding: 12px 24px;
                margin: 5px;
                font-size: 16px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.3s;
                font-weight: bold;
            }}
            .btn-primary {{
                background: #4CAF50;
                color: white;
            }}
            .btn-primary:hover {{
                background: #45a049;
            }}
            .btn-secondary {{
                background: #f44336;
                color: white;
            }}
            .btn-secondary:hover {{
                background: #da190b;
            }}
            .btn-info {{
                background: #2196F3;
                color: white;
            }}
            .btn-info:hover {{
                background: #0b7dda;
            }}
            .info {{
                margin-top: 10px;
                padding: 12px;
                background: #e3f2fd;
                border-radius: 4px;
                color: #1976d2;
                font-size: 14px;
            }}
            .point-count {{
                margin-top: 10px;
                padding: 8px;
                background: #fff3cd;
                border-radius: 4px;
                color: #856404;
                font-weight: bold;
            }}
            .copy-success {{
                margin-top: 10px;
                padding: 12px;
                background: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
                border-radius: 4px;
                display: none;
                animation: slideDown 0.3s ease-out;
            }}
            @keyframes slideDown {{
                from {{
                    opacity: 0;
                    transform: translateY(-20px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            .highlight {{
                background: #ffc107;
                padding: 2px 6px;
                border-radius: 3px;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <canvas id="canvas"></canvas>
            <div class="point-count" id="pointCount">已选择顶点数: 0</div>
            <div class="controls">
                <button class="btn-secondary" onclick="clearPoints()">🗑️ 清除所有点</button>
                <button class="btn-info" onclick="undoPoint()">↩️ 撤销上一点</button>
                <button class="btn-primary" onclick="confirmMask()">✅ 确认蒙版并复制</button>
            </div>
            <div class="copy-success" id="copySuccess">
                ✅ <span class="highlight">数据已复制到剪贴板！</span><br>
                请在下方点击 <span class="highlight">"⚡ 一键保存"</span> 按钮完成保存
            </div>
            <div class="info">
                <strong>📌 操作流程：</strong><br>
                1️⃣ 点击图片添加多边形顶点（至少3个点）<br>
                2️⃣ 点击"确认蒙版并复制"按钮<br>
                3️⃣ 向下滚动，点击"⚡ 一键保存"按钮
            </div>
        </div>

        <script>
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            const pointCountDiv = document.getElementById('pointCount');
            const copySuccess = document.getElementById('copySuccess');
            let points = [];
            let img = new Image();
            let isImageLoaded = false;
            
            img.onload = function() {{
                const maxWidth = 800;
                const scale = Math.min(maxWidth / img.width, 1);
                canvas.width = img.width * scale;
                canvas.height = img.height * scale;
                
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                
                canvas.dataset.scale = scale;
                canvas.dataset.originalWidth = img.width;
                canvas.dataset.originalHeight = img.height;
                
                isImageLoaded = true;
            }};
            
            img.src = '{image_base64}';
            
            canvas.addEventListener('click', function(e) {{
                if (!isImageLoaded) {{
                    alert('请等待图片加载完成');
                    return;
                }}
                
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                points.push({{x: x, y: y}});
                updatePointCount();
                redraw();
            }});
            
            function updatePointCount() {{
                pointCountDiv.textContent = '已选择顶点数: ' + points.length;
            }}
            
            function redraw() {{
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                
                if (points.length === 0) return;
                
                ctx.beginPath();
                ctx.moveTo(points[0].x, points[0].y);
                
                for (let i = 1; i < points.length; i++) {{
                    ctx.lineTo(points[i].x, points[i].y);
                }}
                
                if (points.length > 2) {{
                    ctx.lineTo(points[0].x, points[0].y);
                    ctx.fillStyle = 'rgba(76, 175, 80, 0.3)';
                    ctx.fill();
                }}
                
                ctx.strokeStyle = '#4CAF50';
                ctx.lineWidth = 3;
                ctx.stroke();
                
                points.forEach((point, index) => {{
                    ctx.beginPath();
                    ctx.arc(point.x, point.y, 6, 0, 2 * Math.PI);
                    ctx.fillStyle = index === 0 ? '#f44336' : '#4CAF50';
                    ctx.fill();
                    ctx.strokeStyle = 'white';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }});
            }}
            
            function clearPoints() {{
                points = [];
                updatePointCount();
                redraw();
                copySuccess.style.display = 'none';
            }}
            
            function undoPoint() {{
                if (points.length > 0) {{
                    points.pop();
                    updatePointCount();
                    redraw();
                }}
            }}
            
            async function confirmMask() {{
                if (points.length < 3) {{
                    alert('❌ 请至少选择3个点来形成一个区域！');
                    return;
                }}
                
                const scale = parseFloat(canvas.dataset.scale);
                const originalPoints = points.map(p => ({{
                    x: Math.round(p.x / scale),
                    y: Math.round(p.y / scale)
                }}));
                
                const jsonString = JSON.stringify(originalPoints);
                
                try {{
                    await navigator.clipboard.writeText(jsonString);
                    copySuccess.style.display = 'block';
                    
                    // 自动滚动到页面底部，让用户看到"一键保存"按钮
                    setTimeout(() => {{
                        window.scrollTo({{
                            top: document.body.scrollHeight,
                            behavior: 'smooth'
                        }});
                    }}, 300);
                    
                }} catch (err) {{
                    alert('⚠️ 自动复制失败: ' + err.message + '\\n\\n请手动复制数据: ' + jsonString);
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    components.html(html_code, height=height, scrolling=True)

def read_clipboard_and_save(page_type):
    """从剪贴板读取数据并保存"""
    # 创建一个用于读取剪贴板的JavaScript代码
    js_code = """
    (async function() {
        try {
            const text = await navigator.clipboard.readText();
            return text;
        } catch (err) {
            return "ERROR:" + err.message;
        }
    })();
    """
    
    # 使用streamlit_js_eval执行JS并获取返回值
    clipboard_data = streamlit_js_eval(js_code, key=f"clipboard_{page_type}_{st.session_state.get('clipboard_counter', 0)}")
    
    return clipboard_data

def create_mask_from_points(image_size, points_json):
    """根据多边形顶点创建蒙版"""
    if not points_json:
        return None
    
    try:
        points = json.loads(points_json)
        if len(points) < 3:
            return None
        
        mask = Image.new('L', image_size, 0)
        draw = ImageDraw.Draw(mask)
        polygon_points = [(p['x'], p['y']) for p in points]
        draw.polygon(polygon_points, fill=255)
        
        return mask
    except Exception as e:
        st.error(f"创建蒙版失败: {e}")
        return None

def resize_reference_to_match_base(ref_image, ref_mask, base_size):
    """将参考图调整为与底图相同的尺寸"""
    resized_ref = ref_image.resize(base_size, Image.Resampling.LANCZOS)
    resized_mask = ref_mask.resize(base_size, Image.Resampling.LANCZOS)
    return resized_ref, resized_mask

def call_api_with_mask(api_key, base_url, model, prompt, base_image_data, mask_data, ref_image_data, ref_mask_data, timeout=API_TIMEOUT):
    """调用API进行局部修改"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    content_list = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": base_image_data}},
        {"type": "image_url", "image_url": {"url": mask_data}},
        {"type": "image_url", "image_url": {"url": ref_image_data}},
        {"type": "image_url", "image_url": {"url": ref_mask_data}}
    ]

    messages = [{"role": "user", "content": content_list}]
    data = {"model": model, "messages": messages, "stream": True}
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
    except requests.exceptions.RequestException as e:
        st.error(f"API请求失败: {e}")
        raise

# ====================================
# Streamlit界面
# ====================================

st.set_page_config(page_title="筑博AI工作室", page_icon="🎨", layout="wide")
st.title("🎨 筑博AI工作室 - 局部修改工具")

# 初始化session state
if 'base_image' not in st.session_state:
    st.session_state.base_image = None
if 'ref_image' not in st.session_state:
    st.session_state.ref_image = None
if 'base_mask_points' not in st.session_state:
    st.session_state.base_mask_points = None
if 'ref_mask_points' not in st.session_state:
    st.session_state.ref_mask_points = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'upload'
if 'clipboard_counter' not in st.session_state:
    st.session_state.clipboard_counter = 0

# 页面路由
if st.session_state.current_page == 'upload':
    st.write("上传底图和参考图，使用多边形套索工具选择需要修改和参考的区域")
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📷 底图（需要修改的图片）")
        base_image_file = st.file_uploader("上传底图", type=["png", "jpg", "jpeg"], key="base")
        
        if base_image_file is not None:
            st.session_state.base_image = Image.open(base_image_file)
        
        if st.session_state.base_image is not None:
            st.image(st.session_state.base_image, caption="底图", use_container_width=True)
            
            if st.button("🎯 选择需要修改的区域", key="btn_base", type="primary"):
                st.session_state.current_page = 'base_mask'
                st.rerun()
            
            if st.session_state.base_mask_points:
                points = json.loads(st.session_state.base_mask_points)
                st.success(f"✅ 底图蒙版已设置（{len(points)}个顶点）")
                if st.button("🔄 重新选择底图区域"):
                    st.session_state.base_mask_points = None
                    st.rerun()

    with col2:
        st.subheader("🎨 参考图")
        ref_image_file = st.file_uploader("上传参考图", type=["png", "jpg", "jpeg"], key="ref")
        
        if ref_image_file is not None:
            st.session_state.ref_image = Image.open(ref_image_file)
        
        if st.session_state.ref_image is not None:
            st.image(st.session_state.ref_image, caption="参考图", use_container_width=True)
            
            if st.button("🎯 选择参考区域", key="btn_ref", type="primary"):
                st.session_state.current_page = 'ref_mask'
                st.rerun()
            
            if st.session_state.ref_mask_points:
                points = json.loads(st.session_state.ref_mask_points)
                st.success(f"✅ 参考图蒙版已设置（{len(points)}个顶点）")
                if st.button("🔄 重新选择参考区域"):
                    st.session_state.ref_mask_points = None
                    st.rerun()

    # 生成部分
    if st.session_state.base_image and st.session_state.ref_image:
        st.markdown("---")
        st.subheader("✍️ 修改说明")
        custom_prompt = st.text_area(
            "描述你想要的修改效果",
            value="请将底图中白色蒙版标记的区域，严格按照参考图中白色蒙版标记区域的风格、材质和细节进行修改。输出图片必须保持底图的原始尺寸和长宽比，只修改蒙版区域内的内容，其他区域完全不变。确保修改后的区域与周围环境自然融合。",
            height=120
        )

        if st.button("🚀 生成修改后的图片", type="primary", 
                    disabled=not (st.session_state.base_mask_points and st.session_state.ref_mask_points)):
            if not st.session_state.base_mask_points or not st.session_state.ref_mask_points:
                st.error("❌ 请为两张图片都设置蒙版区域")
            else:
                with st.spinner("⏳ 正在生成图片，请稍候..."):
                    try:
                        base_mask = create_mask_from_points(
                            st.session_state.base_image.size, 
                            st.session_state.base_mask_points
                        )
                        
                        ref_mask = create_mask_from_points(
                            st.session_state.ref_image.size, 
                            st.session_state.ref_mask_points
                        )
                        
                        if base_mask and ref_mask:
                            ref_image_resized, ref_mask_resized = resize_reference_to_match_base(
                                st.session_state.ref_image,
                                ref_mask,
                                st.session_state.base_image.size
                            )
                            
                            base_image_data = image_to_base64(st.session_state.base_image)
                            base_mask_data = image_to_base64(base_mask)
                            ref_image_data = image_to_base64(ref_image_resized)
                            ref_mask_data = image_to_base64(ref_mask_resized)
                            
                            result_content = call_api_with_mask(
                                api_key=API_KEY, base_url=BASE_URL, model=MODEL_NAME,
                                prompt=custom_prompt, base_image_data=base_image_data,
                                mask_data=base_mask_data, ref_image_data=ref_image_data,
                                ref_mask_data=ref_mask_data
                            )
                            
                            if "![image](" in result_content:
                                start_idx = result_content.index("![image](") + len("![image](")
                                end_idx = result_content.index(")", start_idx)
                                image_url = result_content[start_idx:end_idx]
                                
                                st.success("✅ 图片生成成功！")
                                st.image(image_url, caption="修改后的图片", use_container_width=True)
                                st.markdown(f"[📥 下载图片]({image_url})")
                            else:
                                st.warning("⚠️ 未能从响应中提取图片")
                                st.write("API响应:", result_content)
                    except Exception as e:
                        st.error(f"❌ 生成失败: {e}")

elif st.session_state.current_page == 'base_mask':
    st.subheader("🖱️ 底图蒙版选择")
    
    if st.session_state.base_image:
        base_image_b64 = image_to_base64(st.session_state.base_image)
        create_polygon_selector_with_clipboard(base_image_b64)
        
        st.markdown("---")
        st.info("⬆️ 请先在上方画布完成蒙版绘制并点击'确认蒙版并复制'，然后点击下方的'⚡ 一键保存'按钮")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⚡ 一键保存（自动读取剪贴板）", type="primary", use_container_width=True, key="auto_save_base"):
                # 增加计数器以触发新的剪贴板读取
                st.session_state.clipboard_counter += 1
                
                with st.spinner("🔄 正在从剪贴板读取数据..."):
                    clipboard_data = read_clipboard_and_save('base')
                    
                    if clipboard_data and not clipboard_data.startswith("ERROR:"):
                        try:
                            points = json.loads(clipboard_data)
                            if len(points) >= 3:
                                st.session_state.base_mask_points = clipboard_data
                                st.success(f"✅ 已自动保存{len(points)}个顶点！正在返回...")
                                st.balloons()
                                st.session_state.current_page = 'upload'
                                st.rerun()
                            else:
                                st.error("❌ 剪贴板数据无效：至少需要3个顶点")
                        except json.JSONDecodeError:
                            st.error(f"❌ 剪贴板数据格式错误\n\n数据内容: {clipboard_data[:200]}")
                    elif clipboard_data and clipboard_data.startswith("ERROR:"):
                        st.error(f"❌ 读取剪贴板失败: {clipboard_data[6:]}\n\n💡 请确保在画布上点击了'确认蒙版并复制'按钮")
                    else:
                        st.warning("⚠️ 剪贴板为空或无法读取\n\n💡 请先在上方画布点击'确认蒙版并复制'")
        
        with col2:
            if st.button("🔙 返回", use_container_width=True):
                st.session_state.current_page = 'upload'
                st.rerun()

elif st.session_state.current_page == 'ref_mask':
    st.subheader("🖱️ 参考图蒙版选择")
    
    if st.session_state.ref_image:
        ref_image_b64 = image_to_base64(st.session_state.ref_image)
        create_polygon_selector_with_clipboard(ref_image_b64)
        
        st.markdown("---")
        st.info("⬆️ 请先在上方画布完成蒙版绘制并点击'确认蒙版并复制'，然后点击下方的'⚡ 一键保存'按钮")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⚡ 一键保存（自动读取剪贴板）", type="primary", use_container_width=True, key="auto_save_ref"):
                st.session_state.clipboard_counter += 1
                
                with st.spinner("🔄 正在从剪贴板读取数据..."):
                    clipboard_data = read_clipboard_and_save('ref')
                    
                    if clipboard_data and not clipboard_data.startswith("ERROR:"):
                        try:
                            points = json.loads(clipboard_data)
                            if len(points) >= 3:
                                st.session_state.ref_mask_points = clipboard_data
                                st.success(f"✅ 已自动保存{len(points)}个顶点！正在返回...")
                                st.balloons()
                                st.session_state.current_page = 'upload'
                                st.rerun()
                            else:
                                st.error("❌ 剪贴板数据无效：至少需要3个顶点")
                        except json.JSONDecodeError:
                            st.error(f"❌ 剪贴板数据格式错误\n\n数据内容: {clipboard_data[:200]}")
                    elif clipboard_data and clipboard_data.startswith("ERROR:"):
                        st.error(f"❌ 读取剪贴板失败: {clipboard_data[6:]}\n\n💡 请确保在画布上点击了'确认蒙版并复制'按钮")
                    else:
                        st.warning("⚠️ 剪贴板为空或无法读取\n\n💡 请先在上方画布点击'确认蒙版并复制'")
        
        with col2:
            if st.button("🔙 返回", use_container_width=True):
                st.session_state.current_page = 'upload'
                st.rerun()

# 使用说明
with st.expander("📖 使用说明"):
    st.markdown("""
    ### ⚡ 最新操作流程（超简化版）：
    
    1. **上传底图和参考图**
    2. **底图蒙版选择**：
       - 点击"选择需要修改的区域"
       - 在图片上添加顶点（至少3个点）
       - 点击 "✅ 确认蒙版并复制"
       - 点击 "⚡ 一键保存" → **自动完成读取+验证+保存+跳转**
    3. **参考图蒙版选择** - 重复上述步骤
    4. **生成图片**
    
    ### 🎯 核心改进：
    - ✅ **真正的一键操作**：点击"一键保存"自动从剪贴板读取数据
    - ✅ **零手动输入**：无需粘贴，无需输入框
    - ✅ **自动验证**：自动检查数据有效性
    - ✅ **自动跳转**：保存成功后自动返回主页
    - ✅ **智能提示**：清晰的操作引导和错误提示
    
    ### 🚀 用户操作仅需2步：
    1. 点击"确认蒙版并复制" 
    2. 点击"一键保存"（完成所有后续操作）
    """)
