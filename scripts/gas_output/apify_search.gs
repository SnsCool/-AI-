/**
 * Apify APIを使用したTwitter検索スクリプト
 *
 * 使用方法:
 * 1. このコードをスプレッドシートのApps Script（拡張機能 > Apps Script）に貼り付ける
 * 2. APIFY_API_TOKEN を自分のApify APIトークンに置き換える
 * 3. 「検索条件入力」シートに条件を入力
 * 4. カスタムメニュー「Apify検索」から実行
 */

// ============================================
// 設定（ここを編集してください）
// ============================================

// Apify APIトークン（https://console.apify.com/settings/integrations で取得）
const APIFY_API_TOKEN = "apify_api_UzaYDmTKq9ivHyaatdsPWEbxrPJ9hV4kt3mq";

// 使用するApify Actor ID（URLでは / を ~ に置換）
const ACTOR_ID = "apidojo~tweet-scraper";

// シート名
const INPUT_SHEET_NAME = "検索条件入力";
const OUTPUT_SHEET_NAME = "検索結果";

// ============================================
// メイン関数
// ============================================

/**
 * スプレッドシート起動時にカスタムメニューを追加
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🔍 Apify検索')
    .addItem('検索実行', 'runApifySearch')
    .addItem('検索結果クリア', 'clearSearchResults')
    .addSeparator()
    .addItem('APIトークンテスト', 'testApiToken')
    .addToUi();
}

/**
 * Apify APIを使用してTwitter検索を実行
 */
function runApifySearch() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const inputSheet = ss.getSheetByName(INPUT_SHEET_NAME);
  const outputSheet = ss.getSheetByName(OUTPUT_SHEET_NAME);

  if (!inputSheet) {
    SpreadsheetApp.getUi().alert('エラー: 「' + INPUT_SHEET_NAME + '」シートが見つかりません');
    return;
  }

  if (!outputSheet) {
    SpreadsheetApp.getUi().alert('エラー: 「' + OUTPUT_SHEET_NAME + '」シートが見つかりません');
    return;
  }

  // 検索条件を取得（B列の値）
  const keyword = inputSheet.getRange("B3").getValue();
  const account = inputSheet.getRange("B4").getValue();
  const minLikes = inputSheet.getRange("B5").getValue();
  const startDate = inputSheet.getRange("B6").getValue();
  const endDate = inputSheet.getRange("B7").getValue();

  // 検索クエリを構築
  let searchQuery = "";

  if (keyword) {
    searchQuery += keyword;
  }

  if (account) {
    searchQuery += (searchQuery ? " " : "") + "from:" + account;
  }

  if (minLikes && minLikes > 0) {
    searchQuery += (searchQuery ? " " : "") + "min_faves:" + minLikes;
  }

  if (startDate) {
    const start = formatDate(startDate);
    if (start) {
      searchQuery += (searchQuery ? " " : "") + "since:" + start;
    }
  }

  if (endDate) {
    const end = formatDate(endDate);
    if (end) {
      searchQuery += (searchQuery ? " " : "") + "until:" + end;
    }
  }

  // 検索クエリを検索条件入力シートに表示
  inputSheet.getRange("B10").setValue(searchQuery);

  if (!searchQuery) {
    SpreadsheetApp.getUi().alert('検索条件を入力してください');
    return;
  }

  // 実行確認
  const ui = SpreadsheetApp.getUi();
  const response = ui.alert(
    '検索実行確認',
    '以下のクエリで検索を実行しますか？\n\n' + searchQuery,
    ui.ButtonSet.YES_NO
  );

  if (response !== ui.Button.YES) {
    return;
  }

  // ステータス表示
  SpreadsheetApp.getActiveSpreadsheet().toast('Apify API検索を実行中...', '処理中', -1);

  try {
    // Apify APIを呼び出し
    const tweets = callApifyApi(searchQuery);

    if (!tweets || tweets.length === 0) {
      SpreadsheetApp.getActiveSpreadsheet().toast('検索結果が見つかりませんでした', '完了', 5);
      return;
    }

    // 結果をスプレッドシートに書き込み
    writeResultsToSheet(outputSheet, tweets);

    SpreadsheetApp.getActiveSpreadsheet().toast(
      tweets.length + '件のツイートを取得しました',
      '完了',
      5
    );

  } catch (error) {
    Logger.log('Error: ' + error);
    SpreadsheetApp.getUi().alert('エラー: ' + error.message);
  }
}

/**
 * Apify APIを呼び出してツイートを取得
 */
