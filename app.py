import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json
import io

# ==========================================
# 1. Page Configuration
# ==========================================
st.set_page_config(
    page_title="차량 및 장구류 점검 | Data Intel PRO",
    page_icon="🚔",
    layout="wide", # 넓은 화면 사용
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. Settings & Constants
# ==========================================
DATA_DIR = os.path.expanduser("~/.dataintelligence_pro/inspections")
DB_DIR = os.path.expanduser("~/.dataintelligence_pro/db")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

BRANCHES = ["중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"]

CHECK_ITEMS = {
    "기동 차량 점검": [
        {
            "id": "c1", 
            "title": "차량외부: 파손(도장) 및 Ci/BI상태 등", 
            "desc": "외관 스크래치, 파손, 랩핑 상태 확인", 
            "detail": "1. 차량의 전/후/좌/우 외관 스크래치 및 찌그러짐 점검\n2. 회사 로고(Ci/BI) 랩핑 훼손 여부 확인\n3. 타이어 마모도 및 휠 파손 여부 육안 확인"
        },
        {
            "id": "c2", 
            "title": "경광등 및 사이렌 작동", 
            "desc": "점등 및 출력 소음 상태 확인", 
            "detail": "1. 경광등 스위치 작동 시 전체 LED 정상 점등 확인\n2. 사이렌 작동 시 출력음이 정상적으로 발생하는지 테스트"
        },
        {
            "id": "c3", 
            "title": "블랙박스 녹화 상태", 
            "desc": "SD카드 인식 및 각도 확인", 
            "detail": "1. 블랙박스 전원 및 녹화 LED 점등 확인\n2. SD 카드 포맷 상태 및 에러 메시지 여부 확인\n3. 카메라 각도가 전방 및 실내를 올바르게 향하는지 세팅"
        }
    ],
    "경비 장구류 및 옵션": [
        {
            "id": "e1", 
            "title": "가스총(가스발사총)", 
            "desc": "약제 유효기간 및 트리거 확인", 
            "detail": "1. 내부 약제통 유효기간(제조일로부터 확인) 점검\n2. 방아쇠(트리거) 및 안전장치 물리적 파손 여부 확인"
        },
        {
            "id": "e2", 
            "title": "휴대용 무전기(TRS)", 
            "desc": "채널 고정 및 안테나 파손 여부", 
            "detail": "1. 지정된 보안 채널로 설정되어 있는지 점검\n2. 안테나 피복 벗겨짐 여부 및 배터리 충전 상태 확인"
        },
        {
            "id": "e3", 
            "title": "비상 구급함/소화기", 
            "desc": "비치 품목 및 압력 확인", 
            "detail": "1. 차량용 소화기 압력 게이지가 녹색(정상) 구간에 있는지 확인\n2. 구급함 내 비상 의약품(소독약, 붕대 등) 비치 및 유통기한 확인"
        }
    ]
}

# ==========================================
# 3. Custom CSS Injection
# ==========================================
def load_css():
    css_file = os.path.join(os.path.dirname(__file__), "ui", "style.css")
    if os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
load_css()

# ==========================================
# 4. Helper Functions
# ==========================================
@st.dialog("🔍 상세점검내역 가이드", width="large")
def show_inspection_details(item_title, item_detail):
    st.markdown(f"### {item_title}")
    st.info("아래의 점검 가이드라인에 따라 꼼꼼하게 확인해 주십시오.")
    for line in item_detail.split('\n'):
        st.markdown(f"- **{line}**")
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("확인 완료 (닫기)", type="primary"):
        st.rerun()

def get_vehicle_db():
    db_path = os.path.join(DB_DIR, "vehicles.csv")
    if os.path.exists(db_path):
        return pd.read_csv(db_path)["차량번호"].tolist()
    return []

def load_all_inspections():
    data = []
    for f in os.listdir(DATA_DIR):
        if f.endswith(".json"):
            with open(os.path.join(DATA_DIR, f), "r", encoding="utf-8") as file:
                try:
                    data.append(json.load(file))
                except:
                    pass
    return data

# ==========================================
# 5. Sidebar Navigation
# ==========================================
with st.sidebar:
    st.markdown("## 🧭 네비게이션")
    page = st.radio("이동할 페이지 선택", ["📋 현장 점검 입력", "📊 관리자 대시보드"])
    st.divider()
    st.markdown("### 🚀 배포 및 엑셀 기능")
    st.info("관리자 탭에서 점검 데이터를 엑셀로 다운로드하고 차량 DB를 업로드할 수 있습니다.")

# ==========================================
# PAGE 1: USER INSPECTION FORM
# ==========================================
if page == "📋 현장 점검 입력":
    # 5.1 Initialize States
    for category, items in CHECK_ITEMS.items():
        for item in items:
            if item["id"] not in st.session_state:
                st.session_state[item["id"]] = "정상"

    def get_status_counts():
        ok_count, ng_count = 0, 0
        for category, items in CHECK_ITEMS.items():
            for item in items:
                if st.session_state.get(item["id"], "정상") == "정상":
                    ok_count += 1
                else:
                    ng_count += 1
        return ok_count, ng_count

    # 5.2 Header
    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    st.markdown(f"""
        <div class="nav-bar-custom">
            <h1>현장 점검 시스템 (본부 지사 통합)</h1>
            <span>{today_str}</span>
        </div>
    """, unsafe_allow_html=True)

    # 5.3 Metrics
    ok_count, ng_count = get_status_counts()
    total_count = ok_count + ng_count

    m1, m2, m3 = st.columns(3)
    m1.metric(label="전체 점검 항목", value=f"{total_count}건")
    m2.metric(label="정비대상 (불량)", value=f"{ng_count}건", delta="-조치필요" if ng_count > 0 else None, delta_color="inverse")
    m3.metric(label="정상기동", value=f"{ok_count}건", delta="양호" if ok_count == total_count else None)

    # 5.4 Form
    with st.container(border=True):
        st.markdown("### 📋 현장 기본 정보")
        c1, c2 = st.columns([2, 1])
        with c1:
            # 차량번호: DB에서 선택하거나 직접 입력
            vehicle_list = get_vehicle_db()
            vehicle_list.insert(0, "기타 (직접입력)")
            selected_vehicle = st.selectbox("차량 번호", options=vehicle_list)
            if selected_vehicle == "기타 (직접입력)":
                car_num = st.text_input("차량 번호 입력", placeholder="예: 123가4567")
            else:
                car_num = selected_vehicle
        with c2:
            branch = st.selectbox("방문 지사", options=BRANCHES)
        
        mileage = st.number_input("누적 주행거리 (km)", value=0, step=1)

    # 5.5 Checklist
    for category, items in CHECK_ITEMS.items():
        st.markdown(f"### 🛠️ {category}")
        with st.container(border=True):
            for item in items:
                col_text, col_btn = st.columns([3, 1])
                with col_text:
                    st.markdown(f"""
                    <div class="check-row-container">
                        <div style="font-weight: 700; font-size: 1.1rem; color: #1e293b;">{item['title']}</div>
                        <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 5px;">{item['desc']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    st.markdown("<br>", unsafe_allow_html=True) # 여백 정렬
                    if st.button("🔍 상세점검내역", key=f"btn_{item['id']}", use_container_width=True):
                        show_inspection_details(item["title"], item["detail"])
                
                # 라디오 버튼
                st.radio(
                    label="상태",
                    options=["정상", "불량"],
                    key=item["id"],
                    horizontal=True,
                    label_visibility="collapsed"
                )
                st.markdown("<hr style='border:none; border-top:1px dashed #e2e8f0;'>", unsafe_allow_html=True)

    # 5.6 Photos & Memo
    with st.container(border=True):
        st.markdown("### 📸 현장 증빙 사진")
        st.info("파일을 업로드하면 엑셀 다운로드 시 파일명이 함께 기록됩니다.")
        cam_col, up_col = st.columns(2)
        with cam_col:
            cam_photo = st.camera_input("실시간 촬영", label_visibility="collapsed")
        with up_col:
            uploaded_files = st.file_uploader("파일 업로드", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

        photo_names = []
        if cam_photo or uploaded_files:
            st.markdown("#### 미리보기")
            cols = st.columns(3)
            idx = 0
            if cam_photo:
                cols[idx % 3].image(cam_photo, use_container_width=True)
                photo_names.append("camera_capture.png")
                idx += 1
            if uploaded_files:
                for file in uploaded_files:
                    cols[idx % 3].image(file, use_container_width=True)
                    photo_names.append(file.name)
                    idx += 1

    with st.container(border=True):
        st.markdown("### 📝 종합 의견")
        memo = st.text_area("특이사항 기록", placeholder="차량 외관 스크래치 등 특이사항을 입력해주세요.", height=100)

    # 5.7 Submit
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 점검 완료 및 데이터 전송", use_container_width=True, type="primary"):
        if not car_num or not car_num.strip():
            st.error("⚠️ 차량 번호를 정확히 입력/선택해주세요.")
        else:
            report_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "car_num": car_num,
                "branch": branch,
                "mileage": mileage,
                "total_count": total_count,
                "ok_count": ok_count,
                "ng_count": ng_count,
                "memo": memo,
                "photos": ", ".join(photo_names) if photo_names else "없음"
            }
            # 개별 항목 결과 합치기
            for cat, items in CHECK_ITEMS.items():
                for item in items:
                    report_data[item["title"]] = st.session_state[item["id"]]
            
            save_path = os.path.join(DATA_DIR, f"report_{car_num}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=4)
                
            st.success(f"✅ {car_num} ({branch}) 점검 데이터가 성공적으로 전송되었습니다!")
            st.balloons()


# ==========================================
# PAGE 2: ADMIN DASHBOARD
# ==========================================
elif page == "📊 관리자 대시보드":
    st.markdown("## 🔐 관리자 인증")
    
    # 단순 인증 로직
    if "admin_auth" not in st.session_state:
        st.session_state["admin_auth"] = False
        
    if not st.session_state["admin_auth"]:
        pwd = st.text_input("관리자 비밀번호를 입력하세요 (데모: admin1234)", type="password")
        if st.button("로그인"):
            if pwd == "admin1234":
                st.session_state["admin_auth"] = True
                st.rerun()
            else:
                st.error("비밀번호가 일치하지 않습니다.")
    else:
        st.markdown("<div style='text-align: right;'><small>✅ 관리자 인증 완료</small></div>", unsafe_allow_html=True)
        if st.button("로그아웃", size="small"):
            st.session_state["admin_auth"] = False
            st.rerun()
            
        st.divider()
        
        # 6.1 차량 DB 관리
        with st.expander("🛠️ 차량 번호 일괄 업로드 (CSV/Excel)"):
            st.info("단일 '차량번호' 컬럼을 가진 엑셀 또는 CSV 파일을 업로드하면 사용자 드롭다운에 즉시 반영됩니다.")
            db_file = st.file_uploader("DB 파일 선택", type=['csv', 'xlsx'])
            if db_file:
                try:
                    if db_file.name.endswith('.csv'):
                        df_db = pd.read_csv(db_file)
                    else:
                        df_db = pd.read_excel(db_file)
                    
                    if "차량번호" in df_db.columns:
                        df_db[["차량번호"]].to_csv(os.path.join(DB_DIR, "vehicles.csv"), index=False)
                        st.success(f"✅ 차량 DB가 업데이트 되었습니다. 총 {len(df_db)}대 등록.")
                    else:
                        st.error("파일에 '차량번호' 컬럼이 없습니다.")
                except Exception as e:
                    st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        
        # 6.2 Data Loading
        inspections = load_all_inspections()
        if not inspections:
            st.warning("아직 등록된 점검 데이터가 없습니다.")
        else:
            df = pd.DataFrame(inspections)
            
            # 6.3 Dashboard Metrics
            st.markdown("### 📊 지사별 점검 현황 대시보드")
            c1, c2, c3 = st.columns(3)
            c1.metric("총 누적 점검", f"{len(df)}건")
            c2.metric("조치 필요 차량 (NG 존재)", f"{len(df[df['ng_count'] > 0])}대")
            c3.metric("최근 점검일", df['timestamp'].max()[:10])
            
            # 지사별 통계
            st.markdown("#### 지사별 점검 대수")
            branch_counts = df['branch'].value_counts().reset_index()
            branch_counts.columns = ['지사명', '점검 건수']
            st.bar_chart(branch_counts.set_index('지사명'))

            # 6.4 Raw Data & Excel Download
            st.markdown("### 📄 전체 상세 점검 내역")
            st.dataframe(df.sort_values(by="timestamp", ascending=False), use_container_width=True)
            
            # Excel Buffer
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='점검내역')
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 점검 데이터 전체 엑셀(Excel) 다운로드",
                data=excel_data,
                file_name=f"차량점검통합데이터_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
