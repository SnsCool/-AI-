#!/usr/bin/env python3
"""
スプレッドシートを開いて検索機能を確認
"""

import time
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1daCU06YoPJf1izqOSpqmTf8t20NSN451/edit"
OUTPUT_DIR = "/Users/hatakiyoto/-AI-egent-libvela/scripts/gas_output"

def main():
    with sync_playwright() as p:
        # ブラウザを起動（ユーザーデータを保持して認証を維持）
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("=" * 60)
        print("スプレッドシート検索機能確認")
        print("=" * 60)
        print()

        # スプレッドシートを開く
        print(f"Opening: {SPREADSHEET_URL}")
        try:
            page.goto(SPREADSHEET_URL, wait_until="domcontentloaded", timeout=120000)
        except Exception as e:
            print(f"  Navigation: {e}")

        # ページ読み込み待機
        time.sleep(5)
        print(f"URL: {page.url}")

        # ログインが必要か確認
        if "accounts.google.com" in page.url:
            print()
            print("=" * 40)
            print("Googleログインが必要です")
            print("ブラウザでログインしてください...")
            print("120秒待機します...")
            print("=" * 40)

            for i in range(24):
                time.sleep(5)
                if "docs.google.com/spreadsheets" in page.url:
                    print("✓ ログイン完了")
                    break
                print(f"  [{i*5}s] 待機中...")

            time.sleep(5)

        # スプレッドシート読み込み待機
        print()
        print("スプレッドシート読み込み中...")
        time.sleep(5)

        # スクリーンショット
        screenshot1 = f"{OUTPUT_DIR}/check_01_initial_{datetime.now().strftime('%H%M%S')}.png"
        page.screenshot(path=screenshot1)
        print(f"Screenshot: {screenshot1}")

        # メニューバーを確認
        print()
        print("=" * 40)
        print("カスタムメニュー確認")
        print("=" * 40)

        # Apify検索メニューを探す
        try:
            # メニューバーの全テキストを取得
            menu_bar = page.locator('#docs-menubar')
            if menu_bar:
                menu_text = menu_bar.inner_text()
                print(f"メニューバー内容: {menu_text[:200]}...")

                # Apify検索メニューがあるか
                if "Apify" in menu_text or "検索" in menu_text:
                    print("✓ Apify検索メニューを発見")
                else:
                    print("⚠ Apify検索メニューが見つかりません")
        except Exception as e:
            print(f"メニュー確認エラー: {e}")

        # カスタムメニューをクリックしてみる
        print()
        print("=" * 40)
        print("カスタムメニューをクリック")
        print("=" * 40)

        try:
            # 「🔍 Apify検索」メニューを探してクリック
            apify_menu = page.locator('text="Apify検索"').first
            if apify_menu:
                apify_menu.click()
                print("✓ Apify検索メニューをクリック")
                time.sleep(2)

                # スクリーンショット
                screenshot2 = f"{OUTPUT_DIR}/check_02_menu_clicked_{datetime.now().strftime('%H%M%S')}.png"
                page.screenshot(path=screenshot2)
                print(f"Screenshot: {screenshot2}")

                # 「検索実行」をクリック
                search_item = page.locator('text="検索実行"').first
                if search_item:
                    search_item.click()
                    print("✓ 検索実行をクリック")
                    time.sleep(3)

                    # スクリーンショット
                    screenshot3 = f"{OUTPUT_DIR}/check_03_search_clicked_{datetime.now().strftime('%H%M%S')}.png"
                    page.screenshot(path=screenshot3)
                    print(f"Screenshot: {screenshot3}")

                    # ダイアログが出るか待機
                    time.sleep(5)
                    screenshot4 = f"{OUTPUT_DIR}/check_04_after_search_{datetime.now().strftime('%H%M%S')}.png"
                    page.screenshot(path=screenshot4)
                    print(f"Screenshot: {screenshot4}")

        except Exception as e:
            print(f"メニュークリックエラー: {e}")

        # Apps Scriptエディタを開いてエラーログを確認
        print()
        print("=" * 40)
        print("Apps Script実行ログを確認")
        print("=" * 40)

        try:
            # 拡張機能メニューを開く
            extensions = page.locator('text="拡張機能"').first
            if extensions:
                extensions.click()
                time.sleep(1)

                screenshot5 = f"{OUTPUT_DIR}/check_05_extensions_{datetime.now().strftime('%H%M%S')}.png"
                page.screenshot(path=screenshot5)
                print(f"Screenshot: {screenshot5}")

                # Apps Scriptをクリック
                apps_script = page.locator('text="Apps Script"').first
                if apps_script:
                    with context.expect_page(timeout=30000) as new_page_info:
                        apps_script.click()

                    gas_page = new_page_info.value
                    gas_page.wait_for_load_state()
                    time.sleep(5)

                    screenshot6 = f"{OUTPUT_DIR}/check_06_gas_editor_{datetime.now().strftime('%H%M%S')}.png"
                    gas_page.screenshot(path=screenshot6)
                    print(f"Screenshot: {screenshot6}")

                    # 実行ログを確認（左のメニューから）
                    try:
                        executions = gas_page.locator('text="実行"').first
                        if executions:
                            executions.click()
                            time.sleep(2)
                            screenshot7 = f"{OUTPUT_DIR}/check_07_executions_{datetime.now().strftime('%H%M%S')}.png"
                            gas_page.screenshot(path=screenshot7)
                            print(f"Screenshot: {screenshot7}")
                    except:
                        pass

        except Exception as e:
            print(f"Apps Script確認エラー: {e}")

        # 最終待機
        print()
        print("=" * 40)
        print("60秒間ブラウザを開いたままにします")
        print("手動で操作して確認してください")
        print("=" * 40)
        time.sleep(60)

        browser.close()
        print("完了")

if __name__ == "__main__":
    main()
