import requests
import pandas as pd
from bs4 import BeautifulSoup
import re

# HTML 정제 함수
def clean_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # <p class="bold">를 괄호로 처리
    for p in soup.find_all("p", class_="bold"):
        p.replace_with(f"({p.get_text(strip=True)})")

    # 전체 텍스트 추출
    text = soup.get_text(separator=', ', strip=True)

    # 불필요한 중복 쉼표, 공백 정리
    text = re.sub(r',\s*,', ', ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# 공통 API 정보
base_url = "https://foodqr.kr/openapi/service/qr1007/F007"
params = {
    "accessKey": "",
    "numOfRows": 10,
    "_type": "json"
}

all_items = []

# 페이지 반복
for page in range(1, 24):
    print(f"📦 Fetching page {page}")
    params["pageNo"] = page
    response = requests.get(base_url, params=params)
    response.raise_for_status()

    data = response.json()
    items = data['response']['body']['items']['item']
    if isinstance(items, dict):  # 단일 item일 경우
        items = [items]

    for item in items:
        if "prvwCn" in item:
            item["cleanPrvwCn"] = clean_html(item["prvwCn"])
        else:
            item["cleanPrvwCn"] = None
        all_items.append(item)

# DataFrame 생성 및 저장
df = pd.DataFrame(all_items)
df.to_excel("cleaned_food_items.xlsx", index=False)

print("✅ 모든 페이지 데이터를 'cleaned_food_items.xlsx'로 저장했습니다.")