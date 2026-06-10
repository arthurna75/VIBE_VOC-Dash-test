# 🔥 도시가스 고객 현황 대시보드

Streamlit 기반 도시가스 고객 데이터 분석 대시보드 + Gemini AI 분석 어시스턴트

## 📋 페이지 구성

| 페이지 | 내용 |
|--------|------|
| 📊 전체 요약 | KPI 카드, 지역별 분포, 월별 추이 |
| 👤 고객 360도 뷰 | 개별 고객 프로필·이력·만족도 |
| 😠 불만·민원 분석 | 카테고리·처리현황·처리시간 |
| 💬 고객의 소리 VOC | 감정분석·키워드·개선 우선순위 |
| 📈 사용량·요금 | 타입별 사용량·연체·이상 탐지 |
| 🛠 A/S·상담 운영 | A/S 현황·상담원 성과·시간대 분포 |
| 🤖 AI 분석 어시스턴트 | Gemini 기반 데이터 질의응답 |

## ⚙️ 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/arthurna75/VIBE_VOC-Dash-test.git
cd VIBE_VOC-Dash-test
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 아래 내용을 입력합니다.

```
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-flash-latest
```

> Gemini API 키는 [Google AI Studio](https://aistudio.google.com/app/apikey)에서 발급받을 수 있습니다.

### 4. 실행

```bash
streamlit run dashboard.py
```

기본 포트는 `8501`입니다. 포트를 변경하려면:

```bash
streamlit run dashboard.py --server.port 8503
```

## 📦 주요 의존성

| 패키지 | 용도 |
|--------|------|
| streamlit | 대시보드 UI |
| pandas / numpy | 데이터 처리 |
| matplotlib | 차트 시각화 |
| google-genai | Gemini AI API |
| python-dotenv | 환경변수 로드 |

## 📁 프로젝트 구조

```
.
├── dashboard.py              # 메인 진입점
├── utils.py                  # 공통 함수 (데이터 로드, Gemini 클라이언트 등)
├── requirements.txt
├── .env                      # API 키 (git 미포함)
├── pages/
│   ├── 1_overview.py
│   ├── 2_customer_360.py
│   ├── 3_complaint_analysis.py
│   ├── 4_voc_analysis.py
│   ├── 5_usage_billing.py
│   ├── 6_service_ops.py
│   └── ai_chat.py            # AI 분석 어시스턴트
└── *.csv                     # 샘플 데이터
```
