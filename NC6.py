import streamlit as st
import base64
from PIL import Image
import io
import json
import time

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="全自动图像区域标注系统",
    page_icon="🖼️",
    layout="wide"
)

# ==================== 初始化 Session State ====================
if 'polygon_data' not in st.session_state:
    st.session_state.polygon_data = None
if 'image_data' not in st.session_state:
    st.session_state.image_data = None
if 'check_data' not in st.session_state:
    st.session_state.check_data = False

# ==================== 核心函数 ====================

def create_polygon_selector_auto(image_b64):
    """全自动多边形选择器 - 无需手动复制粘贴"""
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                padding: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #0e1117;
                color: white;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            #canvas {{
                border: 3px solid #4CAF50;
                cursor: crosshair;
                display: block;
                margin: 20px auto;
                background: white;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                border-radius: 8px;
            }}
            .controls {{
                text-align: center;
                margin: 25px 0;
            }}
            button {{
                padding: 14px 35px;
                margin: 0 12px;
                font-size: 17px;
                font-weight: 600;
                cursor: pointer;
                border: none;
                border-radius: 8px;
                transition: all 0.3s ease;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }}
            button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            }}
            button:active {{
                transform: translateY(0);
            }}
            #confirmBtn {{
                background: linear-gradient(135deg, #4CAF50, #45a049);
                color: white;
            }}
            #confirmBtn:disabled {{
                background: #666;
                cursor: not-allowed;
                transform: none;
            }}
            #clearBtn {{
                background: linear-gradient(135deg, #f44336, #da190b);
                color: white;
            }}
            #status {{
                text-align: center;
                margin: 20px 0;
                font-size: 18px;
                min-height: 30px;
                font-weight: 600;
                padding: 12px;
                border-radius: 8px;
                background: rgba(255,255,255,0.1);
            }}
            .success {{
                background: rgba(76, 175, 80, 0.2) !important;
                color: #4CAF50 !important;
                border: 2px solid #4CAF50;
            }}
            .info {{
                color: #2196F3;
                border: 2px solid rgba(33, 150, 243, 0.3);
            }}
            .error {{
                background: rgba(244, 67, 54, 0.2) !important;
                color: #f44336 !important;
                border: 2px solid #f44336;
            }}
            .point-info {{
                text-align: center;
                color: #aaa;
                margin-top: 10px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div id="status" class="info">🖱️ 在图片上点击绘制多边形顶点（至少3个点）</div>
            <canvas id="canvas"></canvas>
            <div class="point-info">
                已标注 <span id="pointCount">0</span> 个点 | 
                <span style="color: #ff0000;">●</span> 红色为起点 | 
                <span style="color: #4CAF50;">●</span> 绿色为其他顶点
            </div>
            <div class="controls">
                <button id="confirmBtn">✓ 确认选区（自动保存）</button>
                <button id="clearBtn">✗ 清除重画</button>
            </div>
        </div>

        <script>
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            const status = document.getElementById('status');
            const pointCount = document.getElementById('pointCount');
            const confirmBtn = document.getElementById('confirmBtn');
            const clearBtn = document.getElementById('clearBtn');
            
            let points = [];
            const img = new Image();
            
            // 加载图片
            img.onload = function() {{
                const scale = Math.min(800 / img.width, 600 / img.height, 1);
                canvas.width = img.width * scale;
                canvas.height = img.height * scale;
                redraw();
            }};
            
            img.src = 'data:image/png;base64,{image_b64}';
            
            // 重绘画布
            function redraw() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                
                if (points.length > 0) {{
                    // 绘制多边形
                    ctx.beginPath();
                    ctx.moveTo(points[0].x, points[0].y);
                    for (let i = 1; i < points.length; i++) {{
                        ctx.lineTo(points[i].x, points[i].y);
                    }}
                    ctx.closePath();
                    ctx.strokeStyle = '#4CAF50';
                    ctx.lineWidth = 3;
                    ctx.stroke();
                    ctx.fillStyle = 'rgba(76, 175, 80, 0.25)';
                    ctx.fill();
                    
                    // 绘制顶点
                    points.forEach((point, index) => {{
                        ctx.beginPath();
                        ctx.arc(point.x, point.y, 6, 0, 2 * Math.PI);
                        ctx.fillStyle = index === 0 ? '#ff0000' : '#4CAF50';
                        ctx.fill();
                        ctx.strokeStyle = 'white';
                        ctx.lineWidth = 2;
                        ctx.stroke();
                    }});
                }}
            }}
            
            // 点击添加顶点
            canvas.addEventListener('click', function(e) {{
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                points.push({{x: x, y: y}});
                pointCount.textContent = points.length;
                redraw();
                
                if (points.length >= 3) {{
                    status.textContent = `✓ 已添加 ${{points.length}} 个点，可以确认了`;
                    status.className = 'info';
                }} else {{
                    status.textContent = `已添加 ${{points.length}} 个点，还需要 ${{3 - points.length}} 个点`;
                    status.className = 'info';
                }}
            }});
            
            // 确认按钮
            confirmBtn.addEventListener('click', function() {{
                if (points.length < 3) {{
                    status.textContent = '❌ 至少需要3个点才能形成区域！';
                    status.className = 'error';
                    return;
                }}
                
                confirmBtn.disabled = true;
                
                // 归一化坐标（相对于图片尺寸）
                const normalizedPoints = points.map(p => ({{
                    x: Math.round((p.x / canvas.width) * 10000) / 10000,
                    y: Math.round((p.y / canvas.height) * 10000) / 10000
                }}));
                
                const jsonData = JSON.stringify(normalizedPoints);
                
                // 方法1: localStorage (主要方法)
                try {{
                    localStorage.setItem('streamlit_polygon_data', jsonData);
                    localStorage.setItem('streamlit_data_timestamp', Date.now().toString());
                }} catch(e) {{
                    console.error('localStorage error:', e);
                }}
                
                // 方法2: postMessage (备用方法)
                try {{
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        value: jsonData
                    }}, '*');
                }} catch(e) {{
                    console.error('postMessage error:', e);
                }}
                
                status.textContent = '✓ 数据已保存！页面即将刷新...';
                status.className = 'success';
                
                // 延迟后触发刷新
                setTimeout(() => {{
                    try {{
                        window.parent.postMessage({{
                            type: 'streamlit:setComponentValue',
                            value: 'REFRESH_TRIGGER'
                        }}, '*');
                    }} catch(e) {{}}
                    
                    // 强制标记需要刷新
                    localStorage.setItem('streamlit_need_refresh', 'true');
                }}, 800);
            }});
            
            // 清除按钮
            clearBtn.addEventListener('click', function() {{
                points = [];
                pointCount.textContent = '0';
                redraw();
                status.textContent = '🖱️ 画布已清除，重新开始绘制';
                status.className = 'info';
                confirmBtn.disabled = false;
            }});
        </script>
    </body>
    </html>
    """
    
    return html_code


def create_data_reader():
    """创建隐藏的数据读取器"""
    reader_html = """
    <script>
        try {
            const data = localStorage.getItem('streamlit_polygon_data');
            const needRefresh = localStorage.getItem('streamlit_need_refresh');
            
            if (data && needRefresh === 'true') {
                // 发送数据给 Streamlit
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: data
                }, '*');
                
                // 清除标记
                localStorage.removeItem('streamlit_need_refresh');
            }
        } catch(e) {
            console.error('Reader error:', e);
        }
    </script>
    """
    return reader_html


# ==================== 主界面 ====================

st.title("🖼️ 全自动图像区域标注系统")
st.markdown("---")

# 侧边栏
with st.sidebar:
    st.header("📋 使用说明")
    st.markdown("""
    **操作步骤：**
    1. 📤 上传图片
    2. 🖱️ 在图片上点击标注顶点
    3. ✅ 点击"确认选区"
    4. 🎉 数据自动保存！
    
    **注意事项：**
    - 至少需要标注3个点
    - 红色点为起点
    - 绿色点为其他顶点
    """)
    
    if st.session_state.polygon_data:
        st.success("✅ 当前已有数据")
        if st.button("🗑️ 清除数据"):
            st.session_state.polygon_data = None
            st.rerun()

# 主内容区
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📤 上传图片")
    uploaded_file = st.file_uploader(
        "选择图片文件",
        type=['png', 'jpg', 'jpeg', 'bmp'],
        help="支持 PNG、JPG、JPEG、BMP 格式"
    )

if uploaded_file:
    # 转换图片为 base64
    image = Image.open(uploaded_file)
    st.session_state.image_data = image
    
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()
    
    with col1:
        st.markdown("### 📍 标注区域")
        st.info("💡 在下方图片上点击绘制多边形，完成后点击'确认选区'，数据会自动保存")
        
        # 显示标注器
        from streamlit.components.v1 import html
        html_content = create_polygon_selector_auto(img_b64)
        component_value = html(html_content, height=800)
        
        # 检查返回值
        if component_value:
            if component_value == 'REFRESH_TRIGGER':
                st.session_state.check_data = True
                st.rerun()
            else:
                try:
                    polygon_data = json.loads(component_value)
                    if isinstance(polygon_data, list) and len(polygon_data) >= 3:
                        st.session_state.polygon_data = polygon_data
                        st.success("✅ 数据接收成功！")
                        st.rerun()
                except:
                    pass
    
    # 隐藏的数据读取器
    reader_value = html(create_data_reader(), height=0)
    if reader_value:
        try:
            polygon_data = json.loads(reader_value)
            if isinstance(polygon_data, list) and len(polygon_data) >= 3:
                st.session_state.polygon_data = polygon_data
                st.rerun()
        except:
            pass
    
    # 检查数据标记
    if st.session_state.check_data:
        st.session_state.check_data = False
        time.sleep(0.5)
        st.rerun()
    
    with col2:
        st.markdown("### 📊 标注数据")
        
        if st.session_state.polygon_data:
            st.success(f"✅ 已标注 {len(st.session_state.polygon_data)} 个顶点")
            
            # 显示数据
            with st.expander("查看坐标数据", expanded=True):
                st.json(st.session_state.polygon_data)
            
            # 下载按钮
            json_str = json.dumps(st.session_state.polygon_data, indent=2)
            st.download_button(
                label="📥 下载 JSON 文件",
                data=json_str,
                file_name=f"polygon_mask_{uploaded_file.name.split('.')[0]}.json",
                mime="application/json",
                use_container_width=True
            )
            
            # 可视化预览
            st.markdown("#### 🔍 坐标预览")
            for i, point in enumerate(st.session_state.polygon_data):
                st.text(f"点 {i+1}: ({point['x']:.4f}, {point['y']:.4f})")
        else:
            st.info("⏳ 等待标注数据...")
            st.markdown("标注完成后点击**确认选区**按钮")

else:
    st.info("👆 请先在左侧上传一张图片开始标注")

# 页脚
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "🎨 全自动图像标注系统 | 基于 Streamlit 框架"
    "</div>",
    unsafe_allow_html=True
)
