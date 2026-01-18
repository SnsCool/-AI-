/**
 * Apify APIを使用したTwitter検索 + Gemini API投稿生成スクリプト
 *
 * 使用方法:
 * 1. このコードをスプレッドシートのApps Script（拡張機能 > Apps Script）に貼り付ける
 * 2. APIFY_API_TOKEN と GEMINI_API_KEY を設定
 * 3. 「検索条件入力」シートに条件を入力（条件なしでも実行可能）
 * 4. カスタムメニュー「Apify検索」から実行
 */

// ============================================
// 設定（ここを編集してください）
// ============================================

// Apify APIトークン
const APIFY_API_TOKEN = "apify_api_UzaYDmTKq9ivHyaatdsPWEbxrPJ9hV4kt3mq";

// Gemini APIキー
const GEMINI_API_KEY = "AIzaSyBgiXdrBD4e1_ak_d0fVFlU8eOanCeG3EU";

// 使用するApify Actor ID
const ACTOR_ID = "apidojo~tweet-scraper";

// シート名
const INPUT_SHEET_NAME = "検索条件入力";
const OUTPUT_SHEET_NAME = "検索結果";
const POST_GENERATION_SHEET_NAME = "投稿生成";

// 最大投稿生成数
const MAX_GENERATED_POSTS = 5;

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
    .addItem('条件なし検索実行', 'runApifySearchNoCondition')
    .addItem('検索結果クリア', 'clearSearchResults')
    .addSeparator()
    .addSubMenu(ui.createMenu('✨ 投稿生成')
      .addItem('投稿を生成（5件）', 'generatePosts')
      .addItem('投稿生成シート作成', 'createPostGenerationSheet'))
    .addSeparator()
    .addItem('APIトークンテスト', 'testApiToken')
    .addItem('Gemini APIテスト', 'testGeminiApi')
    .addToUi();
}

/**
 * 条件を指定せずに検索を実行
 */
function runApifySearchNoCondition() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const outputSheet = ss.getSheetByName(OUTPUT_SHEET_NAME);

  if (!outputSheet) {
    SpreadsheetApp.getUi().alert('エラー: 「' + OUTPUT_SHEET_NAME + '」シートが見つかりません');
    return;
  }

  // 最近のトレンドツイートを取得するデフォルトクエリ
  const defaultQuery = "min_faves:100";

  // 実行確認
  const ui = SpreadsheetApp.getUi();
  const response = ui.alert(
    '条件なし検索実行',
    '条件を指定せずに人気ツイートを検索します（min_faves:100）\n\n実行しますか？',
    ui.ButtonSet.YES_NO
  );

  if (response !== ui.Button.YES) {
    return;
  }

  // ステータス表示
  SpreadsheetApp.getActiveSpreadsheet().toast('Apify API検索を実行中（条件なし）...', '処理中', -1);

  try {
    // Apify APIを呼び出し
    const tweets = callApifyApi(defaultQuery);

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
 * 投稿生成シートを作成
 */
function createPostGenerationSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let postSheet = ss.getSheetByName(POST_GENERATION_SHEET_NAME);

  if (postSheet) {
    SpreadsheetApp.getUi().alert('「' + POST_GENERATION_SHEET_NAME + '」シートは既に存在します');
    return;
  }

  // 新しいシートを作成
  postSheet = ss.insertSheet(POST_GENERATION_SHEET_NAME);

  // ヘッダーを設定
  const headers = [
    ['投稿生成設定', '', '', ''],
    ['項目', '値', '説明', ''],
    ['プロンプト', '', '←投稿生成に使用するプロンプト', ''],
    ['トーン', 'カジュアル', '←フォーマル/カジュアル/専門的', ''],
    ['ターゲット層', '一般', '←20代/30代/ビジネス/一般', ''],
    ['', '', '', ''],
    ['生成された投稿', '', '', ''],
    ['No.', '生成投稿', '参考元ツイート', 'いいね数']
  ];

  // ヘッダーを書き込み
  postSheet.getRange(1, 1, headers.length, 4).setValues(headers);

  // スタイル設定
  postSheet.getRange("A1:D1").merge().setBackground("#4285f4").setFontColor("white").setFontWeight("bold").setHorizontalAlignment("center");
  postSheet.getRange("A2:D2").setBackground("#e8f0fe").setFontWeight("bold");
  postSheet.getRange("A7:D7").merge().setBackground("#34a853").setFontColor("white").setFontWeight("bold").setHorizontalAlignment("center");
  postSheet.getRange("A8:D8").setBackground("#e6f4ea").setFontWeight("bold");

  // 列幅を調整
  postSheet.setColumnWidth(1, 100);
  postSheet.setColumnWidth(2, 400);
  postSheet.setColumnWidth(3, 300);
  postSheet.setColumnWidth(4, 100);

  // デフォルトプロンプトを設定
  const defaultPrompt = "以下のツイートを参考に、同じテーマで新しい投稿を作成してください。オリジナリティを持たせつつ、エンゲージメントが高くなるような内容にしてください。140文字以内で作成してください。";
  postSheet.getRange("B3").setValue(defaultPrompt);

  SpreadsheetApp.getActiveSpreadsheet().toast('投稿生成シートを作成しました', '完了', 3);
}

/**
 * 検索結果を基にGemini APIで投稿を生成
 */
