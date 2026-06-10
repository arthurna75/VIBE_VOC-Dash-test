import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import sys
import io

# 인코딩 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 시드 설정
np.random.seed(42)
random.seed(42)

# 기본 설정
regions = ['서울', '경기', '인천', '대전', '대구', '부산', '광주', '울산', '세종', '강원']
customer_types = ['주택', '상업', '산업', '공공']
satisfaction_scores = [1, 2, 3, 4, 5]
complaint_categories = ['요금', '공급', '서비스', '안전', '기술', '기타']
complaint_statuses = ['접수', '처리중', '완료', '보류']

start_date = datetime(2023, 1, 1)
end_date = datetime(2024, 12, 31)

# 1. 고객 정보 데이터
print("생성중: customers.csv...")
num_customers = 5000
customers = {
    '고객ID': [f'CUST{i:06d}' for i in range(1, num_customers + 1)],
    '가입일': [start_date + timedelta(days=random.randint(0, 365)) for _ in range(num_customers)],
    '지역': np.random.choice(regions, num_customers),
    '고객타입': np.random.choice(customer_types, num_customers),
    '계약기간': np.random.choice(['1년', '2년', '장기'], num_customers),
    '요금제': np.random.choice(['기본', '할인', '프리미엄'], num_customers),
}
df_customers = pd.DataFrame(customers)
df_customers.to_csv('customers.csv', index=False, encoding='utf-8-sig')
print(f"✓ customers.csv 생성 완료 ({len(df_customers)} 행)")

# 2. 월별 사용량 데이터
print("생성중: usage_data.csv...")
usage_records = []
for customer_id in df_customers['고객ID']:
    customer_type = df_customers[df_customers['고객ID'] == customer_id]['고객타입'].values[0]

    # 고객타입별 평균 사용량
    avg_usage = {
        '주택': 30,
        '상업': 150,
        '산업': 500,
        '공공': 200
    }[customer_type]

    # 12개월 데이터
    for month in range(1, 13):
        date = datetime(2024, month, 15)
        usage = max(5, np.random.normal(avg_usage, avg_usage * 0.3))
        charge = usage * np.random.uniform(900, 1200)

        usage_records.append({
            '고객ID': customer_id,
            '년월': date.strftime('%Y-%m'),
            '사용량(㎥)': round(usage, 2),
            '요금(원)': round(charge),
            '납부상태': np.random.choice(['납부', '연체', '면제'], p=[0.85, 0.10, 0.05])
        })

df_usage = pd.DataFrame(usage_records)
df_usage.to_csv('usage_data.csv', index=False, encoding='utf-8-sig')
print(f"✓ usage_data.csv 생성 완료 ({len(df_usage)} 행)")

# 3. 고객 불만 데이터
print("생성중: complaints.csv...")
num_complaints = 2000
complaints = {
    '불만ID': [f'COMP{i:06d}' for i in range(1, num_complaints + 1)],
    '고객ID': np.random.choice(df_customers['고객ID'], num_complaints),
    '접수일시': [start_date + timedelta(days=random.randint(0, 730), hours=random.randint(0, 23))
                 for _ in range(num_complaints)],
    '카테고리': np.random.choice(complaint_categories, num_complaints),
    '내용': [random.choice([
        '요금이 지난달보다 많이 나왔어요',
        '공급이 자주 끊겨요',
        '고객센터 응답이 느려요',
        '가스 냄새가 심합니다',
        '계약 변경이 어려워요',
        '청구서 오류가 있습니다',
        '정기점검을 안 해줬어요',
        '앱 사용이 불편해요',
        '환불이 안 되네요',
        '상담원 친절도가 떨어져요'
    ]) for _ in range(num_complaints)],
    '상태': np.random.choice(complaint_statuses, num_complaints, p=[0.2, 0.2, 0.5, 0.1]),
    '만족도': np.random.choice(satisfaction_scores, num_complaints),
    '해결완료일': [None if random.random() > 0.6 else
                    (start_date + timedelta(days=random.randint(0, 730))).strftime('%Y-%m-%d')
                    for _ in range(num_complaints)]
}
df_complaints = pd.DataFrame(complaints)
df_complaints.to_csv('complaints.csv', index=False, encoding='utf-8-sig')
print(f"✓ complaints.csv 생성 완료 ({len(df_complaints)} 행)")

