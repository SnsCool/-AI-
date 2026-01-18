#!/usr/bin/env python3
"""
Playwrightで家系図ビューアのスクリーンショットを取得
"""

from playwright.sync_api import sync_playwright
import os

def take_screenshots():
    html_path = "/Users/hatakiyoto/-AI-egent-libvela/notion_data/viewer/family-tree-view.html"
    output_dir = "/Users/hatakiyoto/-AI-egent-libvela/notion_data/screenshots"

    # 出力ディレクトリ作成
    os.makedirs(output_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})

        # HTMLファイルを開く
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(2000)  # レンダリング待ち

        # 全体スクリーンショット
        print("Taking full page screenshot...")
        page.screenshot(path=f"{output_dir}/family-tree-full.png", full_page=True)

        # 各セクションのスクリーンショット
        sections = [
            ("all", "すべて表示"),
            ("0", "Levela全体"),
            ("1", "部署"),
            ("2", "事業"),
            ("3", "マニュアル"),
            ("4", "インテリジェンス"),
            ("5", "その他"),
        ]

        for value, name in sections:
            print(f"Taking screenshot: {name}...")
            # ドロップダウンを選択
            page.select_option("#parentSelect", value)
            page.wait_for_timeout(1000)

            # スクリーンショット
            safe_name = name.replace("/", "-")
            page.screenshot(path=f"{output_dir}/section-{safe_name}.png", full_page=True)

        browser.close()

    print(f"\nScreenshots saved to: {output_dir}")
    print("Files:")
    for f in os.listdir(output_dir):
        if f.endswith('.png'):
            print(f"  - {f}")

if __name__ == "__main__":
    take_screenshots()
