import streamlit as st
from datetime import date, datetime, timedelta
import re

st.set_page_config(
    page_title="틈새 | 생활 문제 해결소",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Style ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
.stApp { background: #F6F7F4; }
.block-container { max-width: 1050px; padding-top: 1.4rem; padding-bottom: 3rem; }
.hero {
    background: linear-gradient(120deg, #203C35 0%, #31584C 100%);
    padding: 28px 30px; border-radius: 22px; color: white; margin-bottom: 20px;
}
.hero h1 { color: white; font-size: 2rem; margin: 0 0 7px 0; font-weight: 800; }
.hero p { color: #DCE9E2; margin: 0; font-size: 0.98rem; }
.eyebrow { color:#B9D5C6; letter-spacing: .12em; font-size:.72rem; font-weight:700; }
.panel {
    background: white; border: 1px solid #E8ECE7; border-radius: 18px;
    padding: 19px 20px; margin-bottom: 12px;
}
.panel h3 { margin-top: 0; color:#203C35; font-size:1.05rem; }
.muted { color:#77827B; font-size:.88rem; }
.result {
    background:#EEF5F0; border:1px solid #D8E8DD; border-radius:15px;
    padding:16px 18px; margin: 10px 0;
}
.pill {
    display:inline-block; background:#EAF1EC; color:#31584C; border-radius:99px;
    padding:4px 10px; font-size:.76rem; font-weight:700; margin-right:5px;
}
div.stButton > button {
    border-radius: 12px; border: 1px solid #D8E2DA; min-height: 2.7rem;
    font-weight: 650;
}
div.stButton > button[kind="primary"] {
    background:#31584C; border-color:#31584C; color:white;
}
[data-testid="stMetric"] {
    background:white; border:1px solid #E8ECE7; border-radius:15px; padding:12px 14px;
}
[data-testid="stTabs"] button { font-weight:650; }
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ---------- Session data ----------
if "meds" not in st.session_state:
    st.session_state.meds = []
if "supplies" not in st.session_state:
    st.session_state.supplies = []
if "issues" not in st.session_state:
    st.session_state.issues = []
if "solutions" not in st.session_state:
    st.session_state.solutions = []

def card(title, body, tag=None):
    tag_html = f'<span class="pill">{tag}</span>' if tag else ""
    st.markdown(f'<div class="panel">{tag_html}<h3>{title}</h3><div>{body}</div></div>', unsafe_allow_html=True)

def recommend_solution(category, detail):
    text = detail.strip()
    low = text.lower()
    if category == "약·건강 관련":
        return (
            "약 이름과 남은 수량을 먼저 확인하고, 처방전·약 봉투에 적힌 복용 지침을 기준으로 관리해 보세요. "
            "재구매가 필요하면 약국에 전화해 재고와 조제 가능 시점을 확인하면 방문을 줄일 수 있습니다.",
            ["약 봉투 또는 처방전 확인", "남은 수량 확인", "약국에 재고·조제 가능 여부 문의"],
            "이 앱은 약 재고와 준비 과정을 정리하는 도구입니다. 복용량·복용 시간은 임의로 바꾸지 말고, 변경이 필요하면 의사나 약사에게 확인하세요."
        )
    if category == "집안일·주거":
        if any(k in low for k in ["누수", "물", "수도"]):
            advice = "물이 새는 위치와 발생 시점을 사진으로 남기고, 사용을 중단할 수 있는 설비인지 확인하세요. 누수가 계속되거나 전기 설비 근처라면 직접 수리하지 말고 관리사무소나 전문 수리업체에 연락하세요."
            todo = ["누수 위치 사진 촬영", "물이 번지는 범위 확인", "관리사무소 또는 전문업체 문의"]
        elif any(k in low for k in ["전등", "불", "조명"]):
            advice = "전등 자체 문제인지 스위치·차단기 문제인지 구분할 수 있도록 증상을 기록하세요. 전기 배선이나 내부 부품은 직접 분해하지 말고 필요하면 전문가에게 맡기세요."
            todo = ["언제부터 문제가 생겼는지 기록", "전구 교체형인지 확인", "전기 관련 이상이면 전문가 문의"]
        else:
            advice = "문제가 발생한 장소와 상태를 사진으로 남기고, 긴급도에 따라 직접 처리할 일과 업체에 맡길 일을 구분하세요."
            todo = ["문제 사진 남기기", "발생 장소와 시점 기록", "직접 해결 또는 전문가 의뢰 결정"]
        return advice, todo, "가스·전기·누수 등 안전과 관련된 문제는 무리하게 직접 수리하지 마세요."
    if category == "생활용품·구매":
        return (
            "현재 남은 양과 하루 또는 일주일 사용량을 대략 확인한 뒤, 다음 구매 시점을 정해 보세요. "
            "자주 쓰는 물건은 묶음 구매나 정기 배송이 실제로 더 저렴한지도 비교할 수 있습니다.",
            ["현재 남은 양 확인", "평소 사용 속도 파악", "필요한 품목을 한 번에 구매"],
            "필요 이상으로 많이 구매하면 보관 공간과 낭비가 늘 수 있으니 사용량에 맞춰 구매하세요."
        )
    if category == "메일·업무":
        return (
            "메일 내용을 붙여 넣으면 요청사항, 기한, 회신 필요 여부를 직접 구분해 볼 수 있습니다. "
            "개인정보나 민감한 내용은 입력 전에 지우고, 실제 발신·회신은 원문을 확인한 뒤 진행하세요.",
            ["요청받은 일 확인", "마감일과 회신 여부 표시", "원문을 확인한 뒤 답장 작성"],
            "이 화면은 외부 메일 계정에 연결되거나 메일을 자동 전송하지 않습니다. 비밀번호·개인정보·연구자료 등 민감한 내용은 입력하지 마세요."
        )
    return (
        "문제를 한 문장으로 정리한 뒤, 지금 바로 할 수 있는 일과 다른 사람의 도움이 필요한 일을 나눠 보세요. "
        "시간이 오래 걸리는 일은 필요한 준비물을 먼저 모아 한 번에 처리하는 편이 효율적입니다.",
        ["문제를 한 문장으로 정리", "바로 할 수 있는 일 구분", "필요한 준비물과 도움 확인"],
        "상황에 따라 전문가나 관련 기관의 확인이 필요할 수 있습니다."
    )

# ---------- Header ----------
st.markdown("""
<div class="hero">
  <div class="eyebrow">SMALL FRICTIONS, SMART SOLUTIONS</div>
  <h1>틈새 <span style="font-size:1rem;font-weight:500;color:#C9DDD1;">생활 문제 해결소</span></h1>
  <p>사소하지만 반복되는 번거로움, 한곳에서 정리하고 해결 방법을 찾아보세요.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("")

tab_home, tab_solve, tab_medicine, tab_homecare, tab_mail = st.tabs(
    ["홈", "문제 해결", "약 재고", "생활용품·집", "메일 정리"]
)

# ---------- Home ----------
with tab_home:
    st.subheader("오늘의 생활 요약")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("등록한 약", f"{len(st.session_state.meds)}개")
    with c2:
        st.metric("생활용품", f"{len(st.session_state.supplies)}개")
    with c3:
        st.metric("해결 메모", f"{len(st.session_state.solutions)}개")
    st.markdown("")
    st.markdown("#### 무엇을 해결해 볼까요?")
    cols = st.columns(2)
    with cols[0]:
        card("💊 약 재고 확인", "남은 약 수량과 예상 소진일을 관리해 재구매 준비를 도와요.", "건강")
        card("🏠 집안 문제", "집에서 생긴 문제를 정리하고 안전한 다음 행동을 찾아요.", "주거")
    with cols[1]:
        card("🧻 생활용품", "자주 쓰는 물건의 남은 양과 구매할 품목을 정리해요.", "구매")
        card("✉️ 메일 정리", "긴 메일에서 요청사항과 기한을 간단히 구분해요.", "업무")
    st.info("처음에는 각 메뉴에서 예시 정보를 직접 입력해 보세요. 입력한 내용은 현재 앱 실행 세션에 저장됩니다.")

# ---------- Problem solver ----------
with tab_solve:
    st.subheader("문제 해결 도우미")
    st.caption("불편한 상황을 선택하고 간단히 설명하면, 다음에 할 일을 정리해 드려요.")
    category = st.selectbox("어떤 문제인가요?", ["약·건강 관련", "집안일·주거", "생활용품·구매", "메일·업무", "기타"])
    detail = st.text_area("어떤 점이 번거로운가요?", placeholder="예: 약이 언제 떨어질지 몰라 약국에 갑자기 가게 돼요.", height=105)
    if st.button("해결 방법 찾기", type="primary", use_container_width=True):
        if not detail.strip():
            st.warning("상황을 한 문장으로 입력해 주세요.")
        else:
            advice, todo, caution = recommend_solution(category, detail)
            st.session_state.solutions.insert(0, {
                "category": category, "detail": detail.strip(),
                "advice": advice, "date": date.today().isoformat()
            })
            st.markdown('<div class="result"><b>추천 해결 방향</b><br>' + advice + '</div>', unsafe_allow_html=True)
            st.markdown("**이렇게 진행해 보세요.**")
            for item in todo:
                st.checkbox(item, key=f"solve_{len(st.session_state.solutions)}_{item}")
            st.caption("참고: " + caution)
    if st.session_state.solutions:
        st.markdown("---")
        st.markdown("#### 최근 해결 기록")
        for item in st.session_state.solutions[:5]:
            with st.expander(f"{item['category']} · {item['date']}"):
                st.write(item["detail"])
                st.write(item["advice"])

# ---------- Medicine ----------
with tab_medicine:
    st.subheader("약 재고 관리")
    st.caption("복용량이나 처방을 판단하는 기능이 아니라, 사용자가 입력한 수량을 바탕으로 재구매 준비 시점을 계산합니다.")
    with st.form("medicine_form", clear_on_submit=True):
        a, b = st.columns(2)
        with a:
            med_name = st.text_input("약 이름", placeholder="예: 처방약 A")
            quantity = st.number_input("현재 남은 수량", min_value=0, step=1, value=10)
        with b:
            daily_use = st.number_input("하루 사용 수량", min_value=0.1, step=0.1, value=1.0)
            buffer_days = st.number_input("재구매 준비 여유 기간(일)", min_value=0, max_value=30, value=5)
        submitted = st.form_submit_button("약 등록하기", type="primary", use_container_width=True)
        if submitted:
            if not med_name.strip():
                st.error("약 이름을 입력해 주세요.")
            else:
                st.session_state.meds.append({
                    "name": med_name.strip(), "quantity": int(quantity),
                    "daily": float(daily_use), "buffer": int(buffer_days)
                })
                st.success(f"{med_name} 등록 완료")
    if st.session_state.meds:
        st.markdown("#### 등록된 약")
        for i, med in enumerate(st.session_state.meds):
            days_left = med["quantity"] / med["daily"] if med["daily"] > 0 else None
            buy_by = max(0, int(days_left - med["buffer"])) if days_left is not None else 0
            with st.container(border=True):
                left, right = st.columns([3, 1])
                with left:
                    st.markdown(f"**{med['name']}**")
                    st.caption(f"남은 수량 {med['quantity']} · 하루 사용 수량 {med['daily']:g}")
                    if days_left is not None:
                        st.write(f"입력한 사용량 기준 약 **{days_left:.1f}일분** 남아 있어요.")
                        if days_left <= med["buffer"]:
                            st.warning("재구매 준비 시점을 확인해 주세요.")
                        else:
                            st.info(f"약 {buy_by}일 안에 재구매를 준비하는 것을 고려해 보세요.")
                with right:
                    if st.button("삭제", key=f"delmed{i}"):
                        st.session_state.meds.pop(i)
                        st.rerun()
    else:
        st.info("아직 등록된 약이 없어요. 약 이름과 남은 수량을 입력해 보세요.")
    st.caption("주의: 실제 복용 지침과 처방은 반드시 약 봉투·처방전 및 의료진 안내를 따르세요. 이 계산은 예상치이며 처방 변경이나 복용 중단을 권하지 않습니다.")

# ---------- Home supplies / issues ----------
with tab_homecare:
    st.subheader("생활용품·집 관리")
    st.markdown("#### 생활용품 재고")
    with st.form("supply_form", clear_on_submit=True):
        x, y, z = st.columns([2, 1, 1])
        with x:
            item_name = st.text_input("물건 이름", placeholder="예: 세탁세제")
        with y:
            amount = st.number_input("남은 양(개)", min_value=0, step=1, value=1)
        with z:
            minimum = st.number_input("구매 기준(개)", min_value=0, step=1, value=1)
        add_supply = st.form_submit_button("재고 등록", type="primary", use_container_width=True)
        if add_supply:
            if item_name.strip():
                st.session_state.supplies.append({"name": item_name.strip(), "amount": int(amount), "minimum": int(minimum)})
                st.success("생활용품을 등록했어요.")
            else:
                st.error("물건 이름을 입력해 주세요.")
    if st.session_state.supplies:
        for i, item in enumerate(st.session_state.supplies):
            l, r = st.columns([4, 1])
            with l:
                st.write(f"**{item['name']}** — {item['amount']}개 남음")
                if item["amount"] <= item["minimum"]:
                    st.warning("구매 목록에 추가하는 것을 고려해 보세요.")
                else:
                    st.caption(f"구매 기준: {item['minimum']}개")
            with r:
                if st.button("삭제", key=f"delsupply{i}"):
                    st.session_state.supplies.pop(i)
                    st.rerun()
    else:
        st.caption("등록한 생활용품이 아직 없어요.")

    st.markdown("---")
    st.markdown("#### 집에서 발견한 문제")
    issue_type = st.selectbox("문제 종류", ["청소·정리", "고장·수리", "누수·습기", "전기·조명", "기타"])
    issue_text = st.text_area("문제 상황", placeholder="예: 싱크대 아래쪽에 물기가 보여요.", height=85, key="issue_text")
    if st.button("문제 등록 및 해결 방향 보기", type="primary"):
        if issue_text.strip():
            advice, todo, caution = recommend_solution("집안일·주거", issue_text)
            st.session_state.issues.insert(0, {"type": issue_type, "text": issue_text.strip(), "advice": advice})
            st.markdown('<div class="result"><b>추천 해결 방향</b><br>' + advice + '</div>', unsafe_allow_html=True)
            st.markdown("**확인할 사항**")
            for t in todo:
                st.write("• " + t)
            st.caption(caution)
        else:
            st.warning("문제 상황을 입력해 주세요.")
    if st.session_state.issues:
        st.markdown("#### 등록된 문제")
        for issue in st.session_state.issues[:5]:
            with st.expander(f"{issue['type']} · {issue['text'][:35]}"):
                st.write(issue["advice"])

# ---------- Email ----------
with tab_mail:
    st.subheader("메일 핵심 정리")
    st.caption("메일 계정에 연결하지 않는 시제품입니다. 민감한 정보는 지우고 필요한 문장만 붙여 넣으세요.")
    mail_text = st.text_area("메일 내용 붙여넣기", placeholder="메일 본문을 여기에 붙여 넣으세요.", height=210)
    if st.button("핵심 내용 정리", type="primary", use_container_width=True):
        if not mail_text.strip():
            st.warning("메일 내용을 입력해 주세요.")
        else:
            lines = [re.sub(r'\s+', ' ', line).strip(" -•\t") for line in mail_text.splitlines() if line.strip()]
            date_patterns = re.findall(r'\d{4}[년./-]\s?\d{1,2}[월./-]\s?\d{1,2}일?', mail_text)
            keywords = ["제출", "회신", "답변", "신청", "참석", "확인", "마감", "기한", "요청", "부탁", "까지"]
            action_lines = [line for line in lines if any(word in line for word in keywords)]
            st.markdown('<div class="result"><b>메일 핵심</b><br>' + "<br>".join(lines[:5]) + '</div>', unsafe_allow_html=True)
            st.markdown("**요청·확인할 내용으로 보이는 문장**")
            if action_lines:
                for line in action_lines[:8]:
                    st.write("• " + line)
            else:
                st.write("뚜렷한 요청 문장을 자동으로 찾지 못했어요. 메일 원문을 다시 확인해 주세요.")
            st.markdown("**날짜로 보이는 표현**")
            st.write(", ".join(date_patterns) if date_patterns else "날짜 표현을 찾지 못했어요.")
            st.caption("자동 분류는 단순 키워드 기반이므로 중요한 기한이나 요청은 원문에서 반드시 확인하세요. 메일을 발송하거나 계정에 접근하지 않습니다.")

st.markdown("---")
st.markdown('<p class="muted" style="text-align:center;">틈새 · 일상의 작은 번거로움을 줄이는 생활 도구</p>', unsafe_allow_html=True)
