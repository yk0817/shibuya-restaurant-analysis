"""GitHub Pages用 docs/ ディレクトリをビルドする。

output/ のチャートPNGを docs/charts/ にコピーし、
マップHTMLを docs/map.html にコピーする。
"""

import shutil

from config import OUTPUT_DIR, DOCS_DIR, CHARTS_DIR


def build():
    """output/ の成果物を docs/ にコピーする。"""
    CHARTS_DIR.mkdir(exist_ok=True)

    # チャートPNGをコピー
    chart_files = list(OUTPUT_DIR.glob("*.png"))
    for f in chart_files:
        dest = CHARTS_DIR / f.name
        shutil.copy2(f, dest)
        print(f"コピー: {f.name} → docs/charts/")

    # 分析結果JSONをコピー
    json_src = OUTPUT_DIR / "analysis_results.json"
    if json_src.exists():
        shutil.copy2(json_src, DOCS_DIR / "analysis_results.json")
        print("コピー: analysis_results.json → docs/")

    # マップHTMLをコピー
    map_src = OUTPUT_DIR / "restaurant_map.html"
    if map_src.exists():
        dest = DOCS_DIR / "map.html"
        shutil.copy2(map_src, dest)
        print(f"コピー: restaurant_map.html → docs/map.html")

    print("\ndocs/ ディレクトリのビルドが完了しました。")
    print("GitHub Pages: Settings → Pages → Source: /docs (master branch)")


if __name__ == "__main__":
    build()
