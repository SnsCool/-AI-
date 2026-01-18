#!/usr/bin/env python3
"""
Apps Scriptのコードを直接置き換えるスクリプト
"""

import time
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1daCU06YoPJf1izqOSpqmTf8t20NSN451/edit"
OUTPUT_DIR = "/Users/hatakiyoto/-AI-egent-libvela/scripts/gas_output"

# 新しいApifyコード
NEW_CODE = '''/**
 * Apify APIを使用したTwitter検索スクリプト
 */

const APIFY_API_TOKEN = "apify_api_UzaYDmTKq9ivHyaatdsPWEbxrPJ9hV4kt3mq";
const ACTOR_ID = "apidojo~tweet-scraper";
const INPUT_SHEET_NAME = "検索条件入力";
const OUTPUT_SHEET_NAME = "検索結果";

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🔍 Apify検索')
    .addItem('検索実行', 'runApifySearch')
    .addItem('検索結果クリア', 'clearSearchResults')
    .addItem('APIトークンテスト', 'testApiToken')
    .addToUi();
}

function runApifySearch() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const inputSheet = ss.getSheetByName(INPUT_SHEET_NAME);
  const outputSheet = ss.getSheetByName(OUTPUT_SHEET_NAME);

  if (!inputSheet || !outputSheet) {
    SpreadsheetApp.getUi().alert('シートが見つかりません');
    return;
  }

  const keyword = inputSheet.getRange("B3").getValue();
  const account = inputSheet.getRange("B4").getValue();
  const minLikes = inputSheet.getRange("B5").getValue();
  const startDate = inputSheet.getRange("B6").getValue();
  const endDate = inputSheet.getRange("B7").getValue();

  let searchQuery = "";
  if (keyword) searchQuery += keyword;
  if (account) searchQuery += " from:" + account;
  if (minLikes > 0) searchQuery += " min_faves:" + minLikes;
  if (startDate) searchQuery += " since:" + formatDate(startDate);
  if (endDate) searchQuery += " until:" + formatDate(endDate);

  inputSheet.getRange("B10").setValue(searchQuery.trim());

  if (!searchQuery.trim()) {
    SpreadsheetApp.getUi().alert('検索条件を入力してください');
    return;
  }

  const ui = SpreadsheetApp.getUi();
  if (ui.alert('検索実行', searchQuery + ' で検索しますか?', ui.ButtonSet.YES_NO) !== ui.Button.YES) return;

  SpreadsheetApp.getActiveSpreadsheet().toast('検索中...', '処理中', -1);

  try {
    const tweets = callApifyApi(searchQuery.trim());
    if (!tweets || tweets.length === 0) {
      SpreadsheetApp.getActiveSpreadsheet().toast('結果なし', '完了', 5);
      return;
    }
    writeResultsToSheet(outputSheet, tweets);
    SpreadsheetApp.getActiveSpreadsheet().toast(tweets.length + '件取得', '完了', 5);
  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.message);
  }
}

function callApifyApi(searchQuery) {
  const runUrl = "https://api.apify.com/v2/acts/" + ACTOR_ID + "/runs?token=" + APIFY_API_TOKEN;
  const searchUrl = "https://twitter.com/search?q=" + encodeURIComponent(searchQuery) + "&f=live";

  const runResponse = UrlFetchApp.fetch(runUrl, {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({startUrls: [searchUrl], maxItems: 100}),
    muteHttpExceptions: true
  });

  if (runResponse.getResponseCode() !== 201) {
    throw new Error("Actor実行エラー");
  }

  const runResult = JSON.parse(runResponse.getContentText());
  const runId = runResult.data.id;
  const datasetId = runResult.data.defaultDatasetId;

  let status = "RUNNING";
  let count = 0;
  while ((status === "RUNNING" || status === "READY") && count < 60) {
    Utilities.sleep(5000);
    count++;
    const statusResponse = UrlFetchApp.fetch("https://api.apify.com/v2/actor-runs/" + runId + "?token=" + APIFY_API_TOKEN);
    status = JSON.parse(statusResponse.getContentText()).data.status;
  }

  if (status !== "SUCCEEDED") throw new Error("実行失敗: " + status);

  const dataResponse = UrlFetchApp.fetch("https://api.apify.com/v2/datasets/" + datasetId + "/items?token=" + APIFY_API_TOKEN);
  return JSON.parse(dataResponse.getContentText());
}

function writeResultsToSheet(sheet, tweets) {
  const lastRow = sheet.getLastRow();
  if (lastRow > 1) sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).clearContent();

  const rows = tweets.map((t, i) => {
    const author = t.author || {};
    return [
      i + 1,
      author.userName || "",
      author.profilePicture || "",
      t.text || "",
      t.createdAt || "",
      t.likeCount || 0,
      t.retweetCount || 0,
      t.bookmarkCount || 0,
      t.replyCount || 0,
      t.quoteCount || 0,
      t.viewCount || "",
      t.url || "",
      "", "", "", "", "", "", ""
    ];
  });

  if (rows.length > 0) sheet.getRange(2, 1, rows.length, rows[0].length).setValues(rows);
}

function formatDate(d) {
  if (!d) return "";
  if (typeof d === "string" && /^\\d{4}-\\d{2}-\\d{2}$/.test(d)) return d;
  try {
    const date = new Date(d);
    return date.getFullYear() + "-" + String(date.getMonth()+1).padStart(2,"0") + "-" + String(date.getDate()).padStart(2,"0");
  } catch(e) { return ""; }
}

function clearSearchResults() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(OUTPUT_SHEET_NAME);
  if (!sheet) return;
  const lastRow = sheet.getLastRow();
  if (lastRow > 1) sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).clearContent();
  SpreadsheetApp.getActiveSpreadsheet().toast('クリア完了', '完了', 3);
}

function testApiToken() {
  try {
    const response = UrlFetchApp.fetch("https://api.apify.com/v2/users/me?token=" + APIFY_API_TOKEN);
    const result = JSON.parse(response.getContentText());
    SpreadsheetApp.getUi().alert('接続成功!\\nユーザー: ' + result.data.username);
  } catch(e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.message);
  }
}
'''

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("=" * 60)
        print("Apps Script コード置き換え")
        print("=" * 60)

        # スプレッドシートを開く
        print("スプレッドシートを開いています...")
        page.goto(SPREADSHEET_URL, wait_until="domcontentloaded", timeout=120000)
        time.sleep(5)

        # ログイン確認
        if "accounts.google.com" in page.url:
            print("ログインしてください（120秒待機）...")
            for i in range(24):
                time.sleep(5)
                if "docs.google.com/spreadsheets" in page.url:
                    break
            time.sleep(5)

        print(f"現在のURL: {page.url}")
        time.sleep(3)

        # 拡張機能メニューを開く
        print("拡張機能メニューを開きます...")
        try:
            # メニューバーをクリック
            page.keyboard.press("Alt+t")  # ツールメニューのショートカット
            time.sleep(1)
            page.keyboard.press("Escape")
            time.sleep(0.5)

            # 拡張機能をクリック
            extensions = page.locator('span:has-text("拡張機能")').first
            extensions.click()
            time.sleep(2)

            # スクリーンショット
            page.screenshot(path=f"{OUTPUT_DIR}/fix_01_menu.png")

            # Apps Scriptをクリック
            apps_script = page.locator('span:has-text("Apps Script")').first
            with context.expect_page(timeout=30000) as new_page_info:
                apps_script.click()

            gas_page = new_page_info.value
            gas_page.wait_for_load_state()
            time.sleep(5)

            print("Apps Scriptエディタが開きました")
            gas_page.screenshot(path=f"{OUTPUT_DIR}/fix_02_editor.png")

            # エディタ内のコードを全選択して削除
            print("既存コードを削除中...")
            time.sleep(2)

            # Monaco エディタ内をクリック
            editor = gas_page.locator('.monaco-editor').first
            editor.click()
            time.sleep(0.5)

            # 全選択 (Cmd+A on Mac)
            gas_page.keyboard.press("Meta+a")
            time.sleep(0.5)

            # 削除
            gas_page.keyboard.press("Backspace")
            time.sleep(0.5)

            print("新しいコードを入力中...")
            # 新しいコードを入力
            gas_page.keyboard.type(NEW_CODE, delay=1)

            time.sleep(2)
            gas_page.screenshot(path=f"{OUTPUT_DIR}/fix_03_new_code.png")

            # 保存 (Cmd+S on Mac)
            print("保存中...")
            gas_page.keyboard.press("Meta+s")
            time.sleep(3)

            gas_page.screenshot(path=f"{OUTPUT_DIR}/fix_04_saved.png")
            print("✓ コード置き換え完了!")

            # 30秒待機
            print("30秒待機（確認用）...")
            time.sleep(30)

        except Exception as e:
            print(f"エラー: {e}")
            page.screenshot(path=f"{OUTPUT_DIR}/fix_error.png")

        browser.close()
        print("完了")

if __name__ == "__main__":
    main()
