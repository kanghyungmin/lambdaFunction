import hmac
import hashlib
from time import gmtime, strftime
import requests # type: ignore
import json
import psycopg2
import concurrent.futures
from psycopg2.extras import DictCursor  # extras에서 DictCursor 직접 import
from urllib.parse import quote, urlencode
import time


# 쿠팡 파트너스 API 호출 제한으로 사용 불가.
# - 검색 API: 1분당 50회
# - 리포트 API : 1시간당 500회
# - 모든 API: 1분당 100회
# - 파트너스 웹의 링크생성 기능: 1분당 50회

# 쿠팡 파트너스 API 키 설정
ACCESS_KEY = ''  # 자신의 Access Key 입력
SECRET_KEY = ''  # 자신의 Secret Key 입력'



def process_row(row):
        search_result = search_products(row["name"])
        if search_result.get('data'):
            productList = search_result['data']['productData']
            elementToUpdate = []
            for product in productList:
                print("상품명:", product['productName'])
                partner_link_result = generate_partner_link(["https://www.coupang.com/vp/products/{}".format(product['productId'])])
                if partner_link_result.get('data'):
                    partner_link = partner_link_result['data'][0]['shortenUrl']
                    utm_link = add_utm_parameters(partner_link, 'app', 'banner', 'launching_event')
                    product.update({"utmLink": utm_link})
                    elementToUpdate.append(json.dumps(product))
                else:
                    print("파트너스 링크 생성 실패:", partner_link_result)
            if elementToUpdate:
                return (elementToUpdate, row["id"])
            else:
                return ([], row["id"])
        else:
            print("상품 검색 실패 또는 결과 없음:", row["name"])
            print("검색 결과:", search_result)
        return ([], row["id"])

def getFoodANDUpdateDataFromDB()-> None:
    conn = psycopg2.connect(
        dbname="testDB",
        user="kang",
        password="1234",
        host="localhost",
        port="5454"  # 기본 포트
    )
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM food_nutrition WHERE kind = 'Processed Food' and \"coupangProductInfos\" is null limit 2000")
    rows = cur.fetchall()

    start_time = time.time()

    # 각 행에 대해 process_row 함수를 호출하여 결과를 업데이트합니다.
    batch_size = 45
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        time.sleep(70)  # Wait for 1 minute before processing the next batch

        for row in batch:
            result = process_row(row)
            if result:
                elementToUpdate, row_id = result
                cur.execute("UPDATE food_nutrition SET \"coupangProductInfos\" = %s WHERE id = %s", (elementToUpdate, row_id))
        conn.commit()  # Commit after processing each batch
        print("Batch processed:", i // batch_size + 1)
    

    end_time = time.time()


    print(f"Execution time: {end_time - start_time} seconds")

    cur.close()
    conn.commit()
    conn.close()


def generateHmac(method, url, secretKey, accessKey):
    path, *query = url.split("?")
    datetimeGMT = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
    message = datetimeGMT + method + path + (query[0] if query else "")

    signature = hmac.new(bytes(secretKey, "utf-8"),
                         message.encode("utf-8"),
                         hashlib.sha256).hexdigest()

    return "CEA algorithm=HmacSHA256, access-key={}, signed-date={}, signature={}".format(accessKey, datetimeGMT, signature)


# 상품 검색 함수
def search_products(keyword, limit=10):
    method = 'GET'
    domain = 'https://api-gateway.coupang.com'
    url = f"/v2/providers/affiliate_open_api/apis/openapi/products/search?keyword={quote(keyword)}&limit={limit}"
    authorization = generateHmac(method, url, SECRET_KEY, ACCESS_KEY)
    response = requests.get(f"{domain}{url}", headers={'Authorization': authorization, 'Content-Type': 'application/json'})
    # print(f"상품 검색 결과: {response.json()}")
    return response.json()

# 파트너스 링크 생성 함수
def generate_partner_link(coupang_urls):
    method = 'POST'
    domain = 'https://api-gateway.coupang.com'
    url = '/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink'
    authorization = generateHmac(method, url, SECRET_KEY, ACCESS_KEY)
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
