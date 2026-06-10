import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import load_all_data, sidebar_filters, apply_customer_filter, COLORS, PALETTE

st.set_page_config(page_title="사용량·요금 분석", page_icon="📈", layout="wide")
st.title("📈 사용량·요금 분석")

customers, complaints, feedback, call_logs, as_requests, usage_data = load_all_data()
region, ctype = sidebar_filters(customers)
filtered_customers = apply_customer_filter(customers, region, ctype)
cids = set(filtered_customers['고객ID'])

usage = usage_data[usage_data['고객ID'].isin(cids)].copy()
usage = usage.merge(customers[['고객ID','고객타입','지역']], on='고객ID', how='left')

# ── KPI ──────────────────────────────────────────────
total_usage     = usage['사용량(㎥)'].sum()
avg_usage       = usage['사용량(㎥)'].mean()
total_billing   = usage['요금(원)'].sum()
overdue_rate    = (usage[usage['납부상태'] == '연체'].shape[0] / max(len(usage), 1)) * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("총 사용량",      f"{total_usage:,.0f} ㎥")
c2.metric("평균 사용량",    f"{avg_usage:.1f} ㎥")
c3.metric("총 청구 요금",   f"{total_billing/1e8:.1f}억원")
c4.metric("연체 비율",      f"{overdue_rate:.1f}%",
          delta="주의" if overdue_rate > 10 else "양호",
          delta_color="inverse" if overdue_rate > 10 else "normal")

st.markdown("---")

# ── 고객타입별 월평균 사용량 ──────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏭 고객타입별 평균 사용량")
    type_usage = usage.groupby('고객타입')['사용량(㎥)'].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(type_usage.index, type_usage.values, color=PALETTE[:len(type_usage)], alpha=0.85)
    ax.bar_label(bars, fmt='%.1f', padding=3)
    ax.set_ylabel("평균 사용량(㎥)")
    ax.set_title("고객타입별 평균 월 사용량")
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

with col2:
    st.subheader("💰 납부 상태 분포")
    pay_counts = usage['납부상태'].value_counts()
    color_map = {'납부': COLORS['success'], '연체': COLORS['danger'], '면제': COLORS['warning']}
    pay_colors = [color_map.get(s, COLORS['neutral']) for s in pay_counts.index]
    fig, ax = plt.subplots(figsize=(7, 4))
    wedges, texts, autotexts = ax.pie(
        pay_counts.values, labels=pay_counts.index,
        autopct='%1.1f%%', colors=pay_colors, startangle=90
    )
    ax.set_title("납부 상태 분포")
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

st.markdown("---")

# ── 월별 사용량·요금 추이 ─────────────────────────────
st.subheader("📅 월별 사용량·요금 추이")
monthly = usage.groupby('년월').agg(
    총사용량=('사용량(㎥)', 'sum'),
    총요금=('요금(원)', 'sum'),
    연체건수=('납부상태', lambda x: (x == '연체').sum())
).reset_index()

fig, ax1 = plt.subplots(figsize=(12, 4))
ax2 = ax1.twinx()
x = range(len(monthly))
ax1.bar(x, monthly['총사용량'], color=COLORS['primary'], alpha=0.6, label='총 사용량(㎥)')
ax2.plot(x, monthly['총요금'] / 1e6, color=COLORS['danger'], marker='o',
         linewidth=2, label='총 요금(백만원)')
ax1.set_xticks(x)
ax1.set_xticklabels(monthly['년월'], rotation=45, fontsize=8)
ax1.set_ylabel("총 사용량(㎥)")
ax2.set_ylabel("총 요금(백만원)")
ax1.set_title("월별 사용량 및 요금 추이")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9)
plt.tight_layout()
st.pyplot(fig, use_container_width=True)

st.markdown("---")

# ── 요금 구간별 고객 분포 & 지역별 ──────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("💳 요금 구간별 고객 분포")
    avg_bill = usage.groupby('고객ID')['요금(원)'].mean()
    bins = [0, 50000, 100000, 200000, 500000, float('inf')]
    labels = ['~5만', '5~10만', '10~20만', '20~50만', '50만+']
    bill_seg = pd.cut(avg_bill, bins=bins, labels=labels)
    seg_counts = bill_seg.value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(seg_counts.index, seg_counts.values, color=COLORS['warning'], alpha=0.85)
    ax.bar_label(bars, fmt='%d', padding=3)
    ax.set_ylabel("고객 수")
    ax.set_xlabel("월평균 요금 구간")
    ax.set_title("요금 구간별 고객 분포")
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

with col2:
    st.subheader("🗺 지역별 평균 사용량")
    region_usage = usage.groupby('지역')['사용량(㎥)'].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(region_usage.index, region_usage.values, color=COLORS['primary'], alpha=0.85)
    ax.bar_label(bars, fmt='%.1f', padding=3)
    ax.set_xlabel("평균 사용량(㎥)")
    ax.set_title("지역별 평균 월 사용량")
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

st.markdown("---")

# ── 이상 사용량 고객 탐지 ─────────────────────────────
st.subheader("⚠️ 이상 사용량 고객 탐지 (평균 ±2σ)")
cust_avg = usage.groupby('고객ID')['사용량(㎥)'].mean()
mean_val  = cust_avg.mean()
std_val   = cust_avg.std()
upper     = mean_val + 2 * std_val
lower     = max(mean_val - 2 * std_val, 0)

anomaly_high = cust_avg[cust_avg > upper].reset_index()
anomaly_low  = cust_avg[cust_avg < lower].reset_index()
anomaly_high.columns = ['고객ID', '평균사용량(㎥)']
anomaly_low.columns  = ['고객ID', '평균사용량(㎥)']

anomaly_high = anomaly_high.merge(customers[['고객ID','지역','고객타입']], on='고객ID', how='left')
anomaly_low  = anomaly_low.merge(customers[['고객ID','지역','고객타입']],  on='고객ID', how='left')

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**🔴 과다 사용 고객 ({len(anomaly_high)}명, 기준: {upper:.0f}㎥ 초과)**")
    st.dataframe(anomaly_high.sort_values('평균사용량(㎥)', ascending=False).head(15),
                 use_container_width=True, hide_index=True)
with col2:
    st.markdown(f"**🔵 극소 사용 고객 ({len(anomaly_low)}명, 기준: {lower:.0f}㎥ 미만)**")
    st.dataframe(anomaly_low.sort_values('평균사용량(㎥)').head(15),
                 use_container_width=True, hide_index=True)

# 분포 시각화
fig, ax = plt.subplots(figsize=(10, 4))
ax.hist(cust_avg.values, bins=50, color=COLORS['primary'], alpha=0.7, edgecolor='white')
ax.axvline(upper, color=COLORS['danger'],  linestyle='--', linewidth=2, label=f'상한 {upper:.0f}㎥')
ax.axvline(lower, color=COLORS['warning'], linestyle='--', linewidth=2, label=f'하한 {lower:.0f}㎥')
ax.axvline(mean_val, color='black', linestyle='-', linewidth=1.5, label=f'평균 {mean_val:.0f}㎥')
ax.set_xlabel("월평균 사용량(㎥)")
ax.set_ylabel("고객 수")
ax.set_title("고객별 월평균 사용량 분포")
ax.legend()
plt.tight_layout()
st.pyplot(fig, use_container_width=True)
