import json
import os
import requests
from rdbtools import RdbCallback, RdbParser

# תוכל לשים כאן את הקישור המעודכן או לשלוף אותו מ-secrets
RDB_URL = os.environ.get(
    "RDB_DOWNLOAD_URL",
    "https://upstash-rdb-import.s3.us-east-1.amazonaws.com/8f4a8013-9017-4b2a-b6cf-fae866653d77.rdb?X-Amz-Algorithm=AWS4-HMAC-SHA256&...",
)

RDB_FILE_PATH = "dump.rdb"
OUTPUT_DIR = "./exported_json_files"

os.makedirs(OUTPUT_DIR, exist_ok=True)


class JSONExporterCallback(RdbCallback):

  def __init__(self, output_dir):
    super().__init__()
    self.output_dir = output_dir
    self.count = 0

  def _save_key_value(self, key, value, expiry=None):
    if isinstance(key, bytes):
      key = key.decode("utf-8", errors="ignore")

    if isinstance(value, bytes):
      value = value.decode("utf-8", errors="ignore")

    record = {
        "key": key,
        "value": value,
        "expiresAt": expiry,
        "updatedAt": None,
    }

    safe_filename = key.replace(":", "_") + ".json"
    file_path = os.path.join(self.output_dir, safe_filename)

    with open(file_path, "w", encoding="utf-8") as f:
      json.dump(record, f, ensure_ascii=False, indent=2)

    self.count += 1
    print(f"נשמר: {file_path}")

  def set(self, key, value, expiry, info):
    self._save_key_value(key, value, expiry)

  def string(self, key, value, expiry, info):
    self._save_key_value(key, value, expiry)


def download_rdb():
  print("מוריד את קובץ ה-RDB...")
  response = requests.get(RDB_URL, stream=True)
  if response.status_code == 200:
    with open(RDB_FILE_PATH, "wb") as f:
      for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)
    print("הורדת הקובץ הושלמה בהצלחה.")
  else:
    raise Exception(
        f"שגיאה בהורדת הקובץ: {response.status_code} {response.text}"
    )


def parse_rdb():
  print("מתחיל בפענוח קובץ ה-RDB והמרה ל-JSON...")
  callback = JSONExporterCallback(OUTPUT_DIR)
  parser = RdbParser(callback)
  parser.parse(RDB_FILE_PATH)
  print(f"התהליך הושלם. נשמרו {callback.count} קבצים בתיקייה {OUTPUT_DIR}.")


if __name__ == "__main__":
  download_rdb()
  parse_rdb()
