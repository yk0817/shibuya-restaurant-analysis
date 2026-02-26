"""価格帯分析・ランキング生成"""

import json
import re
import sys

import pandas as pd
from tabulate import tabulate

from config import DATA_DIR, OUTPUT_DIR


def load_data():
    """CSVから店舗データを読み込む。"""
    csv_path = DATA_DIR / "restaurants.csv"
    if not csv_path.exists():
        print(f"エラー: {csv_path} が見つかりません。先に collect.py を実行してください。")
        sys.exit(1)
    df = pd.read_csv(csv_path)
    print(f"データ読み込み: {len(df)} 件")
    return df


def parse_budget_range(budget_str):
    """予算文字列を (min, max) のタプルにパースする。

    例: '2001～3000円' → (2001, 3000)
         '5001〜7000円' → (5001, 7000)
    """
    if not isinstance(budget_str, str) or not budget_str:
        return (None, None)

    # 全角/半角チルダ、ハイフンに対応
    budget_str = budget_str.replace("円", "").strip()
    parts = re.split(r"[～〜~\-ー]", budget_str)

    values = []
    for part in parts:
        # 数字のみ抽出
        nums = re.findall(r"\d+", part)
        if nums:
            values.append(int(nums[0]))

    if len(values) == 2:
        return (values[0], values[1])
    elif len(values) == 1:
        return (values[0], values[0])
    return (None, None)


def analyze_budget(df):
    """予算帯分析を行う。"""
    df = df.copy()
    parsed = df["budget_name"].apply(parse_budget_range)
    df["budget_min"] = parsed.apply(lambda x: x[0])
    df["budget_max"] = parsed.apply(lambda x: x[1])
    df["budget_mid"] = df.apply(
        lambda row: (row["budget_min"] + row["budget_max"]) / 2
        if pd.notna(row["budget_min"]) and pd.notna(row["budget_max"])
        else None,
        axis=1,
    )

    valid = df.dropna(subset=["budget_mid"])
    stats = {}
    if len(valid) > 0:
        stats = {
            "total_shops": int(len(df)),
            "shops_with_budget": int(len(valid)),
            "min_price": int(valid["budget_min"].min()),
            "max_price": int(valid["budget_max"].max()),
            "mean_mid": round(valid["budget_mid"].mean()),
            "median_mid": round(valid["budget_mid"].median()),
        }

    # 予算帯別レストラン数
    budget_dist = df["budget_name"].value_counts().reset_index()
    budget_dist.columns = ["budget_range", "count"]
    stats["budget_distribution"] = budget_dist.to_dict(orient="records")

    return df, stats


def analyze_genre(df):
    """ジャンル別分析を行う。"""
    genre_counts = df["genre"].value_counts().reset_index()
    genre_counts.columns = ["genre", "count"]

    # ジャンル別の平均予算（budget_midがある場合）
    if "budget_mid" in df.columns:
        genre_avg = (
            df.dropna(subset=["budget_mid"])
            .groupby("genre")["budget_mid"]
            .agg(["mean", "count"])
            .reset_index()
        )
        genre_avg.columns = ["genre", "avg_budget", "count"]
        genre_avg["avg_budget"] = genre_avg["avg_budget"].round().astype(int)
        genre_avg = genre_avg.sort_values("count", ascending=False)
    else:
        genre_avg = genre_counts.copy()
        genre_avg["avg_budget"] = 0

    return {
        "genre_counts": genre_counts.to_dict(orient="records"),
        "genre_avg_budget": genre_avg.to_dict(orient="records"),
    }


def compute_ranking(df):
    """人気店ランキングを算出する。

    スコア = APIおすすめ順位(0.4) + 席数(0.3) + ジャンル人気度(0.3)
    """
    df = df.copy()

    # APIおすすめ順位スコア (index順=おすすめ順、上位ほど高スコア)
    n = len(df)
    df["rank_score"] = [(n - i) / n for i in range(n)]

    # 席数スコア (正規化)
    df["capacity_num"] = pd.to_numeric(df["capacity"], errors="coerce").fillna(0)
    cap_max = df["capacity_num"].max()
    df["capacity_score"] = df["capacity_num"] / cap_max if cap_max > 0 else 0

    # ジャンル人気度スコア (そのジャンルの店舗数 / 最多ジャンル店舗数)
    genre_counts = df["genre"].value_counts()
    genre_max = genre_counts.max() if len(genre_counts) > 0 else 1
    df["genre_popularity"] = df["genre"].map(genre_counts) / genre_max

    # 総合スコア
    df["score"] = (
        df["rank_score"] * 0.4
        + df["capacity_score"] * 0.3
        + df["genre_popularity"] * 0.3
    )

    top20 = df.nlargest(20, "score")[
        ["name", "genre", "budget_name", "capacity_num", "score", "access"]
    ].copy()
    top20["score"] = top20["score"].round(3)
    top20["rank"] = range(1, len(top20) + 1)

    return top20


def display_results(stats, genre_stats, top20):
    """分析結果をターミナルに表示する。"""
    print("\n" + "=" * 60)
    print("  渋谷道玄坂 レストラン分析結果")
    print("=" * 60)

    print("\n■ エリア概要")
    print(f"  総店舗数: {stats.get('total_shops', 'N/A')}")
    print(f"  予算情報あり: {stats.get('shops_with_budget', 'N/A')} 件")
    print(f"  最低価格帯: {stats.get('min_price', 'N/A')} 円")
    print(f"  最高価格帯: {stats.get('max_price', 'N/A')} 円")
    print(f"  平均予算: {stats.get('mean_mid', 'N/A')} 円")
    print(f"  中央値予算: {stats.get('median_mid', 'N/A')} 円")

    print("\n■ 予算帯分布")
    budget_data = stats.get("budget_distribution", [])
    if budget_data:
        print(tabulate(budget_data, headers="keys", tablefmt="simple"))

    print("\n■ ジャンル別店舗数")
    genre_data = genre_stats.get("genre_counts", [])
    if genre_data:
        print(tabulate(genre_data[:15], headers="keys", tablefmt="simple"))

    print("\n■ 人気店ランキング Top20")
    ranking_data = top20[["rank", "name", "genre", "budget_name", "score"]].values.tolist()
    print(
        tabulate(
            ranking_data,
            headers=["順位", "店名", "ジャンル", "予算", "スコア"],
            tablefmt="simple",
        )
    )


def save_results(stats, genre_stats, top20):
    """分析結果をJSONファイルに保存する。"""
    results = {
        "budget_stats": {k: v for k, v in stats.items() if k != "budget_distribution"},
        "budget_distribution": stats.get("budget_distribution", []),
        "genre_stats": genre_stats,
        "ranking": top20[["rank", "name", "genre", "budget_name", "capacity_num", "score", "access"]].to_dict(
            orient="records"
        ),
    }
    json_path = OUTPUT_DIR / "analysis_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n分析結果保存: {json_path}")
    return results


if __name__ == "__main__":
    df = load_data()
    df, budget_stats = analyze_budget(df)
    genre_stats = analyze_genre(df)
    top20 = compute_ranking(df)
    display_results(budget_stats, genre_stats, top20)
    save_results(budget_stats, genre_stats, top20)
