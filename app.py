import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json

# ==========================================
# 1. Page Configuration
# ==========================================
st.set_page_config(
    page_title="차량 및 장구류 점검 | Data Intel PRO",
    page_icon="🚔",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 사이드바에 배포 가이드라인 추가
with st.sidebar:
    st.markdown("## 🚀 앱 배포 가이드")
    st.info("**Streamlit Community Cloud 배포 (무료/가장 쉬움)**")
    st.markdown("""
    1. 현재 작업 폴더(`차량 및 장구류 점검`)를 **GitHub Repository**에 업로드(Push)합니다.
    2. [Streamlit Community Cloud](https://share.streamlit.io)에 로그인합니다.
    3. 우측 상단 **[New app]** 버튼을 클릭합니다.
    4. 방금 만든 GitHub Repository를 선택합니다.
    5. Main file path에 `app.py`를 입력합니다.
    6. **[Deploy]** 버튼을 누르면 약 1~2분 뒤 URL이 생성되며 스마트폰에서 즉시 접속 가능합니다.
    """)
    st.divider()
    st.success("✅ `requirements.txt`가 폴더 안에 이미 준비되어 있어 추가 설정 없이 바로 배포됩니다.")

# ==========================================
# 2. Inject Custom CSS (Data Intel PRO Style)
# ==========================================
def load_css():
    css_file = os.path.join(os.path.dirname(__file__), "ui", "style.css")
    if os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
            
load_css()

# ==========================================
# 3. State Management & Helper Functions
# ==========================================
# 점검 항목 리스트
CHECK_ITEMS = {
    "기동 차량 점검": [
        {"id": "c1", "title": "경광등 및 사이렌 작동", "desc": "점등 및 출력 소음 상태 확인"},
        {"id": "c2", "title": "블랙박스 녹화 상태", "desc": "SD카드 인식 및 각도 확인"}
    ],
    "경비 장구류 및 옵션": [
        {"id": "e1", "title": "가스총(가스발사총)", "desc": "약제 유효기간 및 트리거 확인"},
        {"id": "e2", "title": "휴대용 무전기(TRS)", "desc": "채널 고정 및 안테나 파손 여부"},
        {"id": "e3", "title": "비상 구급함/소화기", "desc": "비치 품목 및 압력 확인"}
    ]
}

# 모든 항목 초기 상태 "정상"
for category, items in CHECK_ITEMS.items():
    for item in items:
        if item["id"] not in st.session_state:
            st.session_state[item["id"]] = "정상"

def get_status_counts():
    ok_count = 0
    ng_count = 0
    for category, items in CHECK_ITEMS.items():
        for item in items:
            val = st.session_state.get(item["id"], "정상")
            if val == "정상":
                ok_count += 1
            else:
                ng_count += 1
    return ok_count, ng_count

# ==========================================
# 4. Custom Navigation Bar (Simulated)
# ==========================================
today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
st.markdown(f"""
    <div class="nav-bar-custom">
        <h1>본부 지사 점검 시스템</h1>
        <span>{today_str}</span>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 5. Dashboard Metrics
# ==========================================
ok_count, ng_count = get_status_counts()
total_count = ok_count + ng_count

m1, m2, m3 = st.columns(3)
with m1:
    st.metric(label="금일 점검", value=f"{total_count}건")
with m2:
    st.metric(label="정비대상 (불량)", value=f"{ng_count}건", delta="-조치필요" if ng_count > 0 else None, delta_color="inverse")
with m3:
    st.metric(label="정상기동", value=f"{ok_count}건", delta="양호" if ok_count == total_count else None)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 6. Main Form container
# ==========================================
with st.container(border=True):
    st.markdown("### 📋 현장 기본 정보")
    c1, c2 = st.columns(2)
    with c1:
        car_num = st.text_input("차량 번호", value="222허9550")
    with c2:
        branch = st.selectbox("방문 지사", options=["강남지사", "인천지사", "부산지사", "본부"])
    
    mileage = st.number_input("누적 주행거리 (km)", value=139848, step=1)

# ==========================================
# 7. Inspection Checklist
# ==========================================
for category, items in CHECK_ITEMS.items():
    st.markdown(f"### 🛠️ {category}")
    with st.container(border=True):
        for item in items:
            st.markdown(f"""
            <div class="check-row-container">
                <div style="font-weight: 600; font-size: 1.05rem; color: #1e293b;">{item['title']}</div>
                <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 8px;">{item['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
            # Use radio for status selection
            st.radio(
                label="상태",
                options=["정상", "불량"],
                key=item["id"],
                horizontal=True,
                label_visibility="collapsed"
            )
            st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 8. Photos & Memo
# ==========================================
with st.container(border=True):
    st.markdown("### 📸 현장 증빙 사진")
    st.info("카메라로 즉시 촬영하거나 갤러리에서 사진을 업로드하세요.")
    cam_col, up_col = st.columns(2)
    with cam_col:
        cam_photo = st.camera_input("실시간 촬영", label_visibility="collapsed")
    with up_col:
        uploaded_files = st.file_uploader("파일 업로드", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

    if cam_photo or uploaded_files:
        st.markdown("#### 미리보기")
        cols = st.columns(3)
        idx = 0
        if cam_photo:
            cols[idx % 3].image(cam_photo, use_container_width=True)
            idx += 1
        if uploaded_files:
            for file in uploaded_files:
                cols[idx % 3].image(file, use_container_width=True)
                idx += 1

with st.container(border=True):
    st.markdown("### 📝 종합 의견")
    memo = st.text_area("특이사항 기록", placeholder="차량 외관 스크래치, 타이어 마모 상태 등 특이사항을 입력해주세요.", height=100)

# ==========================================
# 9. Submit Action
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)
submit_btn = st.button("🚀 점검 완료 및 데이터 전송", use_container_width=True, type="primary")

if submit_btn:
    # 1. Validation
    if not car_num.strip():
        st.error("⚠️ 차량 번호를 입력해주세요.")
    else:
        # 2. Compile Data
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "car_num": car_num,
            "branch": branch,
            "mileage": mileage,
            "total_count": total_count,
            "ok_count": ok_count,
            "ng_count": ng_count,
            "memo": memo,
            "checks": {item["id"]: st.session_state[item["id"]] for cat, items in CHECK_ITEMS.items() for item in items}
        }
        
        # 3. Simulate Save
        save_dir = os.path.expanduser("~/.dataintelligence_pro/inspections")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"report_{car_num}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
        
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=4)
            
        # 4. Feedback
        st.success(f"✅ {car_num} ({branch}) 점검 데이터가 성공적으로 전송되었습니다!")
        st.balloons()
