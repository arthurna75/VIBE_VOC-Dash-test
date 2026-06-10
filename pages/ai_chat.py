import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import load_all_data, build_data_context

st.set_page_config(page_title="AI 데이터 분석", page_icon="🤖", layout="wide")
st.title("🤖 AI 데이터 분석 어시스턴트")
st.caption("현재 대시보드 데이터를 기반으로 질문하면 Gemini가 분석해 드립니다.")

# ── 데이터 로드 ──────────────────────────────────────────
customers, complaints, feedback, call_logs, as_requests, usage_data = load_all_data()
data_context = build_data_context(customers, complaints, feedback, call_logs, as_requests, usage_data)

# ── Gemini 클라이언트 초기화 ──────────────────────────────
api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
model_name = st.secrets.get("GEMINI_MODEL") or os.getenv("GEMINI_MODEL", "gemini-flash-latest")

model_ok = False
client = None

if not api_key:
    st.error("GEMINI_API_KEY가 .env 파일에 없습니다.")
else:
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        model_ok = True
    except Exception as e:
        st.error(f"Gemini 초기화 실패: {e}")

# ── 채팅 히스토리 초기화 ──────────────────────────────────
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# ── 사이드바 ──────────────────────────────────────────────
with st.sidebar:
    st.header("📊 현재 데이터 현황")
    st.info(f"**전체 고객**: {len(customers):,}명")

    overdue = usage_data[usage_data['납부상태'] == '연체']['고객ID'].nunique()
    overdue_rate = overdue / max(len(customers), 1) * 100
    st.info(f"**연체 고객**: {overdue:,}명 ({overdue_rate:.1f}%)")

    unresolved = len(complaints[complaints['상태'].isin(['접수', '처리중'])])
    st.info(f"**미처리 불만**: {unresolved:,}건")

    avg_sat = pd.concat([complaints['만족도'], feedback['평가점수'], call_logs['상담평가']]).mean()
    st.info(f"**평균 만족도**: {avg_sat:.2f} / 5.0")

    if model_ok:
        st.success(f"✅ 모델: `{model_name}`")
    else:
        st.error("❌ Gemini 연결 안됨")

    st.markdown("---")
    st.markdown("**질문 예시**")
    example_questions = [
        "연체율이 높은 지역은 어디인가요?",
        "불만이 가장 많은 카테고리는?",
        "고객 만족도를 높이려면 어떻게 해야 할까요?",
        "미처리 불만 처리 우선순위를 알려주세요",
        "어느 고객 타입에서 민원이 가장 많나요?",
    ]
    for q in example_questions:
        if st.button(q, use_container_width=True, key=f"ex_{hash(q)}"):
            st.session_state.pending_question = q
            st.rerun()

    st.markdown("---")
    if st.button("대화 초기화", use_container_width=True):
        st.session_state.chat_messages = []
        st.rerun()

# ── 대화 내역 표시 ────────────────────────────────────────
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── 입력 처리 ─────────────────────────────────────────────
if "pending_question" in st.session_state:
    prompt = st.session_state.pop("pending_question")
else:
    prompt = st.chat_input("데이터에 대해 질문하세요...")

if prompt:
    if not model_ok:
        st.error("Gemini가 초기화되지 않아 답변할 수 없습니다. API 키를 확인하세요.")
    else:
        # 사용자 메시지 표시 및 저장
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("분석 중..."):
                try:
                    # 대화 히스토리를 Gemini Content 형식으로 변환
                    history = []
                    for m in st.session_state.chat_messages[:-1]:
                        role = "user" if m["role"] == "user" else "model"
                        history.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))

                    # 현재 사용자 질문 추가
                    history.append(types.Content(role="user", parts=[types.Part(text=prompt)]))

                    # data_context는 system_instruction으로 항상 전달
                    config = types.GenerateContentConfig(
                        system_instruction=data_context,
                        temperature=0.3,
                    )

                    response = client.models.generate_content(
                        model=model_name,
                        contents=history,
                        config=config,
                    )
                    answer = response.text
                    st.markdown(answer)
                    st.session_state.chat_messages.append({"role": "assistant", "content": answer})

                except Exception as e:
                    err_msg = f"응답 생성 중 오류: {e}"
                    st.error(err_msg)
