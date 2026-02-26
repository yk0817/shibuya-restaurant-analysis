"""matplotlib チャート生成"""

import json
import sys
import platform

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd

from config import DATA_DIR, OUTPUT_DIR


def setup_font():
    """日本語フォントを設定する。"""
    if platform.system() == "Darwin":
        font_path = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
        try:
            fm.fontManager.addfont(font_path)
            plt.rcParams["font.family"] = "Hiragino Sans"
        except Exception:
            plt.rcParams["font.family"] = "Hiragino Sans"
    else:
        # Linux等ではIPAフォントを試行
        plt.rcParams["font.family"] = "IPAexGothic"
    plt.rcParams["axes.unicode_minus"] = False


def load_data():
    """分析用データを読み込む。"""
    csv_path = DATA_DIR / "restaurants.csv"
    json_path = OUTPUT_DIR / "analysis_results.json"
    if not csv_path.exists():
        print(f"エラー: {csv_path} が見つかりません。")
        sys.exit(1)

    df = pd.read_csv(csv_path)

    results = None
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            results = json.load(f)

    return df, results


def chart_budget_distribution(results):
    """予算帯分布の横棒グラフを生成する。"""
    dist = results.get("budget_distribution", [])
    if not dist:
        print("予算帯分布データがありません。スキップします。")
        return

    df = pd.DataFrame(dist)
    df = df.sort_values("count", ascending=True)

    fig, ax = plt.subplots(figsize=(10, max(6, len(df) * 0.4)))

    # 緑→赤グラデーション
    n = len(df)
    colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, n))

    ax.barh(df["budget_range"], df["count"], color=colors)
    ax.set_xlabel("店舗数")
    ax.set_title("渋谷道玄坂 予算帯別レストラン分布", fontsize=14, fontweight="bold")

    for i, (val, name) in enumerate(zip(df["count"], df["budget_range"])):
        ax.text(val + 0.3, i, str(val), va="center", fontsize=9)

    plt.tight_layout()
    path = OUTPUT_DIR / "budget_distribution.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"チャート保存: {path}")


def chart_genre_distribution(results):
    """ジャンル分布の横棒グラフ Top15 を生成する。"""
    genre_data = results.get("genre_stats", {}).get("genre_counts", [])
    if not genre_data:
        print("ジャンル分布データがありません。スキップします。")
        return

    df = pd.DataFrame(genre_data).head(15)
    df = df.sort_values("count", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = plt.cm.tab20(np.linspace(0, 1, len(df)))
    ax.barh(df["genre"], df["count"], color=colors)
    ax.set_xlabel("店舗数")
    ax.set_title("渋谷道玄坂 ジャンル別店舗数 Top15", fontsize=14, fontweight="bold")

    for i, (val, name) in enumerate(zip(df["count"], df["genre"])):
        ax.text(val + 0.3, i, str(val), va="center", fontsize=9)

    plt.tight_layout()
    path = OUTPUT_DIR / "genre_distribution.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"チャート保存: {path}")


def chart_budget_histogram(df):
    """平均予算ヒストグラムを生成する。"""
    from analyze import parse_budget_range

    parsed = df["budget_name"].apply(parse_budget_range)
    mids = []
    for mn, mx in parsed:
        if mn is not None and mx is not None:
            mids.append((mn + mx) / 2)

    if not mids:
        print("予算データが不足しています。スキップします。")
        return

    mids = np.array(mids)
    fig, ax = plt.subplots(figsize=(10, 6))

    bins = np.arange(0, mids.max() + 1000, 1000)
    ax.hist(mids, bins=bins, color="#4a90d9", edgecolor="white", alpha=0.8)

    mean_val = mids.mean()
    median_val = np.median(mids)
    ax.axvline(mean_val, color="red", linestyle="--", linewidth=2, label=f"平均: {mean_val:,.0f}円")
    ax.axvline(median_val, color="orange", linestyle="-.", linewidth=2, label=f"中央値: {median_val:,.0f}円")

    ax.set_xlabel("予算 (円)")
    ax.set_ylabel("店舗数")
    ax.set_title("渋谷道玄坂 平均予算分布 (1000円刻み)", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)

    plt.tight_layout()
    path = OUTPUT_DIR / "budget_histogram.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"チャート保存: {path}")


def chart_genre_budget_box(df):
    """ジャンル×価格 ボックスプロット Top10ジャンルを生成する。"""
    from analyze import parse_budget_range

    df = df.copy()
    parsed = df["budget_name"].apply(parse_budget_range)
    df["budget_mid"] = [(mn + mx) / 2 if mn and mx else None for mn, mx in parsed]
    df = df.dropna(subset=["budget_mid"])

    if len(df) == 0:
        print("ボックスプロット用データが不足しています。スキップします。")
        return

    # Top10ジャンルを選定
    top_genres = df["genre"].value_counts().head(10).index.tolist()
    df_top = df[df["genre"].isin(top_genres)]

    # ジャンルごとのデータを店舗数降順で整理
    genre_order = df_top["genre"].value_counts().index.tolist()
    data_by_genre = [df_top[df_top["genre"] == g]["budget_mid"].values for g in genre_order]

    fig, ax = plt.subplots(figsize=(12, 7))
    bp = ax.boxplot(data_by_genre, vert=False, patch_artist=True, tick_labels=genre_order)

    colors = plt.cm.Set3(np.linspace(0, 1, len(genre_order)))
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)

    ax.set_xlabel("予算 (円)")
    ax.set_title("渋谷道玄坂 ジャンル別予算分布 Top10", fontsize=14, fontweight="bold")

    plt.tight_layout()
    path = OUTPUT_DIR / "genre_budget_box.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"チャート保存: {path}")


if __name__ == "__main__":
    setup_font()
    df, results = load_data()

    if results is None:
        print("分析結果JSONがありません。先に analyze.py を実行してください。")
        sys.exit(1)

    chart_budget_distribution(results)
    chart_genre_distribution(results)
    chart_budget_histogram(df)
    chart_genre_budget_box(df)
    print("\n全チャートの生成が完了しました。")
