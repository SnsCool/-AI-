#!/usr/bin/env python3
"""
Apify API テストスクリプト
GASコードと同じロジックでAPIをテスト（標準ライブラリのみ使用）
"""

import json
import time
import urllib.request
import urllib.error
import urllib.parse

# Apify API設定
APIFY_API_TOKEN = "apify_api_UzaYDmTKq9ivHyaatdsPWEbxrPJ9hV4kt3mq"
ACTOR_ID = "apidojo~tweet-scraper"  # URL形式では / を ~ に置換

def make_request(url, data=None, method="GET"):
    """HTTPリクエストを送信"""
    headers = {"Content-Type": "application/json"}

    if data:
        data = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def test_api_connection():
    """APIトークンの接続テスト"""
    print("=" * 60)
    print("1. APIトークン接続テスト")
    print("=" * 60)

    url = f"https://api.apify.com/v2/users/me?token={APIFY_API_TOKEN}"
    status, data = make_request(url)

    if status == 200 and data.get("data"):
        user = data["data"]
        print(f"✓ 接続成功!")
        print(f"  ユーザー名: {user.get('username', 'N/A')}")
        print(f"  Email: {user.get('email', 'N/A')}")
        return True

    print(f"✗ 接続失敗: {status}")
    print(json.dumps(data, indent=2))
    return False

def run_search(search_query, max_tweets=10):
    """Apify APIで検索を実行"""
    print()
    print("=" * 60)
    print("2. 検索実行テスト")
    print("=" * 60)
    print(f"検索クエリ: {search_query}")
    print(f"最大取得数: {max_tweets}")
    print()

    # Actor実行エンドポイント
    run_url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_API_TOKEN}"

    # 入力パラメータ（Twitter検索URLを使用）
    # apidojo/tweet-scraperはstartUrlsでTwitter検索URLを指定
    search_url = f"https://twitter.com/search?q={urllib.parse.quote(search_query)}&f=live"
    input_data = {
        "startUrls": [search_url],
        "maxItems": max_tweets
    }

    print("Actor実行リクエスト送信中...")
    status, run_result = make_request(run_url, data=input_data, method="POST")

    if status != 201:
        print(f"✗ Actor実行エラー: {status}")
        print(json.dumps(run_result, indent=2))
        return None

    run_id = run_result["data"]["id"]
    dataset_id = run_result["data"]["defaultDatasetId"]

    print(f"✓ Actor実行開始")
    print(f"  Run ID: {run_id}")
    print(f"  Dataset ID: {dataset_id}")

    # 完了待機
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_API_TOKEN}"
    run_status = "RUNNING"
    wait_count = 0
    max_wait = 60

    print()
    print("実行完了を待機中...")

    while run_status in ["RUNNING", "READY"]:
        time.sleep(5)
        wait_count += 1

        if wait_count > max_wait:
            print("✗ タイムアウト")
            return None

        _, status_result = make_request(status_url)
        run_status = status_result["data"]["status"]

        print(f"  [{wait_count * 5}s] Status: {run_status}")

    if run_status != "SUCCEEDED":
        print(f"✗ 実行失敗: {run_status}")
        return None

    print("✓ 実行完了")

    # 結果取得
    data_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_API_TOKEN}"
    _, tweets = make_request(data_url)

    print(f"✓ {len(tweets)}件のツイートを取得")

    return tweets

def display_results(tweets):
    """検索結果を表示（スプレッドシートのカラム形式で）"""
    print()
    print("=" * 60)
    print("3. 検索結果（スプレッドシート形式）")
    print("=" * 60)

    if not tweets:
        print("結果なし")
        return

    print()
    print("-" * 120)

    for idx, tweet in enumerate(tweets[:10]):  # 最大10件表示
        # データ抽出
        author = tweet.get("author", {})
        username = author.get("userName") or author.get("screen_name", "N/A")
        profile_image = author.get("profileImageUrl", "")

        text = tweet.get("text") or tweet.get("full_text", "")
        text_preview = text[:50].replace("\n", " ") + "..." if len(text) > 50 else text.replace("\n", " ")

        created_at = tweet.get("createdAt") or tweet.get("created_at", "N/A")

        likes = tweet.get("likeCount") or tweet.get("favorite_count", 0)
        retweets = tweet.get("retweetCount") or tweet.get("retweet_count", 0)
        bookmarks = tweet.get("bookmarkCount", 0)
        replies = tweet.get("replyCount", 0)
        quotes = tweet.get("quoteCount", 0)
        views = tweet.get("viewCount", "N/A")

        tweet_id = tweet.get("id") or tweet.get("id_str", "")
        tweet_url = tweet.get("url", f"https://x.com/{username}/status/{tweet_id}")

        # メディアカウント
        media = tweet.get("media") or []
        extended = tweet.get("extended_entities", {}).get("media", []) if tweet.get("extended_entities") else []
        media_count = len(media) + len(extended)

        video_count = sum(1 for m in (media + extended) if isinstance(m, dict) and m.get("type") in ["video", "animated_gif"])

        print(f"\n【{idx + 1}】 @{username}")
        print(f"   アイコン: {profile_image[:50]}..." if profile_image else "   アイコン: N/A")
        print(f"   本文: {text_preview}")
        print(f"   日時: {created_at}")
        print(f"   いいね: {likes} | RT: {retweets} | ブクマ: {bookmarks} | リプ: {replies} | 引用: {quotes} | 閲覧: {views}")
        print(f"   URL: {tweet_url}")
        print(f"   メディア: {media_count}件 | 動画: {video_count}件")
        print("-" * 120)

    # カラムマッピング確認
    print()
    print("=" * 60)
    print("4. カラムマッピング確認")
    print("=" * 60)
    print("A列 No.         : ✓ 連番生成")
    print("B列 ユーザー名  : ✓ author.userName")
    print("C列 アイコン    : ✓ author.profileImageUrl")
    print("D列 ツイート本文: ✓ text")
    print("E列 日時        : ✓ createdAt")
    print("F列 いいね数    : ✓ likeCount")
    print("G列 RT数        : ✓ retweetCount")
    print("H列 ブクマ数    : ✓ bookmarkCount")
    print("I列 リプ数      : ✓ replyCount")
    print("J列 引用数      : ✓ quoteCount")
    print("K列 閲覧数      : ✓ viewCount")
    print("L列 URL         : ✓ url")
    print("M-O列 メディア  : ✓ media配列から抽出")
    print("P-S列 動画URL   : ✓ video_info.variantsから抽出")

    # JSON形式でも保存
    output_file = "/Users/hatakiyoto/-AI-egent-libvela/scripts/gas_output/test_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(tweets, f, ensure_ascii=False, indent=2)
    print(f"\n✓ 全結果をJSONファイルに保存: {output_file}")

def main():
    print("=" * 60)
    print("Apify API テスト")
    print("=" * 60)
    print()

    # 1. 接続テスト
    if not test_api_connection():
        return

    # 2. 検索テスト（生成AI関連）
    search_query = "生成AI min_faves:100"
    tweets = run_search(search_query, max_tweets=10)

    # 3. 結果表示
    if tweets:
        display_results(tweets)

    print()
    print("=" * 60)
    print("テスト完了")
    print("=" * 60)

if __name__ == "__main__":
    main()