function generatePosts() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const outputSheet = ss.getSheetByName(OUTPUT_SHEET_NAME);
  let postSheet = ss.getSheetByName(POST_GENERATION_SHEET_NAME);

  if (!outputSheet) {
    SpreadsheetApp.getUi().alert('エラー: 「' + OUTPUT_SHEET_NAME + '」シートが見つかりません');
    return;
  }

  // 投稿生成シートがなければ作成
  if (!postSheet) {
    createPostGenerationSheet();
    postSheet = ss.getSheetByName(POST_GENERATION_SHEET_NAME);
  }

  // 検索結果を取得
  const lastRow = outputSheet.getLastRow();
  if (lastRow < 2) {
    SpreadsheetApp.getUi().alert('検索結果がありません。先に検索を実行してください。');
    return;
  }

  // プロンプト設定を取得
  const basePrompt = postSheet.getRange("B3").getValue() || "以下のツイートを参考に、同じテーマで新しい投稿を作成してください。";
  const tone = postSheet.getRange("B4").getValue() || "カジュアル";
  const targetAudience = postSheet.getRange("B5").getValue() || "一般";

  // 上位のツイートを取得（いいね数でソート済みと仮定）
  const dataRange = outputSheet.getRange(2, 1, Math.min(lastRow - 1, 10), 12);
  const tweets = dataRange.getValues();

  // 実行確認
  const ui = SpreadsheetApp.getUi();
  const response = ui.alert(
    '投稿生成確認',
    MAX_GENERATED_POSTS + '件の投稿を生成します。\n\nトーン: ' + tone + '\nターゲット: ' + targetAudience + '\n\n実行しますか？',
    ui.ButtonSet.YES_NO
  );

  if (response !== ui.Button.YES) {
    return;
  }

  SpreadsheetApp.getActiveSpreadsheet().toast('Gemini APIで投稿を生成中...', '処理中', -1);

  try {
    const generatedPosts = [];

    // 最大5件の投稿を生成
    for (let i = 0; i < Math.min(tweets.length, MAX_GENERATED_POSTS); i++) {
      const tweet = tweets[i];
      const tweetText = tweet[3]; // D列: ツイート本文
      const likes = tweet[5]; // F列: いいね数

      if (!tweetText) continue;

      // Gemini APIで投稿を生成
      const prompt = buildPrompt(basePrompt, tweetText, tone, targetAudience);
      const generatedText = callGeminiApi(prompt);

      generatedPosts.push([
        i + 1,
        generatedText,
        tweetText.substring(0, 100) + (tweetText.length > 100 ? "..." : ""),
        likes
      ]);

      // レート制限を考慮して少し待機
      Utilities.sleep(1000);
    }

    // 結果を投稿生成シートに書き込み
    if (generatedPosts.length > 0) {
      // 既存の生成結果をクリア
      const existingLastRow = postSheet.getLastRow();
      if (existingLastRow > 8) {
        postSheet.getRange(9, 1, existingLastRow - 8, 4).clearContent();
      }

      // 新しい結果を書き込み
      postSheet.getRange(9, 1, generatedPosts.length, 4).setValues(generatedPosts);
    }

    SpreadsheetApp.getActiveSpreadsheet().toast(
      generatedPosts.length + '件の投稿を生成しました',
      '完了',
      5
    );

    // 投稿生成シートをアクティブに
    postSheet.activate();

  } catch (error) {
    Logger.log('Error: ' + error);
    SpreadsheetApp.getUi().alert('エラー: ' + error.message);
  }
}

/**
 * 投稿生成用のプロンプトを構築
 */
function buildPrompt(basePrompt, tweetText, tone, targetAudience) {
  return `${basePrompt}

【参考ツイート】
${tweetText}

【生成条件】
- トーン: ${tone}
- ターゲット層: ${targetAudience}
- 文字数: 140文字以内
- 絵文字は適度に使用可
- ハッシュタグは1-2個まで

【出力】
生成した投稿のみを出力してください。説明や注釈は不要です。`;
}

/**
 * Gemini APIを呼び出して投稿を生成
 */
function callGeminiApi(prompt) {
  if (!GEMINI_API_KEY || GEMINI_API_KEY === "YOUR_GEMINI_API_KEY_HERE") {
    throw new Error("GEMINI_API_KEYを設定してください");
  }

  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${GEMINI_API_KEY}`;

  const payload = {
    "contents": [{
      "parts": [{
        "text": prompt
      }]
    }],
    "generationConfig": {
      "temperature": 0.8,
      "maxOutputTokens": 256
    }
  };

  const options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(payload),
    "muteHttpExceptions": true
  };

  const response = UrlFetchApp.fetch(url, options);
  const result = JSON.parse(response.getContentText());

  if (response.getResponseCode() !== 200) {
    throw new Error("Gemini API エラー: " + JSON.stringify(result));
  }

  // レスポンスからテキストを抽出
  const candidates = result.candidates || [];
  if (candidates.length > 0 && candidates[0].content && candidates[0].content.parts) {
    return candidates[0].content.parts[0].text.trim();
  }

  throw new Error("Gemini APIから有効なレスポンスが得られませんでした");
}

/**
 * Gemini APIのテスト
 */
function testGeminiApi() {
  if (!GEMINI_API_KEY || GEMINI_API_KEY === "YOUR_GEMINI_API_KEY_HERE") {
    SpreadsheetApp.getUi().alert('GEMINI_API_KEYを設定してください');
    return;
  }

  try {
    const testPrompt = "「こんにちは」と返答してください。";
    const result = callGeminiApi(testPrompt);

    SpreadsheetApp.getUi().alert(
      'Gemini API確認',
      '✓ 接続成功!\n\nテスト応答: ' + result,
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  } catch (error) {
    SpreadsheetApp.getUi().alert('エラー: ' + error.message);
  }
}

// ============================================
// 以下は既存の検索機能（変更なし）
// ============================================

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
