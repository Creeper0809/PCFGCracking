import os.path
import pathlib

ROOT_PATH = pathlib.Path(__file__).parent.parent
BASE_PATH = pathlib.Path(__file__).parent
DATA_PATH = BASE_PATH / "data/"
KOREAN_DICT_DB_PATH = DATA_PATH / "korean_dict.db"