import os.path
import pathlib

import requests

ROOT_PATH = pathlib.Path(__file__).parent.parent
BASE_PATH = pathlib.Path(__file__).parent
DATA_PATH = BASE_PATH / "data/"
KOREAN_DICT_DB_PATH = DATA_PATH / "korean_dict.db"
PASSWORD_DB_PATH = DATA_PATH / "passwords.db"
TRAIN_DB_PATH = DATA_PATH / "train.db"

_KOREAN_DICT_DB_GITHUB = ""
_PASSWORD_DB_GITHUB = ""
_TRAIN_DB_GITHUB = ""

def download_file_from_github(url, local_path):
    try:
        print(f"[Debug] Try download in {url}")
        response = requests.get(url)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(response.content)
            print(f"[Debug] Download success {local_path}")
            return True
        else:
            print(f"[Error] Download failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"[Error] Error on download: {e}")
        return False

def get_korean_dict_url():
    if (os.path.exists(KOREAN_DICT_DB_PATH)
            or download_file_from_github(_KOREAN_DICT_DB_GITHUB,KOREAN_DICT_DB_PATH)):
        return KOREAN_DICT_DB_PATH
    print("[Error] No Such Korean Dictionary DB")
    return None

def get_password_url():
    if (os.path.exists(PASSWORD_DB_PATH)
        or download_file_from_github(_PASSWORD_DB_GITHUB,PASSWORD_DB_PATH)):
        return PASSWORD_DB_PATH
    print("[Error] No Such Password DB")
    return None

def get_train_set_url():
    if (os.path.exists(TRAIN_DB_PATH)
        or download_file_from_github(_TRAIN_DB_GITHUB,TRAIN_DB_PATH)):
        return TRAIN_DB_PATH
    print("[Error] No Such Train Set DB")
    return None

