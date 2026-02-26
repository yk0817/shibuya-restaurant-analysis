"""設定・定数・API URL"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# APIキー
HOTPEPPER_API_KEY = os.getenv("HOTPEPPER_API_KEY", "")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# ホットペッパーグルメAPI
HOTPEPPER_API_URL = "http://webservice.recruit.co.jp/hotpepper/gourmet/v1/"

# 検索パラメータ
SEARCH_PARAMS = {
    "large_area": "Z011",   # 東京
    "keyword": "道玄坂",
    "order": 4,             # おすすめ順
    "format": "json",
    "count": 100,           # 1リクエストあたりの取得件数
}

# 道玄坂中心座標
CENTER_LAT = 35.6580
CENTER_LNG = 139.6994

# ディレクトリパス
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
DOCS_DIR = BASE_DIR / "docs"
CHARTS_DIR = DOCS_DIR / "charts"

# ディレクトリ作成
for d in [DATA_DIR, OUTPUT_DIR, DOCS_DIR, CHARTS_DIR]:
    d.mkdir(exist_ok=True)