function callApifyApi(searchQuery) {
  if (!APIFY_API_TOKEN || APIFY_API_TOKEN === "YOUR_APIFY_API_TOKEN_HERE") {
    throw new Error("APIFY_API_TOKENを設定してください");
  }

  // Apify Actor実行エンドポイント
  const runUrl = `https://api.apify.com/v2/acts/${ACTOR_ID}/runs?token=${APIFY_API_TOKEN}`;

  // 入力パラメータ（Twitter検索URLを使用）
  const searchUrl = "https://twitter.com/search?q=" + encodeURIComponent(searchQuery) + "&f=live";
  const input = {
    "startUrls": [searchUrl],
    "maxItems": 100
  };

  // Actor実行リクエスト
  const runOptions = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(input),
    "muteHttpExceptions": true
  };

  Logger.log("Apify API呼び出し開始: " + searchQuery);

  const runResponse = UrlFetchApp.fetch(runUrl, runOptions);
  const runResult = JSON.parse(runResponse.getContentText());

  if (runResponse.getResponseCode() !== 201) {
    throw new Error("Actor実行エラー: " + JSON.stringify(runResult));
  }

  const runId = runResult.data.id;
  Logger.log("Run ID: " + runId);

  // 完了を待機
  const statusUrl = `https://api.apify.com/v2/actor-runs/${runId}?token=${APIFY_API_TOKEN}`;
  let status = "RUNNING";
  let waitCount = 0;
  const maxWait = 60; // 最大60回（5分）待機

  while (status === "RUNNING" || status === "READY") {
    Utilities.sleep(5000); // 5秒待機
    waitCount++;

    if (waitCount > maxWait) {
      throw new Error("タイムアウト: Actor実行が5分以上かかっています");
    }

    const statusResponse = UrlFetchApp.fetch(statusUrl);
    const statusResult = JSON.parse(statusResponse.getContentText());
    status = statusResult.data.status;

    Logger.log("Status: " + status + " (" + waitCount + "/" + maxWait + ")");
  }

  if (status !== "SUCCEEDED") {
    throw new Error("Actor実行失敗: " + status);
  }

  // 結果を取得
  const datasetId = runResult.data.defaultDatasetId;
  const dataUrl = `https://api.apify.com/v2/datasets/${datasetId}/items?token=${APIFY_API_TOKEN}`;

  const dataResponse = UrlFetchApp.fetch(dataUrl);
  const tweets = JSON.parse(dataResponse.getContentText());

  Logger.log("取得ツイート数: " + tweets.length);

  return tweets;
}

/**
 * 検索結果をスプレッドシートに書き込み
 */
function writeResultsToSheet(sheet, tweets) {
  // 既存データをクリア（ヘッダー行は残す）
  const lastRow = sheet.getLastRow();
  if (lastRow > 1) {
    sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).clearContent();
  }

  // 結果を整形
  const rows = tweets.map((tweet, index) => {
    // ユーザー情報
    const author = tweet.author || {};
    const username = author.userName || author.screen_name || "";
    const profileImage = author.profilePicture || author.profileImageUrl || "";

    // ツイート本文
    const text = tweet.text || tweet.full_text || "";

    // 日時
    const createdAt = tweet.createdAt || tweet.created_at || "";

    // エンゲージメント
    const likes = tweet.likeCount || tweet.favorite_count || 0;
    const retweets = tweet.retweetCount || tweet.retweet_count || 0;
    const bookmarks = tweet.bookmarkCount || 0;
    const replies = tweet.replyCount || 0;
    const quotes = tweet.quoteCount || 0;
    const views = tweet.viewCount || "";

    // URL
    const tweetId = tweet.id || tweet.id_str || "";
    const tweetUrl = tweet.url || (username && tweetId ? `https://x.com/${username}/status/${tweetId}` : "");

    // メディアURL抽出
    const mediaUrls = extractMediaUrls(tweet);
    const videoUrls = extractVideoUrls(tweet);

    return [
      index + 1,        // A: No.
      username,         // B: ユーザー名
      profileImage,     // C: アイコン
      text,            // D: ツイート本文
      createdAt,       // E: 日時
      likes,           // F: いいね数
      retweets,        // G: リツイート数
      bookmarks,       // H: ブックマーク数
      replies,         // I: リプ数
      quotes,          // J: 引用数
      views,           // K: 閲覧数
      tweetUrl,        // L: URL
      mediaUrls[0] || "",  // M: メディア1
      mediaUrls[1] || "",  // N: メディア2
      mediaUrls[2] || "",  // O: メディア3
      videoUrls[0] || "",  // P: 動画URL1
      videoUrls[1] || "",  // Q: 動画URL2
      videoUrls[2] || "",  // R: 動画URL3
      videoUrls[3] || ""   // S: 動画URL4
    ];
  });

  if (rows.length > 0) {
    // データを書き込み（2行目から）
    sheet.getRange(2, 1, rows.length, rows[0].length).setValues(rows);
  }
}

