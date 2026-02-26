"""ホットペッパーグルメAPI データ収集"""

import sys
import time
import requests
import pandas as pd

from config import HOTPEPPER_API_KEY, HOTPEPPER_API_URL, SEARCH_PARAMS, DATA_DIR


def search_restaurants(start=1):
    """ホットペッパーAPIで道玄坂周辺のレストランを検索する。"""
    params = {
        **SEARCH_PARAMS,
        "key": HOTPEPPER_API_KEY,
        "start": start,
    }
    resp = requests.get(HOTPEPPER_API_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def extract_shop_data(shop):
    """APIレスポンスの1店舗分から必要フィールドを抽出する。"""
    return {
        "id": shop.get("id", ""),
        "name": shop.get("name", ""),
        "address": shop.get("address", ""),
        "lat": shop.get("lat", ""),
        "lng": shop.get("lng", ""),
        "genre": shop.get("genre", {}).get("name", ""),
        "genre_code": shop.get("genre", {}).get("code", ""),
        "budget_code": shop.get("budget", {}).get("code", ""),
        "budget_name": shop.get("budget", {}).get("name", ""),
        "budget_average": shop.get("budget", {}).get("average", ""),
        "capacity": shop.get("capacity", ""),
        "access": shop.get("access", ""),
        "url": shop.get("urls", {}).get("pc", ""),
        "photo": shop.get("photo", {}).get("pc", {}).get("l", ""),
    }


def collect_all():
    """全ページ分のレストランデータを収集する。"""
    if not HOTPEPPER_API_KEY:
        print("エラー: HOTPEPPER_API_KEY が設定されていません。")
        print(".env ファイルに HOTPEPPER_API_KEY=<your_key> を設定してください。")
        sys.exit(1)

    all_shops = []
    start = 1

    # 初回リクエストで総件数を取得
    print("ホットペッパーAPIからデータ収集を開始します...")
    data = search_restaurants(start=start)
    results = data.get("results", {})
    total = int(results.get("results_available", 0))
    returned = int(results.get("results_returned", 0))
    print(f"検索結果: {total} 件")

    shops = results.get("shop", [])
    for shop in shops:
        all_shops.append(extract_shop_data(shop))

    start += returned

    # 残りのページを取得
    while start <= total:
        time.sleep(1)  # API礼儀
        print(f"  取得中... {start}/{total}")
        data = search_restaurants(start=start)
        results = data.get("results", {})
        returned = int(results.get("results_returned", 0))
        if returned == 0:
            break
        shops = results.get("shop", [])
        for shop in shops:
            all_shops.append(extract_shop_data(shop))
        start += returned

    print(f"取得完了: {len(all_shops)} 件")
    return all_shops


def save_to_csv(shops):
    """店舗データをCSVに保存する。"""
    df = pd.DataFrame(shops)
    csv_path = DATA_DIR / "restaurants.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"CSVファイル保存: {csv_path}")
    return df


if __name__ == "__main__":
    shops = collect_all()
    if shops:
        save_to_csv(shops)
