import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import load_all_data, sidebar_filters, apply_customer_filter, COLORS, PALETTE

st.set_page_config(page_title="전체 요약", page_icon="📊", layout="wide")
st.title("📊 전체 요약")

customers, complaints, feedback, call_logs, as_requests, usage_data = load_all_data()
region, ctype = sidebar_filters(customers)
filtered_customers = apply_customer_filter(customers, region, ctype)
cids = set(filtered_customers['고객ID'])

# 필터 적용
comp  = complaints[complaints['고객ID'].isin(cids)]
fb    = feedback[feedback['고객ID'].isin(cids)]
calls = call_logs[call_logs['고객ID'].isin(cids)]
usage = usage_data[usage_data['고객ID'].isin(cids)]

# ── KPI 카드 ────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("전체 고객수", f"{len(filtered_customers):,}명")

overdue_rate = (usage[usage['납부상태'] == '연체']['고객ID'].nunique() / max(len(filtered_customers), 1)) * 100
c2.metric("연체 고객 비율", f"{overdue_rate:.1f}%",
          delta="주의" if overdue_rate > 10 else "양호",
          delta_color="inverse" if overdue_rate > 10 else "normal")

avg_sat = pd.concat([comp['만족도'], fb['평가점수'], calls['상담평가']]).mean()
c3.metric("평균 만족도", f"{avg_sat:.2f} / 5")

unresolved = len(comp[comp['상태'].isin(['접수', '처리중'])])
c4.metric("미처리 불만", f"{unresolved:,}건",
          delta="높음" if unresolved > 500 else "정상",
          delta_color="inverse" if unresolved > 500 else "normal")

urgent_as = len(as_requests[as_requests['심각도'] == '긴급'])
c5.metric("긴급 A/S", f"{urgent_as:,}건",
          delta="즉시 대응" if urgent_as > 0 else "없음",
          delta_color="inverse" if urgent_as > 0 else "off")

st.markdown("---")

# ── 지역별 고객 분포 & 타입별 구성 ────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("🗺 지역별 고객 수")
    region_counts = filtered_customers['지역'].value_counts()
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(region_counts.index, region_counts.values, color=COLORS['primary'], alpha=0.85)
    ax.bar_label(bars, fmt='%d', fontsize=9)
    ax.set_ylabel("고객 수")
    ax.set_title("지역별 고객 분포")
    plt.xticks(rotation=30)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

with col2:
    st.subheader("👥 고객 타입 구성")
    type_counts = filtered_customers['고객타입'].value_counts()
    fig, ax = plt.subplots(figsize=(7, 4))
    wedges, texts, autotexts = ax.pie(
        type_counts.values, labels=type_counts.index,
        autopct='%1.1f%%', colors=PALETTE, startangle=90
    )
    ax.set_title("고객 타입별 비율")
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

st.markdown("---")

# ── 지역 × 고객타입 히트맵 ─────────────────────────────
st.subheader("🔥 지역 × 고객타입 히트맵")
heatmap_data = filtered_customers.pivot_table(
    index='지역', columns='고객타입', aggfunc='size', fill_value=0
)
fig, ax = plt.subplots(figsize=(10, 4))
im = ax.imshow(heatmap_data.values, cmap='YlOrRd', aspect='auto')
ax.set_xticks(range(len(heatmap_data.columns)))
ax.set_xticklabels(heatmap_data.columns)
ax.set_yticks(range(len(heatmap_data.index)))
ax.set_yticklabels(heatmap_data.index)
for i in range(len(heatmap_data.index)):
    for j in range(len(heatmap_data.columns)):
        ax.text(j, i, heatmap_data.values[i, j], ha='center', va='center', fontsize=10)
plt.colorbar(im, ax=ax, label='고객 수')
ax.set_title("지역 × 고객타입 고객 수")
plt.tight_layout()
st.pyplot(fig, use_container_width=True)

st.markdown("---")

# ── 월별 종합 추이 ────────────────────────────────────
st.subheader("📈 월별 종합 추이")

comp['년월']  = comp['접수일시'].dt.to_period('M').astype(str)
fb['년월']    = fb['등록일'].dt.to_period('M').astype(str)
calls['년월'] = calls['상담일시'].dt.to_period('M').astype(str)

monthly_comp  = comp.groupby('년월').size()
monthly_fb    = fb.groupby('년월').size()
monthly_calls = calls.groupby('년월').size()

all_months = sorted(set(monthly_comp.index) | set(monthly_fb.index) | set(monthly_calls.index))

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(all_months, [monthly_comp.get(m, 0) for m in all_months],
        marker='o', label='불만', color=COLORS['danger'], linewidth=2)
ax.plot(all_months, [monthly_fb.get(m, 0) for m in all_months],
        marker='s', label='피드백', color=COLORS['success'], linewidth=2)
ax.plot(all_months, [monthly_calls.get(m, 0) for m in all_months],
        marker='^', label='상담', color=COLORS['primary'], linewidth=2)
ax.set_xlabel("년월")
ax.set_ylabel("건수")
ax.set_title("월별 불만·피드백·상담 추이")
ax.legend()
ax.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig, use_container_width=True)

st.markdown("---")

# ── 실시간 알람 ───────────────────────────────────────
st.subheader("🚨 즉시 처리 필요 항목")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**미처리 불만 (상위 10건)**")
    open_comp = comp[comp['상태'].isin(['접수', '처리중'])][['불만ID','고객ID','카테고리','내용','상태','접수일시']].head(10)
    st.dataframe(open_comp, use_container_width=True, hide_index=True)

with col2:
    st.markdown("**긴급 A/S 미완료**")
    urgent = as_requests[(as_requests['심각도'] == '긴급') & (as_requests['완료일'].isna())][
        ['AS신청ID','고객ID','분류','심각도','신청일']].head(10)
    st.dataframe(urgent, use_container_width=True, hide_index=True)
