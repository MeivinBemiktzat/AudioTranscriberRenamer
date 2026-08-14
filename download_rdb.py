import os
import sys
import requests

RDB_URL = os.environ.get("RDB_DOWNLOAD_URL")

if not RDB_URL:
  print("שגיאה: לא סופק קישור להורדה במשתנה הסביבה RDB_DOWNLOAD_URL.")
  sys.exit(1)

RDB_FILE_PATH = "dump.rdb"


def download_rdb():
  print("מוריד את קובץ ה-RDB...")
  response = requests.get(RDB_URL, stream=True)
  if response.status_code == 200:
    with open(RDB_FILE_PATH, "wb") as f:
      for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)
    print("הורדת קובץ ה-RDB הושלמה בהצלחה.")
  else:
    raise Exception(
        f"שגיאה בהורדת הקובץ: {response.status_code} {response.text}"
    )


if __name__ == "__main__":
  download_rdb()