/**
 * メディアURLを抽出
 */
function extractMediaUrls(tweet) {
  const urls = [];

  // Apify形式
  const media = tweet.media || [];
  for (const m of media) {
    if (m && m.type !== "video" && m.type !== "animated_gif") {
      const url = m.media_url_https || m.url || "";
      if (url) urls.push(url);
    }
  }

  // 既存形式
  const extendedEntities = tweet.extended_entities || {};
  const extMedia = extendedEntities.media || [];
  for (const m of extMedia) {
    if (m && m.type !== "video" && m.type !== "animated_gif") {
      const url = m.media_url_https || "";
      if (url && !urls.includes(url)) urls.push(url);
    }
  }

  return urls.slice(0, 3); // 最大3つ
}

/**
 * 動画URLを抽出
 */
function extractVideoUrls(tweet) {
  const urls = [];

  // Apify形式
  const media = tweet.media || [];
  for (const m of media) {
    if (m && (m.type === "video" || m.type === "animated_gif")) {
      const videoInfo = m.video_info || {};
      const variants = videoInfo.variants || [];
      const mp4Variants = variants.filter(v => v.content_type === "video/mp4");
      if (mp4Variants.length > 0) {
        // 最高品質を選択
        mp4Variants.sort((a, b) => (b.bitrate || 0) - (a.bitrate || 0));
        urls.push(mp4Variants[0].url || "");
      }
    }
  }

  // 既存形式
  const extendedEntities = tweet.extended_entities || {};
  const extMedia = extendedEntities.media || [];
  for (const m of extMedia) {
    if (m && (m.type === "video" || m.type === "animated_gif")) {
      const videoInfo = m.video_info || {};
      const variants = videoInfo.variants || [];
      const mp4Variants = variants.filter(v => v.content_type === "video/mp4");
      if (mp4Variants.length > 0) {
        mp4Variants.sort((a, b) => (b.bitrate || 0) - (a.bitrate || 0));
        const url = mp4Variants[0].url || "";
        if (url && !urls.includes(url)) urls.push(url);
      }
    }
  }

  return urls.slice(0, 4); // 最大4つ
}

/**
 * 日付をYYYY-MM-DD形式にフォーマット
 */
function formatDate(dateValue) {
  if (!dateValue) return null;

  // すでに文字列の場合
  if (typeof dateValue === "string") {
    // YYYY-MM-DD形式かチェック
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateValue)) {
      return dateValue;
    }
    // Dateオブジェクトに変換を試みる
    try {
      dateValue = new Date(dateValue);
    } catch (e) {
      return null;
    }
  }

  // Dateオブジェクトの場合
  if (dateValue instanceof Date && !isNaN(dateValue)) {
    const year = dateValue.getFullYear();
    const month = String(dateValue.getMonth() + 1).padStart(2, '0');
    const day = String(dateValue.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  return null;
}

/**
 * 検索結果をクリア
 */
function clearSearchResults() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const outputSheet = ss.getSheetByName(OUTPUT_SHEET_NAME);

  if (!outputSheet) {
    SpreadsheetApp.getUi().alert('エラー: 「' + OUTPUT_SHEET_NAME + '」シートが見つかりません');
    return;
  }

  const lastRow = outputSheet.getLastRow();
  if (lastRow > 1) {
    outputSheet.getRange(2, 1, lastRow - 1, outputSheet.getLastColumn()).clearContent();
    SpreadsheetApp.getActiveSpreadsheet().toast('検索結果をクリアしました', '完了', 3);
  } else {
    SpreadsheetApp.getActiveSpreadsheet().toast('クリアするデータがありません', '情報', 3);
  }
}

/**
 * APIトークンのテスト
 */
function testApiToken() {
  if (!APIFY_API_TOKEN || APIFY_API_TOKEN === "YOUR_APIFY_API_TOKEN_HERE") {
    SpreadsheetApp.getUi().alert('APIFY_API_TOKENを設定してください');
    return;
  }

  try {
    const url = `https://api.apify.com/v2/users/me?token=${APIFY_API_TOKEN}`;
    const response = UrlFetchApp.fetch(url);
    const result = JSON.parse(response.getContentText());

    if (result.data && result.data.username) {
      SpreadsheetApp.getUi().alert(
        'APIトークン確認',
        '✓ 接続成功!\n\nユーザー名: ' + result.data.username + '\nEmail: ' + (result.data.email || 'N/A'),
        SpreadsheetApp.getUi().ButtonSet.OK
      );
    } else {
      SpreadsheetApp.getUi().alert('APIトークンが無効です');
    }
  } catch (error) {
    SpreadsheetApp.getUi().alert('エラー: ' + error.message);
  }
}
