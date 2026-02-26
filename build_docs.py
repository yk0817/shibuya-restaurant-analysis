"""GitHub Pages用 docs/ ディレクトリをビルドする。

output/ のチャートPNGを docs/charts/ にコピーし、
マップHTMLを docs/map.html にコピーし、
分析結果JSONを index.html に埋め込む。
"""

import json
import shutil

from config import OUTPUT_DIR, DOCS_DIR, CHARTS_DIR


def build():
    """output/ の成果物を docs/ にコピー・埋め込みする。"""
    CHARTS_DIR.mkdir(exist_ok=True)

    # チャートPNGをコピー
    chart_files = list(OUTPUT_DIR.glob("*.png"))
    for f in chart_files:
        dest = CHARTS_DIR / f.name
        shutil.copy2(f, dest)
        print(f"コピー: {f.name} → docs/charts/")

    # 分析結果JSONを index.html に埋め込み (テンプレートから生成)
    json_src = OUTPUT_DIR / "analysis_results.json"
    template_path = DOCS_DIR / "index_template.html"
    index_path = DOCS_DIR / "index.html"
    if json_src.exists() and template_path.exists():
        with open(json_src, "r", encoding="utf-8") as f:
            json_data = f.read()
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()
        html = html.replace("__ANALYSIS_DATA__", json_data)
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html)
        print("埋め込み: analysis_results.json → docs/index.html")

    # マップHTMLをコピー
    map_src = OUTPUT_DIR / "restaurant_map.html"
    if map_src.exists():
        dest = DOCS_DIR / "map.html"
        shutil.copy2(map_src, dest)
        print("コピー: restaurant_map.html → docs/map.html")

    print("\ndocs/ ディレクトリのビルドが完了しました。")
    print("GitHub Pages: Settings → Pages → Source: /docs (master branch)")


if __name__ == "__main__":
    build()
