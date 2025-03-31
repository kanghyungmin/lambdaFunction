import os
import time
import requests
import pandas as pd

base_url = "http://openapi.foodsafetykorea.go.kr/api//C002/json/"
batch_size = 1000
start = 1
end = 996000  # Adjust this to your desired maximum range
output_file = "/Users/hyungmin/Desktop/food_safety_data.xlsx"

# 순번 초기화
sequence_number = 1

for i in range(start, end, batch_size):
    time.sleep(10)  # Wait for 1 minute before processing the next batch
    batch_start = i
    batch_end = min(i + batch_size - 1, end)
    url = f"{base_url}{batch_start}/{batch_end}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"Success: {url}")
            # print(response.text)  # Print the response content
            # Parse the JSON response
            data = response.json()

            # Extract the rows
            rows = data.get("C002", {}).get("row", [])

            # Convert rows to a DataFrame
            df = pd.DataFrame(rows)

            # 순번 열 추가
            df.insert(0, "순번", range(sequence_number, sequence_number + len(df)))
            sequence_number += len(df)  # 순번 업데이트

            # Save the DataFrame to an Excel file
            if not os.path.exists(output_file):
                # 파일이 없으면 새로 생성
                df.to_excel(output_file, index=False, sheet_name=f"Batch_{batch_start}_{batch_end}")
            else:
                # 파일이 있으면 기존 데이터에 덧붙이기
                existing_df = pd.read_excel(output_file, sheet_name=0)  # 첫 번째 시트 읽기
                combined_df = pd.concat([existing_df, df], ignore_index=True)  # 기존 데이터와 새 데이터 결합
                combined_df.to_excel(output_file, index=False, sheet_name="Combined_Data")  # 덮어쓰기

            # print(f"Data saved to {output_file}")
        else:
            print(f"Failed: {url} with status code {response.status_code}")
    except Exception as e:
        print(f"Error occurred for URL {url}: {e}")