# 4. A/S 신청 데이터
print("생성중: as_requests.csv...")
num_as = 1500
as_requests = {
    'AS신청ID': [f'AS{i:06d}' for i in range(1, num_as + 1)],
    '고객ID': np.random.choice(df_customers['고객ID'], num_as),
    '신청일': [start_date + timedelta(days=random.randint(0, 730)) for _ in range(num_as)],
    '분류': np.random.choice(['점검', '수리', '설치', '폐기', '기술상담'], num_as),
    '심각도': np.random.choice(['낮음', '중간', '높음', '긴급'], num_as, p=[0.3, 0.4, 0.2, 0.1]),
    '완료일': [None if random.random() > 0.75 else
              (start_date + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
              for _ in range(num_as)],
    '기술자만족도': [None if random.random() > 0.7 else random.choice([1, 2, 3, 4, 5])
                   for _ in range(num_as)]
}
df_as = pd.DataFrame(as_requests)
df_as.to_csv('as_requests.csv', index=False, encoding='utf-8-sig')
print(f"✓ as_requests.csv 생성 완료 ({len(df_as)} 행)")

# 5. 고객 센터 상담 기록
print("생성중: call_logs.csv...")
num_calls = 3000
call_logs = {
    '상담ID': [f'CALL{i:06d}' for i in range(1, num_calls + 1)],
    '고객ID': np.random.choice(df_customers['고객ID'], num_calls),
    '상담일시': [start_date + timedelta(days=random.randint(0, 730), hours=random.randint(8, 18))
                for _ in range(num_calls)],
    '상담유형': np.random.choice(['요금조회', '신청', '불만', '기술지원', '홍보'], num_calls),
    '상담시간(분)': np.random.randint(1, 30, num_calls),
    '상담원ID': [f'CS{random.randint(1, 50):02d}' for _ in range(num_calls)],
    '상담평가': np.random.choice(satisfaction_scores, num_calls, p=[0.05, 0.05, 0.15, 0.35, 0.40]),
    '재상담필요': np.random.choice([True, False], num_calls, p=[0.15, 0.85])
}
df_calls = pd.DataFrame(call_logs)
df_calls.to_csv('call_logs.csv', index=False, encoding='utf-8-sig')
print(f"✓ call_logs.csv 생성 완료 ({len(df_calls)} 행)")

# 6. 고객 피드백 텍스트 데이터
print("생성중: feedback.csv...")
num_feedback = 1000
feedback_texts = [
    '서비스가 좋습니다',
    '요금이 비싼 편입니다',
    '앱이 사용하기 편해요',
    '상담원이 친절했습니다',
    '공급이 안정적이네요',
    '청구서가 늦게 와요',
    '기술자가 전문적이었습니다',
    '개선이 필요합니다',
    '만족합니다',
    '불만이 많습니다',
    '계약 과정이 복잡해요',
    '가격이 합리적입니다',
    '신청 처리가 빨라요',
    '고객지원이 부족합니다',
    '다시 이용하고 싶습니다'
]

feedback = {
    '피드백ID': [f'FB{i:06d}' for i in range(1, num_feedback + 1)],
    '고객ID': np.random.choice(df_customers['고객ID'], num_feedback),
    '등록일': [start_date + timedelta(days=random.randint(0, 730)) for _ in range(num_feedback)],
    '내용': np.random.choice(feedback_texts, num_feedback),
    '평가점수': np.random.choice(satisfaction_scores, num_feedback, p=[0.05, 0.05, 0.15, 0.35, 0.40]),
    '유형': np.random.choice(['칭찬', '건의', '불만'], num_feedback, p=[0.30, 0.40, 0.30])
}
df_feedback = pd.DataFrame(feedback)
df_feedback.to_csv('feedback.csv', index=False, encoding='utf-8-sig')
print(f"✓ feedback.csv 생성 완료 ({len(df_feedback)} 행)")

print("\n" + "="*50)
print("✓ 모든 CSV 파일 생성 완료!")
print("="*50)
print(f"생성된 파일:")
print(f"  1. customers.csv - 고객 정보 ({len(df_customers)} 행)")
print(f"  2. usage_data.csv - 월별 사용량 ({len(df_usage)} 행)")
print(f"  3. complaints.csv - 고객 불만 ({len(df_complaints)} 행)")
print(f"  4. as_requests.csv - A/S 신청 ({len(df_as)} 행)")
print(f"  5. call_logs.csv - 상담 기록 ({len(df_calls)} 행)")
print(f"  6. feedback.csv - 고객 피드백 ({len(df_feedback)} 행)")
