/**
 * Zoom動画・文字起こしAPI
 *
 * Pythonから呼び出して、動画コピーと文字起こしドキュメント作成を行う
 * エラー時はDiscord通知を送信
 */

// ★設定（スクリプトプロパティから取得）
const ROOT_FOLDER_ID = '1lzfcvVtyN7FCFJWX8GWR3VLyknxVWLnk';

/**
 * Discord Webhook URLを取得
 * スクリプトプロパティに DISCORD_WEBHOOK_URL を設定してください
 */
function getDiscordWebhookUrl() {
  return PropertiesService.getScriptProperties().getProperty('DISCORD_WEBHOOK_URL');
}

/**
 * Discord通知を送信
 */
function sendDiscordNotification(title, message, isError = false) {
  const webhookUrl = getDiscordWebhookUrl();
  if (!webhookUrl) {
    Logger.log('Discord Webhook URLが設定されていません');
    return;
  }

  const color = isError ? 15158332 : 3066993; // 赤 or 緑
  const icon = isError ? '❌' : '✅';
  const mention = '<@1340666940615823451>'; // 常にメンション

  const payload = {
    content: mention,
    embeds: [{
      title: `${icon} ${title}`,
      description: message,
      color: color,
      timestamp: new Date().toISOString(),
      footer: {
        text: 'GAS Zoom API'
      }
    }]
  };

  try {
    UrlFetchApp.fetch(webhookUrl, {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });
  } catch (e) {
    Logger.log('Discord通知エラー: ' + e.toString());
  }
}

/**
 * エラーログを記録してDiscord通知
 */
function logError(functionName, error, details = {}) {
  const errorMessage = error.toString();
  const detailsStr = Object.keys(details).length > 0
    ? '\n\n**詳細:**\n' + Object.entries(details).map(([k, v]) => `• ${k}: ${v}`).join('\n')
    : '';

  Logger.log(`[ERROR] ${functionName}: ${errorMessage}`);

  sendDiscordNotification(
    `GAS エラー: ${functionName}`,
    `\`\`\`${errorMessage}\`\`\`${detailsStr}`,
    true
  );
}

/**
 * 成功ログを記録（通知はオプション）
 */
function logSuccess(functionName, message, notify = false) {
  Logger.log(`[SUCCESS] ${functionName}: ${message}`);

  if (notify) {
    sendDiscordNotification(`GAS 完了: ${functionName}`, message, false);
  }
}

/**
 * Web APIエントリーポイント（POST）
 */
function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const action = data.action;

    Logger.log(`[API] アクション: ${action}`);

    let result;

    switch (action) {
      case 'copy_video':
        result = copyVideoFromServiceAccount(
          data.video_file_id,
          data.video_title,
          data.assignee,
          data.customer_name
        );
        break;

      case 'create_transcript':
        result = createTranscriptDoc(
          data.transcript,
          data.title,
          data.assignee,
          data.customer_name
        );
        break;

      case 'copy_doc':
        result = copyDocFromServiceAccount(
          data.doc_file_id,
          data.doc_title,
          data.assignee,
          data.customer_name
        );
        break;

      case 'health_check':
        result = { success: true, message: 'GAS is working' };
        break;

      default:
        result = { success: false, error: 'Unknown action: ' + action };
        logError('doPost', 'Unknown action: ' + action);
    }

    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    logError('doPost', error, {
      postData: e.postData ? e.postData.contents.substring(0, 200) : 'N/A'
    });

    const errorResult = {
      success: false,
      error: error.toString()
    };
    return ContentService.createTextOutput(JSON.stringify(errorResult))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Web APIエントリーポイント（GET - 動作確認用）
 */
function doGet(e) {
  const action = e.parameter ? e.parameter.action : null;

  // セットアップアクション
  if (action === 'setup') {
    setupDiscordWebhook();
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      message: 'Discord Webhook URL を設定しました',
      timestamp: new Date().toISOString()
    })).setMimeType(ContentService.MimeType.JSON);
  }

  // テスト通知アクション
  if (action === 'test') {
    sendDiscordNotification('GAS テスト通知', 'Web APIからのテスト通知です', false);
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      message: 'テスト通知を送信しました',
      timestamp: new Date().toISOString()
    })).setMimeType(ContentService.MimeType.JSON);
  }

  // デフォルト: ヘルスチェック
  return ContentService.createTextOutput(JSON.stringify({
    success: true,
    message: 'Zoom Video & Transcript API is running',
    webhookConfigured: !!getDiscordWebhookUrl(),
    timestamp: new Date().toISOString()
  })).setMimeType(ContentService.MimeType.JSON);
}

/**
 * サービスアカウントがアップロードした動画をコピー
 */
function copyVideoFromServiceAccount(videoFileId, videoTitle, assignee, customerName) {
  try {
    const sourceFile = DriveApp.getFileById(videoFileId);
    const rootFolder = DriveApp.getFolderById(ROOT_FOLDER_ID);

    // 担当者フォルダを取得または作成
    let assigneeFolder = getOrCreateFolderInParent(rootFolder, assignee);

    // 顧客フォルダを取得または作成
    let customerFolder = getOrCreateFolderInParent(assigneeFolder, customerName);

    // 動画サブフォルダを取得または作成
    let videoFolder = getOrCreateFolderInParent(customerFolder, '動画');

    // ファイルをコピー
    const copiedFile = sourceFile.makeCopy(videoTitle, videoFolder);

    // 公開権限を設定
    copiedFile.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);

    const fileUrl = copiedFile.getUrl();
    logSuccess('copyVideoFromServiceAccount', `動画コピー完了: ${customerName}`);

    return {
      success: true,
      url: fileUrl,
      fileId: copiedFile.getId()
    };

  } catch (error) {
    logError('copyVideoFromServiceAccount', error, {
      videoFileId: videoFileId,
      assignee: assignee,
      customerName: customerName
    });
    return {
      success: false,
      error: error.toString()
    };
  }
}

