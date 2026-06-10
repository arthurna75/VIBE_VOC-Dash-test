import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import load_all_data, sidebar_filters, apply_customer_filter, COLORS, PALETTE

st.set_page_config(page_title="A/S·상담 운영", page_icon="🛠", layout="wide")
st.title("🛠 A/S·상담 운영 현황")

customers, complaints, feedback, call_logs, as_requests, usage_data = load_all_data()
region, ctype = sidebar_filters(customers)
filtered_customers = apply_customer_filter(customers, region, ctype)
cids = set(filtered_customers['고객ID'])

calls = call_logs[call_logs['고객ID'].isin(cids)].copy()
asreq = as_requests[as_requests['고객ID'].isin(cids)].copy()

# 시간대 컬럼 추가
calls['시간대'] = calls['상담일시'].dt.hour
calls['요일']  = calls['상담일시'].dt.day_name()
calls['년월']  = calls['상담일시'].dt.to_period('M').astype(str)

# 처리시간 계산
asreq_resolved = asreq[asreq['완료일'].notna()].copy()
asreq_resolved['처리시간(일)'] = (asreq_resolved['완료일'] - asreq_resolved['신청일']).dt.days

# ── KPI ──────────────────────────────────────────────
total_calls    = len(calls)
avg_duration   = calls['상담시간(분)'].mean()
avg_rating     = calls['상담평가'].mean()
recall_rate    = (calls['재상담필요'] == True).mean() * 100
total_as       = len(asreq)
as_complete    = len(asreq[asreq['완료일'].notna()])
urgent_pending = len(asreq[(asreq['심각도'] == '긴급') & (asreq['완료일'].isna())])

c1, c2, c3, c4 = st.columns(4)
c1.metric("총 상담 건수",     f"{total_calls:,}")
c2.metric("평균 상담시간",    f"{avg_duration:.1f}분")
c3.metric("평균 상담 평가",   f"{avg_rating:.2f}/5")
c4.metric("재상담 필요율",    f"{recall_rate:.1f}%",
          delta="높음" if recall_rate > 20 else "양호",
          delta_color="inverse" if recall_rate > 20 else "normal")

c5, c6, c7, c8 = st.columns(4)
c5.metric("총 A/S 건수",     f"{total_as:,}")
c6.metric("A/S 완료율",      f"{as_complete/max(total_as,1)*100:.1f}%")
c7.metric("평균 처리시간",   f"{asreq_resolved['처리시간(일)'].mean():.1f}일" if not asreq_resolved.empty else "N/A")
c8.metric("긴급 미처리",     f"{urgent_pending:,}건",
          delta="즉시대응" if urgent_pending > 0 else "없음",
          delta_color="inverse" if urgent_pending > 0 else "off")

st.markdown("---")

# ── A/S 심각도·분류 ────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("🚨 A/S 심각도별 현황")
    sev_counts = asreq['심각도'].value_counts()
    color_map = {'긴급': COLORS['danger'], '높음': COLORS['warning'],
                 '중간': COLORS['primary'], '낮음': COLORS['success']}
    sev_colors = [color_map.get(s, COLORS['neutral']) for s in sev_counts.index]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(sev_counts.index, sev_counts.values, color=sev_colors, alpha=0.85)
    ax.bar_label(bars, fmt='%d', padding=3)
    ax.set_ylabel("건수")
    ax.set_title("A/S 심각도별 접수 현황")
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

with col2:
    st.subheader("🔧 A/S 분류별 처리 현황")
    class_stats = asreq.groupby('분류').agg(
        총건수=('AS신청ID', 'count'),
        완료건수=('완료일', lambda x: x.notna().sum())
    ).reset_index()
    class_stats['미완료'] = class_stats['총건수'] - class_stats['완료건수']

    fig, ax = plt.subplots(figsize=(7, 4))
    x = range(len(class_stats))
    ax.bar(x, class_stats['완료건수'], color=COLORS['success'], alpha=0.85, label='완료')
    ax.bar(x, class_stats['미완료'], bottom=class_stats['완료건수'],
           color=COLORS['danger'], alpha=0.85, label='미완료')
    ax.set_xticks(x)
    ax.set_xticklabels(class_stats['분류'])
    ax.set_ylabel("건수")
    ax.set_title("A/S 분류별 완료·미완료")
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

st.markdown("---")

