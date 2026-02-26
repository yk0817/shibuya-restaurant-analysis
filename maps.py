"""Google Maps連携・Foliumマップ生成"""

import sys

import folium
import pandas as pd

from config import DATA_DIR, OUTPUT_DIR, CENTER_LAT, CENTER_LNG


def get_marker_color(budget_name):
    """予算帯に応じたマーカー色を返す。"""
    if not isinstance(budget_name, str):
        return "gray"

    import re
    nums = re.findall(r"\d+", budget_name)
    if not nums:
        return "gray"

    # 最大値で判定
    max_val = max(int(n) for n in nums)
    if max_val <= 2000:
        return "green"
    elif max_val <= 5000:
        return "orange"
    elif max_val <= 10000:
        return "red"
    else:
        return "darkred"


def create_map():
    """Foliumでインタラクティブマップを生成する。"""
    csv_path = DATA_DIR / "restaurants.csv"
    if not csv_path.exists():
        print(f"エラー: {csv_path} が見つかりません。先に collect.py を実行してください。")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    print(f"データ読み込み: {len(df)} 件")

    # マップ初期化
    m = folium.Map(
        location=[CENTER_LAT, CENTER_LNG],
        zoom_start=16,
        tiles="OpenStreetMap",
    )

    # 凡例HTML
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: white; padding: 12px 16px; border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2); font-size: 13px;">
        <b>予算帯</b><br>
        <span style="color: green;">●</span> ～2,000円<br>
        <span style="color: orange;">●</span> ～5,000円<br>
        <span style="color: red;">●</span> ～10,000円<br>
        <span style="color: darkred;">●</span> 10,000円～<br>
        <span style="color: gray;">●</span> 不明
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # マーカー配置
    placed = 0
    for _, row in df.iterrows():
        lat = row.get("lat")
        lng = row.get("lng")
        if pd.isna(lat) or pd.isna(lng):
            continue

        color = get_marker_color(row.get("budget_name", ""))
        popup_html = f"""
        <div style="min-width: 200px;">
            <b>{row.get('name', '不明')}</b><br>
            ジャンル: {row.get('genre', '-')}<br>
            予算: {row.get('budget_name', '-')}<br>
            アクセス: {row.get('access', '-')}<br>
            {'<a href="' + str(row.get("url", "")) + '" target="_blank">詳細</a>' if pd.notna(row.get("url")) else ''}
        </div>
        """

        folium.Marker(
            location=[float(lat), float(lng)],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=row.get("name", ""),
            icon=folium.Icon(color=color, icon="cutlery", prefix="fa"),
        ).add_to(m)
        placed += 1

    print(f"マーカー配置: {placed} 件")

    # 保存
    map_path = OUTPUT_DIR / "restaurant_map.html"
    m.save(str(map_path))
    print(f"マップ保存: {map_path}")
    return map_path


if __name__ == "__main__":
    create_map()
