import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import streamlit as st
import os

# 한글 폰트 설정
matplotlib.rc('font', family='Malgun Gothic')
matplotlib.rcParams['axes.unicode_minus'] = False

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def load_all_data():
    def _csv(name):
        return os.path.join(_BASE_DIR, name)

    customers   = pd.read_csv(_csv('customers.csv'),   encoding='utf-8-sig')
    complaints  = pd.read_csv(_csv('complaints.csv'),  encoding='utf-8-sig')
    feedback    = pd.read_csv(_csv('feedback.csv'),    encoding='utf-8-sig')
    call_logs   = pd.read_csv(_csv('call_logs.csv'),   encoding='utf-8-sig')
    as_requests = pd.read_csv(_csv('as_requests.csv'), encoding='utf-8-sig')
    usage_data  = pd.read_csv(_csv('usage_data.csv'),  encoding='utf-8-sig')

    # 날짜 파싱
    customers['가입일']       = pd.to_datetime(customers['가입일'])
    complaints['접수일시']    = pd.to_datetime(complaints['접수일시'])
    complaints['해결완료일']  = pd.to_datetime(complaints['해결완료일'], errors='coerce')
    feedback['등록일']        = pd.to_datetime(feedback['등록일'])
    call_logs['상담일시']     = pd.to_datetime(call_logs['상담일시'])
    as_requests['신청일']     = pd.to_datetime(as_requests['신청일'])
    as_requests['완료일']     = pd.to_datetime(as_requests['완료일'], errors='coerce')

    return customers, complaints, feedback, call_logs, as_requests, usage_data


def sidebar_filters(customers):
    """사이드바 공통 필터 반환"""
    st.sidebar.header("🔍 필터")

    regions = ['전체'] + sorted(customers['지역'].unique().tolist())
    region = st.sidebar.selectbox("지역", regions)

    types = ['전체'] + sorted(customers['고객타입'].unique().tolist())
    ctype = st.sidebar.selectbox("고객 타입", types)

    return region, ctype


def apply_customer_filter(customers, region, ctype):
    df = customers.copy()
    if region != '전체':
        df = df[df['지역'] == region]
    if ctype != '전체':
        df = df[df['고객타입'] == ctype]
    return df


def kpi_card(col, label, value, delta=None, delta_color="normal"):
    col.metric(label=label, value=value, delta=delta, delta_color=delta_color)


COLORS = {
    'primary':  '#4361EE',
    'success':  '#4CC9A0',
    'warning':  '#F7B731',
    'danger':   '#EE4343',
    'neutral':  '#ADB5BD',
    'bg':       '#F8F9FA',
}

PALETTE = [COLORS['primary'], COLORS['success'], COLORS['warning'],
           COLORS['danger'], COLORS['neutral'], '#9B59B6']


def build_data_context(customers, complaints, feedback, call_logs, as_requests, usage_data):
    """데이터 현황 요약 문자열을 생성해 AI 시스템 프롬프트로 제공"""
    total_customers = len(customers)
    overdue = usage_data[usage_data['납부상태'] == '연체']['고객ID'].nunique()
    overdue_rate = overdue / max(total_customers, 1) * 100
    unresolved = len(complaints[complaints['상태'].isin(['접수', '처리중'])])
    avg_sat = pd.concat([complaints['만족도'], feedback['평가점수'], call_logs['상담평가']]).mean()
    region_dist = customers['지역'].value_counts().to_dict()
    type_dist = customers['고객타입'].value_counts().to_dict()
    comp_cat = complaints['카테고리'].value_counts().head(5).to_dict()
    urgent_as = len(as_requests[as_requests['심각도'] == '긴급'])

    return f"""당신은 도시가스 회사의 고객 데이터 분석 전문 AI 어시스턴트입니다.
아래는 현재 대시보드의 실시간 데이터 현황입니다. 이 데이터를 바탕으로 사용자의 질문에 답하세요.

[현재 데이터 현황]
- 전체 고객 수: {total_customers:,}명
- 연체 고객: {overdue:,}명 ({overdue_rate:.1f}%)
- 미처리 불만/민원: {unresolved:,}건
- 평균 만족도: {avg_sat:.2f} / 5.0
- 긴급 A/S 건수: {urgent_as:,}건

[지역별 고객 분포]
{chr(10).join(f'  - {k}: {v:,}명' for k, v in region_dist.items())}

[고객 타입 구성]
{chr(10).join(f'  - {k}: {v:,}명' for k, v in type_dist.items())}

[불만 카테고리 상위 5개]
{chr(10).join(f'  - {k}: {v:,}건' for k, v in comp_cat.items())}

답변은 한국어로, 데이터 수치를 구체적으로 인용하며 답하세요.
대시보드에 없는 정보를 추측하지 말고, 데이터 범위를 벗어나는 질문에는 그렇다고 명시하세요."""


@st.cache_resource
def get_gemini_client():
    from google import genai
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 secrets.toml 또는 환경변수에 설정되지 않았습니다.")
    return genai.Client(api_key=api_key)


def get_gemini_model_name():
    return st.secrets.get("GEMINI_MODEL") or os.getenv("GEMINI_MODEL", "gemini-flash-latest")
