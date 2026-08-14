import json
import os
import requests
from rdbtools import RdbCallback, RdbParser

# הקישור להורדת קובץ ה-RDB
RDB_URL = "https://upstash-rdb-import.s3.us-east-1.amazonaws.com/8f4a8013-9017-4b2a-b6cf-fae866653d77.rdb?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Checksum-Mode=ENABLED&X-Amz-Credential=ASIARBK5P6ED25GIEYYQ%2F20260814%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260814T150058Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEDcaCXVzLWVhc3QtMSJGMEQCIHjfTu0yJmfOJH%2BiHhmzjU3I2Bth7pNrXIsqZ15QcMDiAiBz71YrWNYF0Te7p7guYNN%2F2Ymwkva8CPrxPhGBrdtFPiq6BQgAEAMaDDA3MTU5OTkxMTE3NSIM4SkhFNONtvkAXHUWKpcF4IVtufpZCR2MFBIMP26iB3PsYgbGtqupVtKDdrxJYOQ5mpcAsXcUzFi0PBeeeq5qyONlaOKtBcrTmwAG9aUMmJJXPikHsxQTGYRitSTkb20TKOggcbNGutyi5LoIyL2g4xpWbqekbJxrrqxch1khyQA4RBD3VnwKRJB67DcXFvJ%2BJxsXzkslryLVi8%2FtveDssjgl4VzMXq4EDie%2FQj5XEsEOexClpxCfJxpWMw8QjXbmiGy2fT9JU4OPtkEYXVkksiNIWZ12CcVqnorXXmOMa3KWZrRL3IHm0nfnii%2FiPaxpBB33qPC9qsDbJeandjYAo1EXs%2FnSMFanJEP5g5mXLkEXSIqYKqREOlOlVbkaINySRWZGf5V59%2FsANCgM%2F4KtmVIRkolDHCKFV1RFhdEOSHAjPjaltU5g6iaK%2FogIsjOiKFJLjnu%2B7ailkPHULUh5BdmdPZeO7nQuhErQUY8T2o%2BAYPAJMThHCOPcyHMUsiZs%2BeDclhiEDxryVl%2FuZuj7UaPYvMXJx2ztkW6KQs0c60PKumFt2fHN88%2FjrMbZOWbDXMrex80yR0%2BJFS9PHWpmvl7%2FXTGUjTe7bzxGxrfs7ouLSoyWhdXIW5aL4AWM76EUOigGO4ZppnO0kdq6nGG3hsevwqTDfBBUKex35Ohv7KG3%2F9O0fsPkoXnFHdRgzqXIO9f%2FNrK6oZaLhSnlPI3JwzKg2dO%2BHyabWkQBG5B2d3ILK26In6%2F9lqrrVZVODi0fewW%2FA6h5HEel80ujZ3CgU74pW4PyAayt4WRSQTiA4do9V0HOZKanJxxk%2BlcHelwL%2BxLpJJrIXwt8kJWHOV2PDaREbth0aydXwclx9lV5G338wRhZXAPSol3oMqHQSwsg7VRmFhq7MNjN%2FNMGOrIB%2FIahwRnwMYFtSg72CBLGQqmT%2Bfron0Z%2BOhUuLQNDBC%2B86D73G10f8WVoWt1jgUON1d3yW2wMI01K60poY7ICheLfSX7pO9tdJlhSoV8t1YkhUbdKmgZJU0ZPWhoZxC3r%2BfISnHsKkRcH3c4E%2B1rMwBFpv6fDYS1yPVrLvZWrxekYKhfQhED4PeBoeUGq7mIgPtqYCN0uKDLunG4bopVjPmGvZPRACQthTPz55h%2FMRjdFqQ%3D%3D&X-Amz-SignedHeaders=host&x-id=GetObject&X-Amz-Signature=f6f2600072ed45d5964e683f2e4f01438102b252f27aeb83d039655c63ba1df3"

RDB_FILE_PATH = "dump.rdb"
OUTPUT_DIR = "./exported_json_files"

os.makedirs(OUTPUT_DIR, exist_ok=True)


class JSONExporterCallback(RdbCallback):
  """Callback שמטפל בכל מפתח שנמצא בקובץ ה-RDB ושומר אותו כ-JSON."""

  def __init__(self, output_dir):
    super().__init__()
    self.output_dir = output_dir
    self.count = 0

  def _save_key_value(self, key, value, expiry=None):
    if isinstance(key, bytes):
      key = key.decode("utf-8", errors="ignore")

    if isinstance(value, bytes):
      value = value.decode("utf-8", errors="ignore")

    # יצירת המבנה בדיוק כפי הנדרש
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
