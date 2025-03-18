import hmac
import hashlib
import time
import requests # type: ignore
import json
import psycopg2
from psycopg2.extras import DictCursor  # extras에서 DictCursor 직접 import
from urllib.parse import quote, urlencode

# [okay]1. 쿠팡 파트너스 API 키 설정 및 onboarding 암호화
# DB에서 식품데이터 가져오기 (naming)
# [okay]3. 쿠팡 api 호출 및 제품 URL  + utm_link 생성(Partners API 생성)
# 4. DB에 저장 + secondFit 
# 5. cloud lambda에 배포(1주일 마다)
# 6. utm URL이 없는 것은 어떻게? 채워넣기. 


# 쿠팡 파트너스 API 키 설정
ACCESS_KEY = 'YOUR_ACCESS_KEY'  # 자신의 Access Key 입력
SECRET_KEY = 'YOUR_SECRET_KEY'  # 자신의 Secret Key 입력

def getFoodANDUpdateDataFromDB()->str:
    conn = psycopg2.connect(
        dbname="testDB",
        user="kang",
        password="1234",
        host="localhost",
        port="5454"  # 기본 포트
    )
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM food_nutrition WHERE \"isAI\" = true limit 10")
    rows = cur.fetchall()

    for row in rows:
        search_result = search_products(row["name"])
        if search_result.get('data'):
            product_url = search_result['data'][0]['productUrl']  #[0]은 첫번째 상품을 의미
            partner_link_result = generate_partner_link([product_url])
            if partner_link_result.get('data'):
                partner_link = partner_link_result['data'][0]['shortenUrl']
                utm_link = add_utm_parameters(partner_link, 'newsletter', 'email', 'spring_sale')
                print(f"최종 UTM 링크: {utm_link}")

                # DB Update
                cur.execute("UPDATE food_nutrition SET utmLink = %s WHERE id = %s", (utm_link, row["id"]))
            else:
                print("파트너스 링크 생성 실패:", partner_link_result)
        else:
            print("상품 검색 실패 또는 결과 없음:", row["name"])

    cur.close()
    conn.close()

    return "무선 키보드"

# API 요청을 위한 HMAC 생성 함수
def generate_hmac(method, url, secret_key, access_key):
    path, *query = url.split('?')
    datetime = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    message = f"{datetime}{method}{path}{query[0] if query else ''}"
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime}, signature={signature}"

# 상품 검색 함수
def search_products(keyword, limit=10):
    method = 'GET'
    domain = 'https://api-gateway.coupang.com'
    url = f"/v2/providers/affiliate_open_api/apis/openapi/products/search?keyword={quote(keyword)}&limit={limit}"
    authorization = generate_hmac(method, url, SECRET_KEY, ACCESS_KEY)
    response = requests.get(f"{domain}{url}", headers={'Authorization': authorization, 'Content-Type': 'application/json'})
    return response.json()

# 파트너스 링크 생성 함수
def generate_partner_link(coupang_urls):
    method = 'POST'
    domain = 'https://api-gateway.coupang.com'
    url = '/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink'
    authorization = generate_hmac(method, url, SECRET_KEY, ACCESS_KEY)
    data = {'coupangUrls': coupang_urls}
    response = requests.post(f"{domain}{url}", headers={'Authorization': authorization, 'Content-Type': 'application/json'}, data=json.dumps(data))
    return response.json()

# UTM 파라미터 추가 함수
def add_utm_parameters(url, source, medium, campaign):
    utm_params = {'utm_source': source, 'utm_medium': medium, 'utm_campaign': campaign}
    return f"{url}?{urlencode(utm_params)}"

# 실행 예제
if __name__ == "__main__":
    getFoodANDUpdateDataFromDB()