# ── 상담원 성과 ───────────────────────────────────────
st.subheader("👩‍💼 상담원 성과 분석")
staff_stats = calls.groupby('상담원ID').agg(
    상담건수=('상담ID', 'count'),
    평균평가=('상담평가', 'mean'),
    평균시간=('상담시간(분)', 'mean'),
    재상담율=('재상담필요', lambda x: (x == True).mean() * 100)
).reset_index().sort_values('평균평가', ascending=False)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**상담원 TOP 15 평균 평가**")
    top15 = staff_stats.head(15)
    fig, ax = plt.subplots(figsize=(7, 6))
    colors_bar = [COLORS['success'] if v >= 4.0 else COLORS['warning'] if v >= 3.0 else COLORS['danger']
                  for v in top15['평균평가']]
    bars = ax.barh(top15['상담원ID'], top15['평균평가'], color=colors_bar, alpha=0.85)
    ax.bar_label(bars, fmt='%.2f', padding=3)
    ax.set_xlim(0, 5.5)
    ax.axvline(4.0, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    ax.set_xlabel("평균 평가")
    ax.set_title("상담원별 평균 평가 점수")
    ax.invert_yaxis()
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

with col2:
    st.markdown("**상담원 성과 상세**")
    display_df = staff_stats[['상담원ID','상담건수','평균평가','평균시간','재상담율']].head(15).copy()
    display_df['평균평가'] = display_df['평균평가'].round(2)
    display_df['평균시간'] = display_df['평균시간'].round(1)
    display_df['재상담율'] = display_df['재상담율'].round(1).astype(str) + '%'
    st.dataframe(display_df, use_container_width=True, hide_index=True)

st.markdown("---")

# ── 시간대 히트맵 ─────────────────────────────────────
st.subheader("🕐 상담 시간대 × 요일 히트맵")
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_kor   = ['월', '화', '수', '목', '금', '토', '일']
day_map   = dict(zip(day_order, day_kor))
calls['요일_kor'] = calls['요일'].map(day_map)

heatmap = calls.groupby(['시간대', '요일_kor']).size().unstack(fill_value=0)
heatmap = heatmap.reindex(columns=day_kor, fill_value=0)

fig, ax = plt.subplots(figsize=(12, 5))
im = ax.imshow(heatmap.values, cmap='YlOrRd', aspect='auto')
ax.set_xticks(range(len(day_kor)))
ax.set_xticklabels(day_kor)
ax.set_yticks(range(len(heatmap.index)))
ax.set_yticklabels([f"{h}시" for h in heatmap.index])
for i in range(len(heatmap.index)):
    for j in range(len(day_kor)):
        val = heatmap.values[i, j]
        if val > 0:
            ax.text(j, i, val, ha='center', va='center', fontsize=8,
                    color='white' if val > heatmap.values.max() * 0.6 else 'black')
plt.colorbar(im, ax=ax, label='상담 건수')
ax.set_title("시간대 × 요일별 상담 집중도")
plt.tight_layout()
st.pyplot(fig, use_container_width=True)

st.markdown("---")

# ── A/S 미완료 목록 & 긴급 알람 ──────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("🚨 긴급 A/S 미처리 목록")
    urgent_list = asreq[(asreq['심각도'] == '긴급') & (asreq['완료일'].isna())].copy()
    urgent_list = urgent_list.merge(customers[['고객ID','지역','고객타입']], on='고객ID', how='left')
    st.dataframe(
        urgent_list[['AS신청ID','고객ID','지역','분류','신청일']].sort_values('신청일'),
        use_container_width=True, hide_index=True
    )

with col2:
    st.subheader("📅 월별 A/S 신청 추이")
    asreq['년월'] = asreq['신청일'].dt.to_period('M').astype(str)
    monthly_as = asreq.groupby(['년월','심각도']).size().unstack(fill_value=0)
    month_list = sorted(monthly_as.index)

    fig, ax = plt.subplots(figsize=(7, 4))
    bottom = np.zeros(len(month_list))
    severity_order = ['긴급', '높음', '중간', '낮음']
    sev_colors2 = [COLORS['danger'], COLORS['warning'], COLORS['primary'], COLORS['success']]
    for sev, color in zip(severity_order, sev_colors2):
        if sev in monthly_as.columns:
            vals = [monthly_as.loc[m, sev] if m in monthly_as.index else 0 for m in month_list]
            ax.bar(range(len(month_list)), vals, bottom=bottom, color=color, alpha=0.85, label=sev)
            bottom += np.array(vals)
    ax.set_xticks(range(len(month_list)))
    ax.set_xticklabels(month_list, rotation=45, fontsize=8)
    ax.set_ylabel("A/S 건수")
    ax.set_title("월별 A/S 신청 추이 (심각도별)")
    ax.legend(loc='upper right', fontsize=8)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
