# -*- coding: utf-8 -*-
import os, io, time, json, base64, re
import httpx
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components
st.set_page_config(page_title="筑博AI工作室ZHUAI内测002", layout="centered")
# ===================== 仅保留这三行配置 =====================
API_KEY    = "sk-wBuUIEArjm2BoTQBCQgzf2bhzksx87xg3pQ3cPsvccmULhAk"
BASE_URL   = "https://api.sydney-ai.com/v1"
MODEL_NAME = "veo3"
# ===========================================================
# 固定默认参数（不暴露UI）
DEFAULT_DURATION = 10
DEFAULT_FPS = 24
DEFAULT_W, DEFAULT_H = 1920, 1080
# ——判断使用哪种后端：Cherry(异步) 或 Chat Completions(同步)——
def is_cherry_backend(base_url: str) -> bool:
    return "cherry" in base_url.lower()
# ——运镜提示词（建筑向）——
def build_motion_prompts(duration, fps, width, height):
    base_params = f"""
Technical Parameters:
- Duration: {duration} seconds
- Frame rate: {fps} fps  
- Resolution: {width}x{height} (aesthetic constraint only)
- Motion curve: ease-in-out
- Movement: smooth, no shake or jitter
Scene Requirements:
- Maintain strict two-point perspective with vertical lines perfectly straight
- No camera roll/tilt on vertical axis
- Preserve original image's materials, proportions, and lighting
- Allow subtle parallax motion in foreground/midground/background (pedestrians, tree leaves, flags, water surfaces may have slight motion)
Output: Generate an online-accessible video (mp4 or m3u8), with thumbnail/poster if available.
"""
    
    return {
        "前进推进（Dolly-In）": f"""{base_params}
CAMERA MOVEMENT: DOLLY-IN / PUSH-IN
- Camera physically moves FORWARD along the perpendicular axis toward the building subject
- Movement distance: 10%-20% closer to subject
- Keep subject centered within ±5% of frame center
- Maintain horizon line stability
- NO camera rotation, NO zoom
- Start frame: original image composition
- End frame: closer view of the building
""",
        "后退拉远（Dolly-Out）": f"""{base_params}
CAMERA MOVEMENT: DOLLY-OUT / PULL-BACK
- Camera physically moves BACKWARD away from the building subject
- Movement distance: 10%-20% farther from subject
- Keep subject centered within ±5% of frame center
- Maintain horizon line stability
- NO camera rotation, NO zoom
- Start frame: original image composition
- End frame: wider view with building appearing smaller
- CRITICAL: This is a physical camera pullback motion, NOT a zoom-out effect
""",
        "左转平摇（Pan Left）": f"""{base_params}
CAMERA MOVEMENT: PAN LEFT
- Camera position is FIXED (no physical movement)
- Camera ROTATES horizontally to the LEFT by 8°-15°
- Rotation pivot: camera position (not building)
- Building subject remains visible in frame throughout
- NO vertical movement, NO camera roll
- Maintain constant camera height
""",
        "右转平摇（Pan Right）": f"""{base_params}
CAMERA MOVEMENT: PAN RIGHT
- Camera position is FIXED (no physical movement)
- Camera ROTATES horizontally to the RIGHT by 8°-15°
- Rotation pivot: camera position (not building)
- Building subject remains visible in frame throughout
- NO vertical movement, NO camera roll
- Maintain constant camera height
""",
        "左侧环绕（Orbit Left）": f"""{base_params}
CAMERA MOVEMENT: ORBIT LEFT (COUNTERCLOCKWISE)
- Camera moves in a CIRCULAR path COUNTERCLOCKWISE around the building
- Orbit radius: 3-8 meters from building center
- Camera height: constant throughout movement
- Camera continuously ROTATES to keep building centered in frame (truck left + pan right)
- Arc angle: approximately 15°-30°
- Smooth orbital trajectory with uniform angular velocity
- NO vertical movement
""",
        "右侧环绕（Orbit Right）": f"""{base_params}
CAMERA MOVEMENT: ORBIT RIGHT (CLOCKWISE)
- Camera moves in a CIRCULAR path CLOCKWISE around the building
- Orbit radius: 3-8 meters from building center
- Camera height: constant throughout movement
- Camera continuously ROTATES to keep building centered in frame (truck right + pan left)
- Arc angle: approximately 15°-30°
- Smooth orbital trajectory with uniform angular velocity
- NO vertical movement
""",
        "升降俯仰（Crane + Tilt）": f"""{base_params}
CAMERA MOVEMENT: CRANE UP/DOWN + TILT
- Camera position moves VERTICALLY (up or down) by approximately 2 meters
- Simultaneously adjust tilt angle to compensate (total tilt change ≤8°)
- Maintain building subject in center region of frame
- If crane up: slight tilt down; if crane down: slight tilt up
- NO horizontal movement, NO camera roll
- Avoid wide-angle distortion
- Smooth coordinated movement
""",
        "推拉变焦（Dolly Zoom）": f"""{base_params}
CAMERA MOVEMENT: DOLLY ZOOM (VERTIGO EFFECT / ZOLLY)
- SIMULTANEOUSLY:
  * Camera physically moves FORWARD while focal length DECREASES (zoom out)
  OR
  * Camera physically moves BACKWARD while focal length INCREASES (zoom in)
- Effect: Background perspective changes subtly while subject size remains relatively constant
- Zoom magnitude: ≤10% to avoid disorientation
- Maintain subject in frame center
- Smooth coordinated dolly and zoom movement
- This creates the characteristic "Vertigo" effect where background appears to compress or expand
"""
    }
