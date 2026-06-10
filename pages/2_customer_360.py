import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import load_all_data, COLORS, PALETTE

st.set_page_config(page_title="고객 360도 뷰", page_icon="👤", layout="wide")
st.title("👤 고객 360도 뷰")

customers, complaints, feedback, call_logs, as_requests, usage_data = load_all_data()

# ── 검색 영역 ─────────────────────────────────────────
st.sidebar.header("🔍 고객 검색")
search_mode = st.sidebar.radio("검색 방식", ["고객ID 직접 입력", "조건 검색"])

if search_mode == "고객ID 직접 입력":
    cid = st.sidebar.text_input("고객ID", placeholder="예: CUST000001")
    if cid:
        selected_ids = [cid]
    else:
        selected_ids = []
else:
    region = st.sidebar.selectbox("지역", ['전체'] + sorted(customers['지역'].unique().tolist()))
    ctype  = st.sidebar.selectbox("고객타입", ['전체'] + sorted(customers['고객타입'].unique().tolist()))
    df_f = customers.copy()
    if region != '전체': df_f = df_f[df_f['지역'] == region]
    if ctype  != '전체': df_f = df_f[df_f['고객타입'] == ctype]
    selected_ids = [st.sidebar.selectbox("고객 선택", df_f['고객ID'].tolist())]

if not selected_ids or selected_ids[0] == '':
    st.info("왼쪽 사이드바에서 고객을 검색하거나 선택하세요.")
    st.stop()

cid = selected_ids[0]
cust = customers[customers['고객ID'] == cid]
if cust.empty:
    st.error(f"고객 '{cid}'을 찾을 수 없습니다.")
    st.stop()

cust = cust.iloc[0]

# ── 고객 프로필 ───────────────────────────────────────
st.subheader(f"📋 고객 프로필 — {cid}")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("지역",     cust['지역'])
c2.metric("고객 타입", cust['고객타입'])
c3.metric("요금제",   cust['요금제'])
c4.metric("계약기간", cust['계약기간'])
c5.metric("가입일",   str(cust['가입일'].date()))

st.markdown("---")

# 개별 데이터 필터
cust_comp  = complaints[complaints['고객ID']  == cid].sort_values('접수일시', ascending=False)
cust_fb    = feedback[feedback['고객ID']      == cid].sort_values('등록일', ascending=False)
cust_calls = call_logs[call_logs['고객ID']    == cid].sort_values('상담일시', ascending=False)
cust_as    = as_requests[as_requests['고객ID']== cid].sort_values('신청일', ascending=False)
cust_usage = usage_data[usage_data['고객ID']  == cid].sort_values('년월')

# ── 사용량 이력 ───────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 월별 사용량·요금")
    if not cust_usage.empty:
        fig, ax1 = plt.subplots(figsize=(8, 4))
        ax2 = ax1.twinx()
        months = cust_usage['년월']
        x = range(len(months))
        ax1.bar(x, cust_usage['사용량(㎥)'], color=COLORS['primary'], alpha=0.7, label='사용량(㎥)')
        ax2.plot(x, cust_usage['요금(원)'] / 1000, color=COLORS['danger'], marker='o',
                 linewidth=2, label='요금(천원)')
        ax1.set_xticks(x)
        ax1.set_xticklabels(months, rotation=45, fontsize=8)
        ax1.set_ylabel("사용량(㎥)")
        ax2.set_ylabel("요금(천원)")
        ax1.set_title("월별 사용량 및 요금")
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
    else:
        st.info("사용량 데이터가 없습니다.")

with col2:
    st.subheader("⭐ 만족도 레이더")
    categories = ['상담 평가', '피드백 점수', '불만 만족도', 'A/S 만족도']
    values = [
        cust_calls['상담평가'].mean()       if not cust_calls.empty else 3,
        cust_fb['평가점수'].mean()           if not cust_fb.empty   else 3,
        cust_comp['만족도'].mean()           if not cust_comp.empty else 3,
        cust_as['기술자만족도'].dropna().mean() if not cust_as.empty else 3,
    ]
    values = [v if not np.isnan(v) else 3 for v in values]

    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    values_plot = values + [values[0]]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 5), subplot_kw=dict(polar=True))
    ax.fill(angles, values_plot, color=COLORS['primary'], alpha=0.25)
    ax.plot(angles, values_plot, color=COLORS['primary'], linewidth=2)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(['1', '2', '3', '4', '5'], fontsize=8)
    ax.set_title("고객 만족도 레이더", pad=15)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

st.markdown("---")

# ── 이력 탭 ──────────────────────────────────────────
st.subheader("📂 고객 활동 이력")
tab1, tab2, tab3, tab4 = st.tabs(["😠 불만 이력", "💬 피드백 이력", "☎️ 상담 이력", "🛠 A/S 이력"])

with tab1:
    if cust_comp.empty:
        st.info("불만 이력 없음")
    else:
        st.dataframe(cust_comp[['불만ID','접수일시','카테고리','내용','상태','만족도']],
                     use_container_width=True, hide_index=True)

with tab2:
    if cust_fb.empty:
        st.info("피드백 이력 없음")
    else:
        st.dataframe(cust_fb[['피드백ID','등록일','내용','평가점수','유형']],
                     use_container_width=True, hide_index=True)

with tab3:
    if cust_calls.empty:
        st.info("상담 이력 없음")
    else:
        st.dataframe(cust_calls[['상담ID','상담일시','상담유형','상담시간(분)','상담원ID','상담평가']],
                     use_container_width=True, hide_index=True)

with tab4:
    if cust_as.empty:
        st.info("A/S 이력 없음")
    else:
        st.dataframe(cust_as[['AS신청ID','신청일','분류','심각도','완료일','기술자만족도']],
                     use_container_width=True, hide_index=True)
