import json
import os
import requests

# שליפת פרטי ההתחברות מתוך משתני הסביבה (GitHub Secrets)
UPSTASH_REST_URL = os.environ.get("UPSTASH_REDIS_REST_URL")
UPSTASH_REST_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN")

if not UPSTASH_REST_URL or not UPSTASH_REST_TOKEN:
  raise ValueError(
      "שגיאה: משתני הסביבה UPSTASH_REDIS_REST_URL ו-UPSTASH_REDIS_REST_TOKEN"
      " אינם מוגדרים."
  )

headers = {"Authorization": f"Bearer {UPSTASH_REST_TOKEN}"}

# יצירת תיקייה לשמירת הקבצים
output_dir = "./exported_json_files"
os.makedirs(output_dir, exist_ok=True)


def get_all_keys():
  """קבלת כל המפתחות מ-Upstash Redis"""
  url = f"{UPSTASH_REST_URL}/keys/*"
  response = requests.get(url, headers=headers)
  if response.status_code == 200:
    return response.json().get("result", [])
  else:
    print("שגיאה במשיכת המפתחות:", response.text)
    return []


def get_key_value(key):
  """קבלת הערך עבור מפתח ספציפי"""
  url = f"{UPSTASH_REST_URL}/get/{key}"
  response = requests.get(url, headers=headers)
  if response.status_code == 200:
    return response.json().get("result")
  return None


def export_data():
  keys = get_all_keys()
  print(f"נמצאו {len(keys)} מפתחות. מתחיל בייצוא...")

  for key in keys:
    val = get_key_value(key)
    if val is not None:
      # בניית מבנה האובייקט
      record = {"key": key, "value": val, "expiresAt": None, "updatedAt": None}

      # יצירת שם קובץ תקין מהמפתח
      safe_filename = key.replace(":", "_") + ".json"
      file_path = os.path.join(output_dir, safe_filename)

      with open(file_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

      print(f"נשמר: {file_path}")


if __name__ == "__main__":
  export_data()
