import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from collections import Counter
import re
from wordcloud import WordCloud

# 페이지 설정
st.set_page_config(
    page_title="고객의 소리 분석",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
sns.set_style("whitegrid")

@st.cache_data
def load_data():
    """데이터 로드"""
    customers = pd.read_csv('customers.csv')
    complaints = pd.read_csv('complaints.csv')
    feedback = pd.read_csv('feedback.csv')
    call_logs = pd.read_csv('call_logs.csv')

    # 날짜 변환
    complaints['접수일시'] = pd.to_datetime(complaints['접수일시'])
    feedback['등록일'] = pd.to_datetime(feedback['등록일'])
    call_logs['상담일시'] = pd.to_datetime(call_logs['상담일시'])

    return customers, complaints, feedback, call_logs

def analyze_sentiment(text):
    """간단한 감정 분석 (키워드 기반)"""
    positive_words = ['좋', '훌륭', '만족', '친절', '빠', '편', '안정', '전문', '합리', '만족']
    negative_words = ['나쁨', '불만', '느림', '비싼', '복잡', '어려움', '부족', '문제', '오류']

    text_lower = text.lower()

    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)

    if pos_count > neg_count:
        return '긍정'
    elif neg_count > pos_count:
        return '부정'
    else:
        return '중립'

def extract_keywords(texts, top_n=20):
    """키워드 추출"""
    # 간단한 단어 분리 (2글자 이상)
    words = []
    for text in texts:
        # 한글만 추출
        korean_text = re.findall(r'[\w가-힣]{2,}', str(text))
        words.extend(korean_text)

    # 불용어 제거
    stopwords = ['수', '있', '있어', '없', '이', '그', '저', '것', '주', '합', '나', '가', '해', '있습니다']
    words = [w for w in words if w not in stopwords and len(w) >= 2]

    return Counter(words).most_common(top_n)

# 데이터 로드
customers, complaints, feedback, call_logs = load_data()

# 제목
st.title("📢 고객의 소리 분석 대시보드")
st.markdown("---")

# 사이드바 필터
st.sidebar.header("필터 설정")
analysis_type = st.sidebar.radio(
    "분석 유형",
    ["전체 분석", "불만 분석", "피드백 분석", "상담 분석"]
)

# 날짜 범위 필터
date_range = st.sidebar.slider(
    "분석 기간",
    value=(30, 365),
    min_value=0,
    max_value=365,
    label_visibility="visible"
)

# 컬럼 정의
col1, col2, col3, col4 = st.columns(4)

