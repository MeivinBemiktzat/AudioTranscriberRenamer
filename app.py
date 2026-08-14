import json
import os
import requests

UPSTASH_REST_URL = os.environ.get("UPSTASH_REDIS_REST_URL")
UPSTASH_REST_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN")

if not UPSTASH_REST_URL or not UPSTASH_REST_TOKEN:
  raise ValueError(
      "שגיאה: משתני הסביבה UPSTASH_REDIS_REST_URL ו-UPSTASH_REDIS_REST_TOKEN"
      " אינם מוגדרים."
  )

headers = {"Authorization": f"Bearer {UPSTASH_REST_TOKEN}"}

output_dir = "./exported_json_files"
os.makedirs(output_dir, exist_ok=True)


def get_all_keys():
  url = f"{UPSTASH_REST_URL}/keys/*"
  response = requests.get(url, headers=headers)
  print(f"Status Code לקבלת מפתחות: {response.status_code}")
  if response.status_code == 200:
    res = response.json().get("result", [])
    print(f"נמצאו {len(res)} מפתחות.")
    return res
  else:
    print("שגיאה במשיכת המפתחות מ-Redis:", response.text)
    return []


def get_key_value(key):
  url = f"{UPSTASH_REST_URL}/get/{key}"
  response = requests.get(url, headers=headers)
  if response.status_code == 200:
    return response.json().get("result")
  else:
    print(f"שגיאה בקריאת המפתח {key}: {response.text}")
    return None


def export_data():
  keys = get_all_keys()

  saved_count = 0
  for key in keys:
    val = get_key_value(key)
    if val is not None:
      record = {"key": key, "value": val, "expiresAt": None, "updatedAt": None}

      safe_filename = key.replace(":", "_") + ".json"
      file_path = os.path.join(output_dir, safe_filename)

      with open(file_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

      saved_count += 1
      print(f"נשמר: {file_path}")

  print(f"סה\"כ קבצים שנשמרו בתיקייה: {saved_count}")


if __name__ == "__main__":
  export_data()