PROMPT_OPTIONS = build_motion_prompts(DEFAULT_DURATION, DEFAULT_FPS, DEFAULT_W, DEFAULT_H)
# ——工具：压缩图片为 data URL（减小请求体，更稳）——
def compress_to_data_url(uploaded_file, max_side=1280, quality=85):
    img = Image.open(uploaded_file).convert("RGB")
    w, h = img.size
    scale = min(1.0, float(max_side) / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}", (w, h)
def infer_orientation(width, height):
    return "portrait" if height >= width else "landscape"
# ——同步后端（/v1/chat/completions）兜底解析视频链接——
URL_RE = re.compile(r'https?://[^\s\)\'"]+', re.IGNORECASE)
def parse_video_info_from_text(text: str):
    for blk in re.findall(r'\{[\s\S]*?\}', text):
        try:
            obj = json.loads(blk)
            if "video_url" in obj:
                return obj.get("video_url"), obj.get("thumbnail_url")
        except:
            pass
    v, t = None, None
    urls = URL_RE.findall(text)
    for u in urls:
        if any(u.lower().endswith(ext) for ext in [".mp4", ".webm"]) or ".m3u8" in u.lower():
            v = u; break
    for u in urls:
        if any(u.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            t = u; break
    return v, t
# ================= Cherry 异步：提交 + 轮询 =================
def cherry_submit(prompt: str, image_data_url: str, orientation: str) -> str:
    submit_ep = f"{BASE_URL.rstrip('/')}/v1/vision/generate"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "prompt": prompt,
        "orientation": orientation,
        "image": image_data_url,
    }
    with httpx.Client(http2=False, timeout=httpx.Timeout(15.0, read=60.0, write=60.0)) as client:
        r = client.post(submit_ep, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    task_id = data.get("task_id") or data.get("id")
    if not task_id:
        raise RuntimeError(f"提交成功但未返回 task_id，原始响应：{json.dumps(data, ensure_ascii=False)}")
    return task_id
def cherry_poll(task_id: str, max_wait=600, interval=2.5, status_placeholder=None):
    status_ep = f"{BASE_URL.rstrip('/')}/v1/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}
    last_pct = 0
    deadline = time.time() + max_wait
    dot_count = 0
    
    while time.time() < deadline:
        with httpx.Client(http2=False, timeout=httpx.Timeout(10.0, read=20.0)) as client:
            r = client.get(status_ep, headers=headers)
            if r.status_code not in (200, 202):
                r.raise_for_status()
            data = r.json()
        status = (data.get("status") or data.get("state") or "").lower()
        pct = data.get("progress") or data.get("pct") or last_pct
        try: pct = int(pct)
        except: pct = last_pct
        last_pct = pct
        
        # 更新动态文字
        dots = "." * ((dot_count % 4) + 1)
        if status_placeholder:
            status_placeholder.markdown(f"🎬 **视频生成中{dots}** ({pct}%)")
        dot_count += 1
        
        video_url = (data.get("video_url") or
                     (data.get("result") or {}).get("url") or
                     (data.get("data") or {}).get("url") or
                     (data.get("output") or {}).get("video_url"))
        thumb_url = (data.get("thumbnail_url") or
                     (data.get("result") or {}).get("thumbnail") or
                     (data.get("data") or {}).get("thumbnail"))
        if status in ("done", "completed", "success", "succeeded", "finished"):
            return video_url, thumb_url, data
        if status in ("failed", "error"):
            raise RuntimeError(f"任务失败：{json.dumps(data, ensure_ascii=False)}")
        time.sleep(interval)
    raise TimeoutError(f"任务轮询超时（{max_wait}s），task_id={task_id}")
# ================= Chat Completions 同步兜底 =================
def chat_completions_image2video(messages, image_data, status_placeholder=None):
    url = f"{BASE_URL.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MODEL_NAME, "messages": messages, "image": image_data, "task": "image_to_video", "stream": False}
    
    if status_placeholder:
        dot_count = 0
        for i in range(10):
            dots = "." * ((dot_count % 4) + 1)
            status_placeholder.markdown(f"🎬 **视频生成中{dots}**")
            dot_count += 1
            time.sleep(0.5)
    
    with httpx.Client(http2=False, timeout=httpx.Timeout(30.0, read=180.0, write=180.0)) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "") or json.dumps(data, ensure_ascii=False)
    return parse_video_info_from_text(text), data
