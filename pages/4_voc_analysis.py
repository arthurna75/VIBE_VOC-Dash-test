import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import re
from collections import Counter
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import load_all_data, sidebar_filters, apply_customer_filter, COLORS, PALETTE

st.set_page_config(page_title="고객의 소리 VOC", page_icon="💬", layout="wide")
st.title("💬 고객의 소리 VOC 분석")

customers, complaints, feedback, call_logs, as_requests, usage_data = load_all_data()
region, ctype = sidebar_filters(customers)
filtered_customers = apply_customer_filter(customers, region, ctype)
cids = set(filtered_customers['고객ID'])

comp = complaints[complaints['고객ID'].isin(cids)].copy()
fb   = feedback[feedback['고객ID'].isin(cids)].copy()

# ── 소스 선택 ────────────────────────────────────────
st.sidebar.markdown("---")
source = st.sidebar.multiselect(
    "분석 데이터 소스",
    ["불만", "피드백"],
    default=["불만", "피드백"]
)

texts_all = []
if "불만" in source:
    texts_all += comp['내용'].dropna().tolist()
if "피드백" in source:
    texts_all += fb['내용'].dropna().tolist()

# 감정 분석 함수
POSITIVE = ['좋', '훌륭', '만족', '친절', '빠르', '편리', '안정', '전문', '합리', '다시']
NEGATIVE = ['나쁨', '불만', '느림', '비싼', '복잡', '어려움', '부족', '문제', '오류', '늦게', '개선']

def classify_sentiment(text):
    pos = sum(1 for w in POSITIVE if w in str(text))
    neg = sum(1 for w in NEGATIVE if w in str(text))
    if pos > neg:   return '긍정'
    elif neg > pos: return '부정'
    return '중립'

def extract_keywords(texts, top_n=20):
    stopwords = {'수', '있어요', '없어요', '이', '그', '저', '것', '주', '합', '나', '가', '해', '있습니다', '합니다', '됩니다'}
    words = []
    for t in texts:
        words += [w for w in re.findall(r'[가-힣]{2,}', str(t)) if w not in stopwords]
    return Counter(words).most_common(top_n)

comp['감정'] = comp['내용'].apply(classify_sentiment)
fb['감정']   = fb['내용'].apply(classify_sentiment)

# ── KPI ──────────────────────────────────────────────
total_voc = len(texts_all)
all_sents = [classify_sentiment(t) for t in texts_all]
sent_counter = Counter(all_sents)
pos_rate = sent_counter['긍정'] / max(total_voc, 1) * 100
neg_rate = sent_counter['부정'] / max(total_voc, 1) * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("총 VOC 건수",   f"{total_voc:,}")
c2.metric("긍정 비율",     f"{pos_rate:.1f}%",  delta="good"  if pos_rate > 50 else "low")
c3.metric("부정 비율",     f"{neg_rate:.1f}%",  delta="high" if neg_rate > 30 else "normal",
          delta_color="inverse" if neg_rate > 30 else "normal")
c4.metric("평균 피드백 평점", f"{fb['평가점수'].mean():.2f}/5" if not fb.empty else "N/A")

st.markdown("---")

# ── 감정 분포 & 피드백 유형 ────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("💭 전체 감정 분포")
    labels = ['긍정', '부정', '중립']
    sizes  = [sent_counter.get(l, 0) for l in labels]
    colors = [COLORS['success'], COLORS['danger'], COLORS['neutral']]
    fig, ax = plt.subplots(figsize=(7, 4))
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                       colors=colors, startangle=90)
    ax.set_title("VOC 감정 분포")
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

with col2:
    st.subheader("📝 피드백 유형별 평균 평점")
    if not fb.empty:
        type_rating = fb.groupby('유형')['평가점수'].mean().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(7, 4))
        color_map = {'칭찬': COLORS['success'], '건의': COLORS['primary'], '불만': COLORS['danger']}
        bar_colors = [color_map.get(t, COLORS['neutral']) for t in type_rating.index]
        bars = ax.bar(type_rating.index, type_rating.values, color=bar_colors, alpha=0.85)
        ax.bar_label(bars, fmt='%.2f', padding=3)
        ax.set_ylim(0, 5.5)
        ax.set_ylabel("평균 평점")
        ax.set_title("피드백 유형별 평균 평점")
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)

st.markdown("---")