/**
 * 文字起こしドキュメントを作成
 */
function createTranscriptDoc(transcript, title, assignee, customerName) {
  try {
    const rootFolder = DriveApp.getFolderById(ROOT_FOLDER_ID);

    // 担当者フォルダを取得または作成
    let assigneeFolder = getOrCreateFolderInParent(rootFolder, assignee);

    // 顧客フォルダを取得または作成
    let customerFolder = getOrCreateFolderInParent(assigneeFolder, customerName);

    // 文字起こしサブフォルダを取得または作成
    let transcriptFolder = getOrCreateFolderInParent(customerFolder, '文字起こし');

    // Google Docsを作成
    const doc = DocumentApp.create(title);
    const docId = doc.getId();

    // 文字起こし内容を挿入
    const body = doc.getBody();
    body.setText(transcript);
    doc.saveAndClose();

    // フォルダに移動
    const docFile = DriveApp.getFileById(docId);
    transcriptFolder.addFile(docFile);

    // ルートから削除
    const parents = docFile.getParents();
    while (parents.hasNext()) {
      const parent = parents.next();
      if (parent.getId() !== transcriptFolder.getId()) {
        parent.removeFile(docFile);
      }
    }

    // 公開権限を設定
    docFile.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);

    const docUrl = doc.getUrl();
    logSuccess('createTranscriptDoc', `文字起こし作成完了: ${customerName}`);

    return {
      success: true,
      url: docUrl,
      docId: docId
    };

  } catch (error) {
    logError('createTranscriptDoc', error, {
      title: title,
      assignee: assignee,
      customerName: customerName
    });
    return {
      success: false,
      error: error.toString()
    };
  }
}

/**
 * サービスアカウントが作成したドキュメントをコピー
 */
function copyDocFromServiceAccount(docFileId, docTitle, assignee, customerName) {
  try {
    const sourceFile = DriveApp.getFileById(docFileId);
    const rootFolder = DriveApp.getFolderById(ROOT_FOLDER_ID);

    // 担当者フォルダを取得または作成
    let assigneeFolder = getOrCreateFolderInParent(rootFolder, assignee);

    // 顧客フォルダを取得または作成
    let customerFolder = getOrCreateFolderInParent(assigneeFolder, customerName);

    // 文字起こしサブフォルダを取得または作成
    let transcriptFolder = getOrCreateFolderInParent(customerFolder, '文字起こし');

    // ファイルをコピー
    const copiedFile = sourceFile.makeCopy(docTitle, transcriptFolder);

    // 公開権限を設定
    copiedFile.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);

    const fileUrl = copiedFile.getUrl();
    logSuccess('copyDocFromServiceAccount', `ドキュメントコピー完了: ${customerName}`);

    return {
      success: true,
      url: fileUrl,
      fileId: copiedFile.getId()
    };

  } catch (error) {
    logError('copyDocFromServiceAccount', error, {
      docFileId: docFileId,
      assignee: assignee,
      customerName: customerName
    });
    return {
      success: false,
      error: error.toString()
    };
  }
}

/**
 * 親フォルダ内にサブフォルダを取得または作成
 */
function getOrCreateFolderInParent(parentFolder, folderName) {
  const folders = parentFolder.getFoldersByName(folderName);

  if (folders.hasNext()) {
    return folders.next();
  }

  return parentFolder.createFolder(folderName);
}

/**
 * テスト用：Discord通知テスト
 */
function testDiscordNotification() {
  sendDiscordNotification('テスト通知', 'GASからのテスト通知です', false);
  Logger.log('Discord通知テスト完了');
}

/**
 * テスト用：エラー通知テスト
 */
function testErrorNotification() {
  logError('testErrorNotification', 'これはテストエラーです', {
    テスト項目: 'テスト値',
    時刻: new Date().toLocaleString('ja-JP')
  });
}

/**
 * テスト用：API動作確認
 */
function testHealthCheck() {
  const testData = {
    postData: {
      contents: JSON.stringify({ action: 'health_check' })
    }
  };
  const result = doPost(testData);
  Logger.log(result.getContent());
}

/**
 * 初期設定：Discord Webhook URLを設定
 * ※ 一度だけ実行してください
 */
function setupDiscordWebhook() {
  const webhookUrl = 'https://discord.com/api/webhooks/1470665385924886703/_RzEIe_OzrkDeCVYuGb1k2FeSKzHQNe6Lo_XGqf9xcwBFNtVqxqhEOCBDIE_adcldHZc';
  PropertiesService.getScriptProperties().setProperty('DISCORD_WEBHOOK_URL', webhookUrl);
  Logger.log('Discord Webhook URL を設定しました');

  // 設定確認
  const saved = PropertiesService.getScriptProperties().getProperty('DISCORD_WEBHOOK_URL');
  if (saved) {
    Logger.log('確認OK: ' + saved.substring(0, 50) + '...');
  }
}

/**
 * 設定確認用
 */
function checkWebhookSetting() {
  const url = PropertiesService.getScriptProperties().getProperty('DISCORD_WEBHOOK_URL');
  if (url) {
    Logger.log('Webhook URL設定済み: ' + url.substring(0, 60) + '...');
    return true;
  } else {
    Logger.log('Webhook URLが設定されていません。setupDiscordWebhook()を実行してください。');
    return false;
  }
}