# ============================ UI ============================
st.title("筑博AI工作室ZHUAI内测002")
st.caption("上传建筑静帧 → 选择运镜 → 一键生成")
uploaded = st.file_uploader("上传图片（建议 1 张；仅取第1张参与生成）", type=["png","jpg","jpeg"], accept_multiple_files=True)
if uploaded:
    st.image(uploaded[0], caption="基准图（以此图构图/光照为准）", use_container_width=True)
motion_key = st.selectbox("运镜方式", list(PROMPT_OPTIONS.keys()))
prompt_text = PROMPT_OPTIONS[motion_key]
# 使用 session_state 来控制按钮状态
if 'generating' not in st.session_state:
    st.session_state.generating = False
# 创建按钮（根据状态显示不同样式）
button_disabled = st.session_state.generating
if st.button("生成视频", type="primary", disabled=button_disabled):
    if not uploaded:
        st.error("请先上传至少 1 张图片")
        st.stop()
    
    # 设置生成状态为 True
    st.session_state.generating = True
    
    # 创建状态显示占位符
    status_placeholder = st.empty()
    status_placeholder.markdown("🎬 **视频生成中.**")
    
    data_url, (w, h) = compress_to_data_url(uploaded[0], max_side=1280, quality=85)
    orientation = infer_orientation(w, h)
    try:
        if is_cherry_backend(BASE_URL):
            # ——Cherry 异步流程——
            with st.status("🚀 提交任务中…", expanded=True) as s:
                try:
                    task_id = cherry_submit(prompt_text, data_url, orientation)
                    s.update(label=f"✅ 提交成功：task_id={task_id}", state="complete")
                except Exception as e:
                    status_placeholder.empty()
                    st.session_state.generating = False
                    st.error(f"提交失败：{e}")
                    st.stop()
            
            st.link_button("异步数据预览", f"https://asyncdata.net/web/{task_id}", type="secondary")
            
            try:
                video_url, thumb_url, raw = cherry_poll(task_id, status_placeholder=status_placeholder)
            except Exception as e:
                status_placeholder.empty()
                st.session_state.generating = False
                st.error(f"轮询失败：{e}")
                st.stop()
        else:
            # ——Chat Completions 同步兜底——
            contents = [{"type": "text", "text": prompt_text}]
            image_data = [{"type": "image_url", "image_url": {"url": data_url}}]
            messages = [{"role": "user", "content": contents + image_data}]
            try:
                (video_url, thumb_url), raw = chat_completions_image2video(messages, image_data, status_placeholder)
            except Exception as e:
                status_placeholder.empty()
                st.session_state.generating = False
                st.error(f"请求失败：{e}")
                st.stop()
        # 清除状态文字
        status_placeholder.empty()
        
        if not video_url:
            st.session_state.generating = False
            st.error("生成完成但未拿到视频 URL。原始数据：")
            st.code(json.dumps(raw, ensure_ascii=False, indent=2))
            st.stop()
        st.success("🎉 视频已生成！点击下方播放或复制链接：")
        st.code(video_url)
        if thumb_url:
            html = f"""
            <video width="100%" height="auto" controls preload="none" poster="{thumb_url}">
                <source src="{video_url}" type="video/mp4">
                <source src="{video_url}" type="application/x-mpegURL">
                您的浏览器不支持 HTML5 视频播放。
            </video>
            """
            components.html(html, height=540)
            st.markdown(f"[![点击播放]({thumb_url})]({video_url})")
        else:
            st.video(video_url)
        
        # 重置生成状态
        st.session_state.generating = False
        
    except Exception as e:
        status_placeholder.empty()
        st.session_state.generating = False
        st.error(f"发生错误：{e}")