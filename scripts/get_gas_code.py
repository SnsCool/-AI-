#!/usr/bin/env python3
"""
Playwright script to access Google Sheets and extract GAS code
Non-interactive version - takes screenshots and extracts data automatically
"""

import time
import json
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1daCU06YoPJf1izqOSpqmTf8t20NSN451/edit"
OUTPUT_DIR = "/Users/hatakiyoto/-AI-egent-libvela/scripts/gas_output"

def main():
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with sync_playwright() as p:
        # Launch browser in headed mode for authentication
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("=" * 60)
        print("Google Sheets GAS Code Extractor (Auto Mode)")
        print("=" * 60)
        print()

        # Navigate to spreadsheet
        print(f"Opening: {SPREADSHEET_URL}")
        try:
            page.goto(SPREADSHEET_URL, wait_until="domcontentloaded", timeout=120000)
        except Exception as e:
            print(f"  Navigation status: {e}")

        # Wait for page to load
        time.sleep(5)
        current_url = page.url
        print(f"Current URL: {current_url}")

        # Take screenshot
        screenshot_path = f"{OUTPUT_DIR}/spreadsheet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot saved: {screenshot_path}")

        # Check if login is needed
        if "accounts.google.com" in current_url or "signin" in current_url:
            print()
            print("=" * 40)
            print("Googleログインが必要です。")
            print("ブラウザでログインしてください...")
            print("90秒待機します...")
            print("=" * 40)

            # Wait for login (up to 90 seconds)
            for i in range(18):
                time.sleep(5)
                current_url = page.url
                print(f"  [{i*5}s] URL: {current_url[:80]}...")
                if "docs.google.com/spreadsheets" in current_url:
                    print("  ✓ ログイン完了!")
                    break

            # Additional wait for spreadsheet to load
            time.sleep(5)

        # Wait for spreadsheet elements
        print()
        print("=" * 40)
        print("スプレッドシートを読み込み中...")
        print("=" * 40)

        time.sleep(3)

        # Take another screenshot
        screenshot_path2 = f"{OUTPUT_DIR}/spreadsheet_loaded_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        page.screenshot(path=screenshot_path2, full_page=True)
        print(f"Screenshot saved: {screenshot_path2}")

        # Get sheet tab names
        print()
        print("=" * 40)
        print("シート情報を取得中...")
        print("=" * 40)

        try:
            # Wait for sheet tabs
            page.wait_for_selector('.docs-sheet-tab', timeout=30000)
            tabs = page.query_selector_all('.docs-sheet-tab')
            sheet_names = []
            for tab in tabs:
                try:
                    name = tab.inner_text()
                    sheet_names.append(name)
                    print(f"  - シート: {name}")
                except:
                    pass
        except Exception as e:
            print(f"  シートタブ取得エラー: {e}")
            sheet_names = []

        # Try to find and click on "検索条件入力" sheet
        print()
        print("=" * 40)
        print("「検索条件入力」シートを探しています...")
        print("=" * 40)

        search_input_sheet = None
        for tab in tabs if 'tabs' in dir() else []:
            try:
                name = tab.inner_text()
                if "検索条件" in name or "入力" in name:
                    print(f"  ✓ 発見: {name}")
                    tab.click()
                    time.sleep(2)
                    search_input_sheet = name

                    # Take screenshot of this sheet
                    screenshot_path3 = f"{OUTPUT_DIR}/search_input_sheet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    page.screenshot(path=screenshot_path3, full_page=True)
                    print(f"  Screenshot saved: {screenshot_path3}")
                    break
            except:
                pass

        # Try to open Apps Script editor
        print()
        print("=" * 40)
        print("Apps Script を開きます...")
        print("=" * 40)

        try:
            # Click on Extensions menu (拡張機能)
            # Try different menu selectors
            extensions_menu = None

            # Try to find menu by text
            try:
                extensions_menu = page.locator('text="拡張機能"').first
                if extensions_menu:
                    extensions_menu.click()
                    print("  ✓ 拡張機能メニューをクリック")
                    time.sleep(1)
            except:
                pass

            if not extensions_menu:
                # Try English version
                try:
                    extensions_menu = page.locator('text="Extensions"').first
                    if extensions_menu:
                        extensions_menu.click()
                        print("  ✓ Extensions menu clicked")
                        time.sleep(1)
                except:
                    pass

            # Take screenshot of menu
            screenshot_menu = f"{OUTPUT_DIR}/menu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=screenshot_menu, full_page=True)
            print(f"  Menu screenshot saved: {screenshot_menu}")

            # Click on Apps Script
            time.sleep(1)
            apps_script = None
            try:
                apps_script = page.locator('text="Apps Script"').first
                if apps_script:
                    # This opens a new tab
                    with context.expect_page(timeout=30000) as new_page_info:
                        apps_script.click()

                    gas_page = new_page_info.value
                    gas_page.wait_for_load_state()
                    time.sleep(5)

                    print("  ✓ Apps Script エディタが開きました")

                    # Take screenshot of GAS editor
                    screenshot_gas = f"{OUTPUT_DIR}/gas_editor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    gas_page.screenshot(path=screenshot_gas, full_page=True)
                    print(f"  GAS Editor screenshot saved: {screenshot_gas}")

                    # Wait for Monaco editor
                    time.sleep(3)

                    # Try to get code
                    try:
                        gas_page.wait_for_selector('.monaco-editor', timeout=30000)
                        print("  ✓ Monaco editor detected")

                        # Extract code using JavaScript
                        code_content = gas_page.evaluate("""
                            () => {
                                try {
                                    if (typeof monaco !== 'undefined' && monaco.editor) {
                                        const models = monaco.editor.getModels();
                                        if (models && models.length > 0) {
                                            return models.map(m => ({
                                                uri: m.uri.toString(),
                                                content: m.getValue()
                                            }));
                                        }
                                    }
                                    return null;
                                } catch(e) {
                                    return {error: e.toString()};
                                }
                            }
                        """)

                        if code_content and not isinstance(code_content, dict):
                            # Save code to file
                            gas_code_path = f"{OUTPUT_DIR}/gas_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                            with open(gas_code_path, 'w', encoding='utf-8') as f:
                                json.dump(code_content, f, ensure_ascii=False, indent=2)
                            print(f"  ✓ GAS code saved: {gas_code_path}")

                            # Also print the code
                            print()
                            print("=" * 60)
                            print("=== GAS CODE ===")
                            print("=" * 60)
                            for file in code_content:
                                print(f"\n--- {file['uri']} ---")
                                print(file['content'])
                        else:
                            print(f"  Code extraction result: {code_content}")

                            # Alternative: try to select all text
                            print("  Attempting alternative extraction...")
                            gas_page.keyboard.press("Control+a")  # Select all
                            time.sleep(0.5)
                            gas_page.keyboard.press("Control+c")  # Copy

                            # Get visible text as fallback
                            view_lines = gas_page.query_selector_all('.view-line')
                            if view_lines:
                                code_lines = []
                                for line in view_lines:
                                    try:
                                        code_lines.append(line.inner_text())
                                    except:
                                        pass

                                if code_lines:
                                    fallback_code = '\n'.join(code_lines)
                                    fallback_path = f"{OUTPUT_DIR}/gas_code_fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                                    with open(fallback_path, 'w', encoding='utf-8') as f:
                                        f.write(fallback_code)
                                    print(f"  ✓ Fallback code saved: {fallback_path}")
                                    print()
                                    print("=== GAS CODE (Fallback) ===")
                                    print(fallback_code)

                    except Exception as e:
                        print(f"  Code extraction error: {e}")

            except Exception as e:
                print(f"  Apps Script opening error: {e}")

        except Exception as e:
            print(f"Menu error: {e}")

        # Final wait and cleanup
        print()
        print("=" * 40)
        print("30秒後にブラウザを閉じます...")
        print("必要に応じて手動でデータを確認してください")
        print("=" * 40)
        time.sleep(30)

        browser.close()

        print()
        print("=" * 60)
        print("完了！")
        print(f"出力フォルダ: {OUTPUT_DIR}")
        print("=" * 60)

if __name__ == "__main__":
    main()
