import os
import requests
import pandas as pd

base_url = "http://openapi.foodsafetykorea.go.kr/api//C002/json/"
batch_size = 2
start = 1
end = 6  # Adjust this to your desired maximum range
output_file = "/Users/hyungmin/Desktop/food_safety_data.xlsx"

# 순번 초기화
sequence_number = 1

for i in range(start, end, batch_size):
    batch_start = i
    batch_end = min(i + batch_size - 1, end)
    url = f"{base_url}{batch_start}/{batch_end}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"Success: {url}")
            print(response.text)  # Print the response content
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
                # 파일이 있으면 데이터 추가
                with pd.ExcelWriter(output_file, mode="a", if_sheet_exists="overlay") as writer:
                    df.to_excel(writer, index=False, sheet_name=f"Batch_{batch_start}_{batch_end}")

            print(f"Data saved to {output_file}")
        else:
            print(f"Failed: {url} with status code {response.status_code}")
    except Exception as e:
        print(f"Error occurred for URL {url}: {e}")