# ── 키워드 분석 ───────────────────────────────────────
st.subheader("🔤 주요 키워드 분석")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**전체 키워드 TOP 20**")
    kw = extract_keywords(texts_all, 20)
    if kw:
        kw_df = pd.DataFrame(kw, columns=['키워드', '빈도'])
        fig, ax = plt.subplots(figsize=(7, 6))
        ax.barh(kw_df['키워드'], kw_df['빈도'], color=COLORS['primary'], alpha=0.85)
        ax.set_xlabel("언급 빈도")
        ax.set_title("전체 VOC 주요 키워드")
        ax.invert_yaxis()
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)

with col2:
    st.markdown("**감정별 키워드 비교**")
    pos_texts = [t for t in texts_all if classify_sentiment(t) == '긍정']
    neg_texts = [t for t in texts_all if classify_sentiment(t) == '부정']
    pos_kw = dict(extract_keywords(pos_texts, 10))
    neg_kw = dict(extract_keywords(neg_texts, 10))

    all_words = list(set(list(pos_kw.keys()) + list(neg_kw.keys())))
    pos_vals = [pos_kw.get(w, 0) for w in all_words]
    neg_vals = [-neg_kw.get(w, 0) for w in all_words]

    fig, ax = plt.subplots(figsize=(7, 6))
    y = range(len(all_words))
    ax.barh(y, pos_vals, color=COLORS['success'], alpha=0.8, label='긍정')
    ax.barh(y, neg_vals, color=COLORS['danger'],  alpha=0.8, label='부정')
    ax.set_yticks(y)
    ax.set_yticklabels(all_words, fontsize=9)
    ax.axvline(0, color='black', linewidth=0.8)
    ax.set_xlabel("← 부정    긍정 →")
    ax.set_title("감정별 키워드 분포")
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

st.markdown("---")

# ── 개선 우선순위 매트릭스 ────────────────────────────
st.subheader("🎯 개선 우선순위 매트릭스 (불만 카테고리)")
if not comp.empty:
    cat_stats = comp.groupby('카테고리').agg(
        건수=('불만ID', 'count'),
        부정비율=('감정', lambda x: (x == '부정').mean() * 100),
        평균만족도=('만족도', 'mean')
    ).reset_index()

    fig, ax = plt.subplots(figsize=(9, 5))
    scatter = ax.scatter(
        cat_stats['건수'], cat_stats['부정비율'],
        s=cat_stats['건수'] * 2,
        c=cat_stats['평균만족도'],
        cmap='RdYlGn', vmin=1, vmax=5, alpha=0.85, edgecolors='gray'
    )
    for _, row in cat_stats.iterrows():
        ax.annotate(row['카테고리'], (row['건수'], row['부정비율']),
                    textcoords='offset points', xytext=(6, 4), fontsize=10)
    plt.colorbar(scatter, ax=ax, label='평균 만족도')
    ax.set_xlabel("불만 건수 (많을수록 우선 대응)")
    ax.set_ylabel("부정 비율(%) (높을수록 심각)")
    ax.set_title("개선 우선순위 매트릭스\n(우상단: 즉시 개선 필요)")
    ax.axvline(cat_stats['건수'].median(), color='gray', linestyle='--', alpha=0.5, label='건수 중앙값')
    ax.axhline(cat_stats['부정비율'].median(), color='gray', linestyle=':', alpha=0.5, label='부정비율 중앙값')
    ax.legend(fontsize=8)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

st.markdown("---")

# ── 월별 감정 추이 ────────────────────────────────────
st.subheader("📈 월별 감정 추이")
comp['년월'] = comp['접수일시'].dt.to_period('M').astype(str)
fb['년월']   = fb['등록일'].dt.to_period('M').astype(str)

monthly_sent = comp.groupby(['년월', '감정']).size().unstack(fill_value=0)
all_months = sorted(monthly_sent.index)

fig, ax = plt.subplots(figsize=(12, 4))
for sentiment, color in [('긍정', COLORS['success']), ('부정', COLORS['danger']), ('중립', COLORS['neutral'])]:
    if sentiment in monthly_sent.columns:
        ax.plot(range(len(all_months)),
                [monthly_sent.loc[m, sentiment] if m in monthly_sent.index else 0 for m in all_months],
                marker='o', label=sentiment, color=color, linewidth=2, markersize=5)
ax.set_xticks(range(len(all_months)))
ax.set_xticklabels(all_months, rotation=45, fontsize=8)
ax.set_ylabel("건수")
ax.set_title("월별 감정 추이 (불만 기준)")
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
st.pyplot(fig, use_container_width=True)

st.markdown("---")
st.subheader("📋 피드백 상세")
st.dataframe(fb[['피드백ID','고객ID','등록일','내용','평가점수','유형','감정']].head(30),
             use_container_width=True, hide_index=True)