if analysis_type == "전체 분석":
    # 전체 통계
    total_complaints = len(complaints)
    total_feedback = len(feedback)
    total_calls = len(call_logs)
    avg_satisfaction = (complaints['만족도'].mean() + feedback['평가점수'].mean() + call_logs['상담평가'].mean()) / 3

    with col1:
        st.metric("총 불만 접수", f"{total_complaints:,}")
    with col2:
        st.metric("총 피드백", f"{total_feedback:,}")
    with col3:
        st.metric("총 상담", f"{total_calls:,}")
    with col4:
        st.metric("평균 만족도", f"{avg_satisfaction:.2f}/5")

    st.markdown("---")

    # 감정 분석
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💭 전체 감정 분석")

        # 불만과 피드백 텍스트 결합
        all_texts = list(complaints['내용']) + list(feedback['내용'])
        sentiments = [analyze_sentiment(text) for text in all_texts]
        sentiment_counts = pd.Series(sentiments).value_counts()

        fig, ax = plt.subplots(figsize=(8, 5))
        colors = ['#ff6b6b', '#51cf66', '#4dabf7']
        sentiment_counts.plot(kind='pie', ax=ax, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.set_ylabel('')
        ax.set_title('감정 분포', fontsize=14, fontweight='bold')
        st.pyplot(fig, use_container_width=True)

    with col2:
        st.subheader("⭐ 만족도 분포")

        # 만족도 분포
        fig, ax = plt.subplots(figsize=(8, 5))

        complaints_satisfaction = complaints['만족도'].value_counts().sort_index()
        feedback_satisfaction = feedback['평가점수'].value_counts().sort_index()
        call_satisfaction = call_logs['상담평가'].value_counts().sort_index()

        x = np.arange(1, 6)
        width = 0.25

        ax.bar(x - width, [complaints_satisfaction.get(i, 0) for i in x], width, label='불만', alpha=0.8)
        ax.bar(x, [feedback_satisfaction.get(i, 0) for i in x], width, label='피드백', alpha=0.8)
        ax.bar(x + width, [call_satisfaction.get(i, 0) for i in x], width, label='상담', alpha=0.8)

        ax.set_xlabel('만족도')
        ax.set_ylabel('건수')
        ax.set_title('만족도 비교', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.legend()
        st.pyplot(fig, use_container_width=True)

    # 시계열 분석
    st.subheader("📈 월별 추이")
    col1, col2 = st.columns(2)

    with col1:
        # 불만 월별 추이
        complaints['년월'] = complaints['접수일시'].dt.to_period('M').astype(str)
        complaint_monthly = complaints.groupby('년월').size()

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(range(len(complaint_monthly)), complaint_monthly.values, marker='o', linewidth=2, markersize=6)
        ax.set_xlabel('월')
        ax.set_ylabel('불만 건수')
        ax.set_title('월별 불만 접수 추이', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        st.pyplot(fig, use_container_width=True)

    with col2:
        # 피드백 월별 추이
        feedback['년월'] = feedback['등록일'].dt.to_period('M').astype(str)
        feedback_monthly = feedback.groupby('년월').size()

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(range(len(feedback_monthly)), feedback_monthly.values, marker='s', linewidth=2,
                markersize=6, color='orange')
        ax.set_xlabel('월')
        ax.set_ylabel('피드백 건수')
        ax.set_title('월별 피드백 등록 추이', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        st.pyplot(fig, use_container_width=True)

elif analysis_type == "불만 분석":
    st.subheader("😠 고객 불만 분석")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 불만", len(complaints))
    with col2:
        resolved = len(complaints[complaints['상태'] == '완료'])
        st.metric("해결 완료", f"{resolved} ({resolved/len(complaints)*100:.1f}%)")
    with col3:
        pending = len(complaints[complaints['상태'] == '처리중'])
        st.metric("처리 중", f"{pending} ({pending/len(complaints)*100:.1f}%)")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 카테고리별 불만")
        category_counts = complaints['카테고리'].value_counts()

        fig, ax = plt.subplots(figsize=(8, 5))
        category_counts.plot(kind='barh', ax=ax, color='#ff6b6b')
        ax.set_xlabel('건수')
        ax.set_title('불만 카테고리 분포', fontsize=12, fontweight='bold')
        st.pyplot(fig, use_container_width=True)

    with col2:
        st.subheader("⚡ 처리 상태")
        status_counts = complaints['상태'].value_counts()

        fig, ax = plt.subplots(figsize=(8, 5))
        colors_status = {'접수': '#ffd93d', '처리중': '#ff6b6b', '완료': '#51cf66', '보류': '#adb5bd'}
        status_colors = [colors_status.get(status, '#666') for status in status_counts.index]
        status_counts.plot(kind='pie', ax=ax, colors=status_colors, autopct='%1.1f%%', startangle=90)
        ax.set_ylabel('')
        ax.set_title('처리 상태 분포', fontsize=12, fontweight='bold')
        st.pyplot(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🔤 주요 불만 키워드")
    keywords = extract_keywords(complaints['내용'], top_n=20)

    # 키워드 테이블
    keyword_df = pd.DataFrame(keywords, columns=['키워드', '빈도'])
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(range(len(keyword_df)), keyword_df['빈도'], color='#4dabf7')
    ax.set_yticks(range(len(keyword_df)))
    ax.set_yticklabels(keyword_df['키워드'])
    ax.set_xlabel('언급 빈도')
    ax.set_title('고객 불만 주요 키워드', fontsize=12, fontweight='bold')
    ax.invert_yaxis()
    st.pyplot(fig, use_container_width=True)

elif analysis_type == "피드백 분석":
    st.subheader("💬 고객 피드백 분석")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 피드백", len(feedback))
    with col2:
        avg_rating = feedback['평가점수'].mean()
        st.metric("평균 평가", f"{avg_rating:.2f}/5")
    with col3:
        positive = len(feedback[feedback['유형'] == '칭찬'])
        st.metric("칭찬", f"{positive} ({positive/len(feedback)*100:.1f}%)")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📝 피드백 유형")
        type_counts = feedback['유형'].value_counts()

        fig, ax = plt.subplots(figsize=(8, 5))
        colors_type = {'칭찬': '#51cf66', '건의': '#4dabf7', '불만': '#ff6b6b'}
        type_colors = [colors_type.get(t, '#666') for t in type_counts.index]
        type_counts.plot(kind='pie', ax=ax, colors=type_colors, autopct='%1.1f%%', startangle=90)
        ax.set_ylabel('')
        ax.set_title('피드백 유형 분포', fontsize=12, fontweight='bold')
        st.pyplot(fig, use_container_width=True)

    with col2:
        st.subheader("⭐ 평가 점수 분포")
        rating_counts = feedback['평가점수'].value_counts().sort_index()

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(rating_counts.index, rating_counts.values, color='#ffd93d', edgecolor='black')
        ax.set_xlabel('평가 점수')
        ax.set_ylabel('건수')
        ax.set_title('평가 점수 분포', fontsize=12, fontweight='bold')
        ax.set_xticks([1, 2, 3, 4, 5])
        st.pyplot(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🔤 주요 피드백 키워드")
    keywords = extract_keywords(feedback['내용'], top_n=20)

    keyword_df = pd.DataFrame(keywords, columns=['키워드', '빈도'])
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(range(len(keyword_df)), keyword_df['빈도'], color='#51cf66')
    ax.set_yticks(range(len(keyword_df)))
    ax.set_yticklabels(keyword_df['키워드'])
    ax.set_xlabel('언급 빈도')
    ax.set_title('고객 피드백 주요 키워드', fontsize=12, fontweight='bold')
    ax.invert_yaxis()
    st.pyplot(fig, use_container_width=True)

elif analysis_type == "상담 분석":
    st.subheader("☎️ 고객센터 상담 분석")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 상담", len(call_logs))
    with col2:
        avg_duration = call_logs['상담시간(분)'].mean()
        st.metric("평균 상담시간", f"{avg_duration:.1f}분")
    with col3:
        avg_rating = call_logs['상담평가'].mean()
        st.metric("평균 평가", f"{avg_rating:.2f}/5")
    with col4:
        need_recall = len(call_logs[call_logs['재상담필요'] == True])
        st.metric("재상담 필요", f"{need_recall} ({need_recall/len(call_logs)*100:.1f}%)")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📞 상담유형별 분포")
        type_counts = call_logs['상담유형'].value_counts()

        fig, ax = plt.subplots(figsize=(8, 5))
        type_counts.plot(kind='pie', ax=ax, autopct='%1.1f%%', startangle=90)
        ax.set_ylabel('')
        ax.set_title('상담유형 분포', fontsize=12, fontweight='bold')
        st.pyplot(fig, use_container_width=True)

    with col2:
        st.subheader("📊 상담원별 평가")
        staff_stats = call_logs.groupby('상담원ID').agg({
            '상담평가': 'mean',
            '상담ID': 'count'
        }).rename(columns={'상담평가': '평균평가', '상담ID': '상담건수'})
        staff_stats = staff_stats.sort_values('평균평가', ascending=False).head(10)

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh(range(len(staff_stats)), staff_stats['평균평가'], color='#4dabf7')
        ax.set_yticks(range(len(staff_stats)))
        ax.set_yticklabels(staff_stats.index)
        ax.set_xlabel('평균 평가')
        ax.set_title('상담원 TOP 10 평가', fontsize=12, fontweight='bold')
        ax.set_xlim(0, 5)
        st.pyplot(fig, use_container_width=True)

# 하단 상세 데이터 테이블
st.markdown("---")
st.subheader("📋 상세 데이터")

if analysis_type == "전체 분석":
    tab1, tab2, tab3 = st.tabs(["불만", "피드백", "상담"])
    with tab1:
        st.dataframe(complaints.head(20), use_container_width=True)
    with tab2:
        st.dataframe(feedback.head(20), use_container_width=True)
    with tab3:
        st.dataframe(call_logs.head(20), use_container_width=True)
elif analysis_type == "불만 분석":
    st.dataframe(complaints.head(30), use_container_width=True)
elif analysis_type == "피드백 분석":
    st.dataframe(feedback.head(30), use_container_width=True)
else:
    st.dataframe(call_logs.head(30), use_container_width=True)

st.markdown("---")
st.caption("마지막 업데이트: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
