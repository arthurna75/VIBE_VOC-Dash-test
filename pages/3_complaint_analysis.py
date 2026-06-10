import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import load_all_data, sidebar_filters, apply_customer_filter, COLORS, PALETTE

st.set_page_config(page_title="불만·민원 분석", page_icon="😠", layout="wide")
st.title("😠 불만·민원 분석")

customers, complaints, feedback, call_logs, as_requests, usage_data = load_all_data()
region, ctype = sidebar_filters(customers)
filtered_customers = apply_customer_filter(customers, region, ctype)
cids = set(filtered_customers['고객ID'])
comp = complaints[complaints['고객ID'].isin(cids)].copy()

# ── KPI ──────────────────────────────────────────────
total      = len(comp)
resolved   = len(comp[comp['상태'] == '완료'])
processing = len(comp[comp['상태'] == '처리중'])
pending    = len(comp[comp['상태'] == '접수'])

c1, c2, c3, c4 = st.columns(4)
c1.metric("총 불만 건수",  f"{total:,}")
c2.metric("해결 완료",     f"{resolved:,} ({resolved/max(total,1)*100:.1f}%)")
c3.metric("처리 중",       f"{processing:,} ({processing/max(total,1)*100:.1f}%)")
c4.metric("평균 만족도",   f"{comp['만족도'].mean():.2f} / 5")

st.markdown("---")

# ── 카테고리·상태 ──────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 카테고리별 불만 건수")
    cat_counts = comp['카테고리'].value_counts()
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(cat_counts.index, cat_counts.values, color=COLORS['danger'], alpha=0.85)
    ax.bar_label(bars, fmt='%d', padding=3)
    ax.set_xlabel("건수")
    ax.set_title("카테고리별 불만 분포")
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

with col2:
    st.subheader("⚡ 카테고리별 미해결 비율")
    cat_total    = comp.groupby('카테고리').size()
    cat_unresolved = comp[comp['상태'] != '완료'].groupby('카테고리').size()
    cat_rate = (cat_unresolved / cat_total * 100).fillna(0).sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(7, 4))
    colors_bar = [COLORS['danger'] if v > 50 else COLORS['warning'] for v in cat_rate.values]
    bars = ax.barh(cat_rate.index, cat_rate.values, color=colors_bar, alpha=0.85)
    ax.bar_label(bars, fmt='%.1f%%', padding=3)
    ax.set_xlabel("미해결 비율(%)")
    ax.set_title("카테고리별 미해결 비율")
    ax.set_xlim(0, 110)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

st.markdown("---")

# ── 처리 시간 분석 ────────────────────────────────────
st.subheader("⏱ 카테고리별 평균 처리 시간")
resolved_comp = comp[comp['상태'] == '완료'].copy()
resolved_comp['처리시간(일)'] = (
    resolved_comp['해결완료일'] - resolved_comp['접수일시']
).dt.days

proc_time = resolved_comp.groupby('카테고리')['처리시간(일)'].mean().sort_values(ascending=False)

col1, col2 = st.columns([2, 1])
with col1:
    fig, ax = plt.subplots(figsize=(9, 4))
    bars = ax.bar(proc_time.index, proc_time.values, color=COLORS['warning'], alpha=0.85)
    ax.bar_label(bars, fmt='%.1f일', padding=3)
    ax.set_ylabel("평균 처리 시간(일)")
    ax.set_title("카테고리별 평균 처리 시간")
    ax.axhline(proc_time.mean(), color=COLORS['danger'], linestyle='--', linewidth=1.5, label=f'전체 평균 {proc_time.mean():.1f}일')
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

with col2:
    st.markdown("**처리 시간 요약**")
    st.dataframe(
        proc_time.reset_index().rename(columns={'처리시간(일)': '평균(일)'}).round(1),
        use_container_width=True, hide_index=True
    )

st.markdown("---")

# ── 반복 민원 고객 ────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔁 반복 민원 고객 TOP 10")
    repeat = comp.groupby('고객ID').size().sort_values(ascending=False).head(10).reset_index()
    repeat.columns = ['고객ID', '불만 건수']
    repeat = repeat.merge(customers[['고객ID','지역','고객타입']], on='고객ID', how='left')

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(repeat['고객ID'], repeat['불만 건수'], color=COLORS['primary'], alpha=0.85)
    ax.bar_label(bars, fmt='%d건', padding=3)
    ax.set_xlabel("불만 건수")
    ax.set_title("반복 민원 고객 TOP 10")
    ax.invert_yaxis()
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

with col2:
    st.subheader("🗺 지역 × 카테고리 크로스 분석")
    cross = comp.groupby(['지역', '카테고리']).size().unstack(fill_value=0)

    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(cross.values, cmap='Reds', aspect='auto')
    ax.set_xticks(range(len(cross.columns)))
    ax.set_xticklabels(cross.columns, rotation=30, fontsize=9)
    ax.set_yticks(range(len(cross.index)))
    ax.set_yticklabels(cross.index, fontsize=9)
    for i in range(cross.shape[0]):
        for j in range(cross.shape[1]):
            ax.text(j, i, cross.values[i, j], ha='center', va='center', fontsize=9)
    plt.colorbar(im, ax=ax, label='불만 건수')
    ax.set_title("지역 × 카테고리 불만 분포")
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

st.markdown("---")

# ── 월별 불만 카테고리 추이 ───────────────────────────
st.subheader("📈 월별 불만 카테고리 추이")
comp['년월'] = comp['접수일시'].dt.to_period('M').astype(str)
monthly_cat = comp.groupby(['년월', '카테고리']).size().unstack(fill_value=0)

fig, ax = plt.subplots(figsize=(12, 4))
for i, col in enumerate(monthly_cat.columns):
    ax.plot(range(len(monthly_cat)), monthly_cat[col], marker='o', label=col,
            color=PALETTE[i % len(PALETTE)], linewidth=2, markersize=5)
ax.set_xticks(range(len(monthly_cat)))
ax.set_xticklabels(monthly_cat.index, rotation=45, fontsize=8)
ax.set_ylabel("불만 건수")
ax.set_title("월별 카테고리별 불만 추이")
ax.legend(loc='upper right', fontsize=8)
ax.grid(True, alpha=0.3)
plt.tight_layout()
st.pyplot(fig, use_container_width=True)

st.markdown("---")
st.subheader("📋 불만 상세 데이터")
st.dataframe(comp[['불만ID','고객ID','접수일시','카테고리','내용','상태','만족도']].head(50),
             use_container_width=True, hide_index=True)
