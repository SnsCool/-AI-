/**
 * Zoom動画・文字起こし & NotebookLM Enterprise 統合API
 *
 * 1. Zoom動画コピー・文字起こしDoc作成（GitHub Actionsから呼び出し）
 * 2. NotebookLM自動同期（時間トリガーで定期実行）
 *
 * アカウント: sales@levela.co.jp
 */

// ──────────────────────────────────────────────
// 設定
// ──────────────────────────────────────────────

// Zoom用: Google Drive保存先フォルダ
const ROOT_FOLDER_ID = '1lzfcvVtyN7FCFJWX8GWR3VLyknxVWLnk';

// コピー先フォルダ（SA→sales@移行用）
const COPY_VIDEO_FOLDER_ID = '1gKBpZ1vKRu5LdpTAI_r0qTM_x2Ft1irl';
const COPY_DOC_FOLDER_ID = '1nV5Ftw9IY4XyFAW1f1zjhrZvDS8SHYNE';

// NotebookLM用: GCPプロジェクト設定
const PROJECT_NUMBER = '421666620867';
const LOCATION = 'global';
const NLM_BASE_URL = `https://${LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_NUMBER}/locations/${LOCATION}`;

// スプレッドシート設定
const SPREADSHEET_ID = '1R5oMbJ7E-QfDFhHR164y8JKs6XLnkJcw8zBm2IPSn8E';
const ZOOM_SHEET_NAME = 'Zoom相談一覧';
const ZOOMKEYS_SHEET_NAME = 'ZoomKeys';

// Zoom相談一覧の列
const COL_CUSTOMER = 0;    // A: 顧客名
const COL_ASSIGNEE = 1;    // B: 担当者
const COL_DATETIME = 2;    // C: 面談日時
const COL_TRANSCRIPT = 6;  // G: 文字起こしリンク
const COL_NLM_SYNCED = 11; // L: NotebookLM同期済みフラグ

// 名前エイリアスマップ（表記ゆれ対応）
const NAME_ALIASES = {
  '長谷川こなつ': '長谷川小夏',
  '真﨑ほのか': '真崎ほのか',
  '播磨谷　彩': '播磨谷 彩',
  '須鑓源太': '須鎗源太',
};

// ──────────────────────────────────────────────
// Web API エントリーポイント（統合）
// ──────────────────────────────────────────────

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const action = data.action;
    Logger.log(`[API] アクション: ${action}`);
    let result;

    switch (action) {
      // --- Zoom用 ---
      case 'copy_video':
        result = copyVideoFromServiceAccount(data.video_file_id, data.video_title, data.assignee, data.customer_name);
        break;
      case 'create_transcript':
        result = createTranscriptDoc(data.transcript, data.title, data.assignee, data.customer_name);
        break;
      case 'copy_doc':
        result = copyDocFromServiceAccount(data.doc_file_id, data.doc_title, data.assignee, data.customer_name);
        break;

      // --- NotebookLM用 ---
      case 'create_notebook':
        result = nlmCreateNotebook(data.title);
        break;
      case 'list_notebooks':
        result = nlmListNotebooks();
        break;
      case 'add_text_source':
        result = nlmAddTextSource(data.notebook_id, data.source_name, data.content);
        break;
      case 'add_doc_source':
        result = nlmAddDocSource(data.notebook_id, data.doc_id, data.source_name);
        break;
      case 'batch_add_text_sources':
        result = nlmBatchAddTextSources(data.notebook_id, data.sources);
        break;
      case 'get_notebook':
        result = nlmGetNotebook(data.notebook_id);
        break;

      // --- 共通 ---
      case 'health_check':
        result = { success: true, message: 'Zoom & NotebookLM API is running', timestamp: new Date().toISOString() };
        break;
      case 'compare_assignees':
        result = compareAssigneeNames();
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
    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      error: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    success: true,
    message: 'Zoom & NotebookLM API is running',
    webhookConfigured: !!getDiscordWebhookUrl(),
    timestamp: new Date().toISOString()
  })).setMimeType(ContentService.MimeType.JSON);
}

// ──────────────────────────────────────────────
// Discord通知
// ──────────────────────────────────────────────

function getDiscordWebhookUrl() {
  return PropertiesService.getScriptProperties().getProperty('DISCORD_WEBHOOK_URL');
}

function sendDiscordNotification(title, message, isError = false) {
  const webhookUrl = getDiscordWebhookUrl();
  if (!webhookUrl) return;

  const payload = {
    content: '<@1340666940615823451>',
    embeds: [{
      title: `${isError ? '❌' : '✅'} ${title}`,
      description: message,
      color: isError ? 15158332 : 3066993,
      timestamp: new Date().toISOString(),
      footer: { text: 'GAS Zoom & NLM API' }
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

function logError(functionName, error, details = {}) {
  const errorMessage = error.toString();
  const detailsStr = Object.keys(details).length > 0
    ? '\n\n**詳細:**\n' + Object.entries(details).map(([k, v]) => `• ${k}: ${v}`).join('\n')
    : '';
  Logger.log(`[ERROR] ${functionName}: ${errorMessage}`);
  sendDiscordNotification(`GAS エラー: ${functionName}`, `\`\`\`${errorMessage}\`\`\`${detailsStr}`, true);
}

function logSuccess(functionName, message, notify = false) {
  Logger.log(`[SUCCESS] ${functionName}: ${message}`);
  if (notify) sendDiscordNotification(`GAS 完了: ${functionName}`, message, false);
}

// ══════════════════════════════════════════════
// リトライヘルパー（サーバーエラー時に最大3回再試行）
// ══════════════════════════════════════════════

function withRetry(fn, maxRetries = 3, initialDelay = 2000) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return fn();
    } catch (error) {
      const errorStr = error.toString();
      const isRetryable = errorStr.includes('server error') ||
                          errorStr.includes('Service error') ||
                          errorStr.includes('Service invoked too many times') ||
                          errorStr.includes('Rate Limit') ||
                          errorStr.includes('try again') ||
                          errorStr.includes('500');
      if (!isRetryable || attempt >= maxRetries) {
        throw error;
      }
      const delay = initialDelay * Math.pow(2, attempt);
      Logger.log(`リトライ ${attempt + 1}/${maxRetries}: ${delay}ms待機 (${errorStr.substring(0, 100)})`);
      Utilities.sleep(delay);
    }
  }
}

// ══════════════════════════════════════════════
// Zoom動画・文字起こし機能（リトライ付き）
// ══════════════════════════════════════════════

function copyVideoFromServiceAccount(videoFileId, videoTitle, assignee, customerName) {
  try {
    return withRetry(() => {
      const sourceFile = DriveApp.getFileById(videoFileId);
      const destFolder = DriveApp.getFolderById(COPY_VIDEO_FOLDER_ID);
      const copiedFile = sourceFile.makeCopy(videoTitle, destFolder);
      copiedFile.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
      logSuccess('copyVideoFromServiceAccount', `動画コピー完了: ${customerName}`);
      return { success: true, url: copiedFile.getUrl(), fileId: copiedFile.getId() };
    });
  } catch (error) {
    logError('copyVideoFromServiceAccount', error, { videoFileId, assignee, customerName });
    return { success: false, error: error.toString() };
  }
}

function createTranscriptDoc(transcript, title, assignee, customerName) {
  try {
    return withRetry(() => {
      const rootFolder = DriveApp.getFolderById(ROOT_FOLDER_ID);
      let assigneeFolder = getOrCreateFolderInParent(rootFolder, assignee);
      let customerFolder = getOrCreateFolderInParent(assigneeFolder, customerName);
      let transcriptFolder = getOrCreateFolderInParent(customerFolder, '文字起こし');

      const doc = DocumentApp.create(title);
      const docId = doc.getId();
      doc.getBody().setText(transcript);
      doc.saveAndClose();

      const docFile = DriveApp.getFileById(docId);
      transcriptFolder.addFile(docFile);
      const parents = docFile.getParents();
      while (parents.hasNext()) {
        const parent = parents.next();
        if (parent.getId() !== transcriptFolder.getId()) parent.removeFile(docFile);
      }
      docFile.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
      logSuccess('createTranscriptDoc', `文字起こし作成完了: ${customerName}`);
      return { success: true, url: doc.getUrl(), docId: docId };
    });
  } catch (error) {
    logError('createTranscriptDoc', error, { title, assignee, customerName });
    return { success: false, error: error.toString() };
  }
}

function copyDocFromServiceAccount(docFileId, docTitle, assignee, customerName) {
  try {
    return withRetry(() => {
      const sourceFile = DriveApp.getFileById(docFileId);
      const destFolder = DriveApp.getFolderById(COPY_DOC_FOLDER_ID);
      const copiedFile = sourceFile.makeCopy(docTitle, destFolder);
      copiedFile.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
      logSuccess('copyDocFromServiceAccount', `ドキュメントコピー完了: ${customerName}`);
      return { success: true, url: copiedFile.getUrl(), fileId: copiedFile.getId() };
    });
  } catch (error) {
    logError('copyDocFromServiceAccount', error, { docFileId, assignee, customerName });
    return { success: false, error: error.toString() };
  }
}

function getOrCreateFolderInParent(parentFolder, folderName) {
  const folders = parentFolder.getFoldersByName(folderName);
  if (folders.hasNext()) return folders.next();
  return parentFolder.createFolder(folderName);
}

// ══════════════════════════════════════════════
// NotebookLM Enterprise 機能
// ══════════════════════════════════════════════

function nlmCreateNotebook(title) {
  const url = `${NLM_BASE_URL}/notebooks`;
  const response = nlmCallApi(url, 'POST', { title: title });
  if (response.error) return { success: false, error: response.error };
  const notebookId = response.name ? response.name.split('/').pop() : null;
  return {
    success: true,
    notebookId: notebookId,
    notebookUrl: notebookId ? `https://notebooklm.cloud.google.com/global/notebook/${notebookId}?project=${PROJECT_NUMBER}` : null,
    name: response.name,
    title: response.title
  };
}

function nlmListNotebooks() {
  const url = `${NLM_BASE_URL}/notebooks:listRecentlyViewed?pageSize=500`;
  const response = nlmCallApi(url, 'GET');
  if (response.error) return { success: false, error: response.error };
  const notebooks = (response.notebooks || []).map(nb => ({
    notebookId: nb.name ? nb.name.split('/').pop() : null,
    name: nb.name,
    title: nb.title || '',
    notebookUrl: nb.name ? `https://notebooklm.cloud.google.com/global/notebook/${nb.name.split('/').pop()}?project=${PROJECT_NUMBER}` : null
  }));
  return { success: true, notebooks: notebooks };
}

function nlmGetNotebook(notebookId) {
  const url = `${NLM_BASE_URL}/notebooks/${notebookId}`;
  const response = nlmCallApi(url, 'GET');
  if (response.error) return { success: false, error: response.error };
  return { success: true, notebookId: notebookId, title: response.title, name: response.name };
}

function nlmAddTextSource(notebookId, sourceName, content) {
  const url = `${NLM_BASE_URL}/notebooks/${notebookId}/sources:batchCreate`;
  const response = nlmCallApi(url, 'POST', { userContents: [{ textContent: { sourceName, content } }] });
  if (response.error) return { success: false, error: response.error };
  return { success: true, sources: response.sources || [] };
}

function nlmAddDocSource(notebookId, docId, sourceName) {
  const url = `${NLM_BASE_URL}/notebooks/${notebookId}/sources:batchCreate`;
  const response = nlmCallApi(url, 'POST', {
    userContents: [{ googleDriveContent: { documentId: docId, mimeType: 'application/vnd.google-apps.document', sourceName } }]
  });
  if (response.error) return { success: false, error: response.error };
  return { success: true, sources: response.sources || [] };
}

function nlmBatchAddTextSources(notebookId, sources) {
  const url = `${NLM_BASE_URL}/notebooks/${notebookId}/sources:batchCreate`;
  const response = nlmCallApi(url, 'POST', {
    userContents: sources.map(s => ({ textContent: { sourceName: s.sourceName, content: s.content } }))
  });
  if (response.error) return { success: false, error: response.error };
  return { success: true, sources: response.sources || [] };
}

function nlmCallApi(url, method, payload) {
  const token = ScriptApp.getOAuthToken();
  const options = {
    method: method.toLowerCase(),
    headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
    muteHttpExceptions: true
  };
  if (payload && method.toUpperCase() !== 'GET') options.payload = JSON.stringify(payload);
  const response = UrlFetchApp.fetch(url, options);
  const code = response.getResponseCode();
  const body = response.getContentText();
  if (code >= 200 && code < 300) return body ? JSON.parse(body) : {};
  Logger.log('API Error (' + code + '): ' + body);
  return { error: 'HTTP ' + code + ': ' + body };
}

// ══════════════════════════════════════════════
// NotebookLM 自動同期（時間トリガー）
// ══════════════════════════════════════════════

function syncNewTranscripts() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const zoomSheet = ss.getSheetByName(ZOOM_SHEET_NAME);
  const zoomData = zoomSheet.getDataRange().getValues();
  const keysSheet = ss.getSheetByName(ZOOMKEYS_SHEET_NAME);
  const keysData = keysSheet.getDataRange().getValues();

  const assigneeMap = {};
  for (let i = 1; i < keysData.length; i++) {
    const name = (keysData[i][0] || '').toString().trim();
    if (name) {
      assigneeMap[name] = {
        row: i + 1,
        notebookUrl: (keysData[i][4] || '').toString().trim()
      };
    }
  }

  const nbList = nlmListNotebooks();
  const existingNotebooks = nbList.success ? nbList.notebooks : [];
  const nbByTitle = {};
  existingNotebooks.forEach(nb => { if (nb.title) nbByTitle[nb.title] = nb; });

  let syncCount = 0;

  for (let i = 1; i < zoomData.length; i++) {
    const row = zoomData[i];
    const rawAssignee = (row[COL_ASSIGNEE] || '').toString().trim();
    const transcriptUrl = (row[COL_TRANSCRIPT] || '').toString().trim();
    const synced = (row[COL_NLM_SYNCED] || '').toString().trim();

    if (!rawAssignee || !transcriptUrl || synced === 'synced') continue;

    const assignee = resolveAssigneeName(rawAssignee, assigneeMap);
    const customer = (row[COL_CUSTOMER] || '').toString().trim();
    const meetingDate = (row[COL_DATETIME] || '').toString().trim();
    const docId = extractDocId(transcriptUrl);
    if (!docId) continue;

    Logger.log(`処理中: ${rawAssignee}${rawAssignee !== assignee ? '→' + assignee : ''} - ${customer} (${meetingDate})`);

    const nbTitle = `${assignee}_面談記録`;
    let notebook = nbByTitle[nbTitle];

    if (!notebook) {
      const createResult = nlmCreateNotebook(nbTitle);
      if (!createResult.success) { Logger.log(`ノートブック作成失敗: ${createResult.error}`); continue; }
      notebook = { notebookId: createResult.notebookId, notebookUrl: createResult.notebookUrl, title: nbTitle };
      nbByTitle[nbTitle] = notebook;
      if (assigneeMap[assignee] && !assigneeMap[assignee].notebookUrl) {
        keysSheet.getRange(assigneeMap[assignee].row, 5).setValue(createResult.notebookUrl);
        assigneeMap[assignee].notebookUrl = createResult.notebookUrl;
      }
    }

    const sourceName = `${customer}_${meetingDate}`;
    const result = nlmAddDocSource(notebook.notebookId, docId, sourceName);

    if (result.success) {
      zoomSheet.getRange(i + 1, COL_NLM_SYNCED + 1).setValue('synced');
      syncCount++;
      Logger.log(`  追加成功: ${sourceName}`);
    } else {
      Logger.log(`  追加失敗: ${result.error}`);
      if (result.error && (result.error.includes('403') || result.error.includes('PERMISSION'))) {
        try {
          const doc = DocumentApp.openById(docId);
          const text = doc.getBody().getText();
          if (text) {
            const textResult = nlmAddTextSource(notebook.notebookId, sourceName, text);
            if (textResult.success) {
              zoomSheet.getRange(i + 1, COL_NLM_SYNCED + 1).setValue('synced');
              syncCount++;
              Logger.log(`  テキスト渡しで追加成功`);
            }
          }
        } catch (docError) { Logger.log(`  Docs読み取りも失敗: ${docError}`); }
      }
    }
    Utilities.sleep(2000);
  }
  Logger.log(`同期完了: ${syncCount}件追加`);
}

function extractDocId(url) {
  const match = url.match(/\/d\/([a-zA-Z0-9_-]+)/);
  return match ? match[1] : null;
}

function resolveAssigneeName(name, assigneeMap) {
  if (NAME_ALIASES[name]) return NAME_ALIASES[name];
  if (assigneeMap[name]) return name;
  const surnames = [name.substring(0, 3), name.substring(0, 2)];
  for (const surname of surnames) {
    const candidates = Object.keys(assigneeMap).filter(k => k.startsWith(surname));
    if (candidates.length === 1) {
      Logger.log(`  名前解決: ${name} → ${candidates[0]}（姓一致）`);
      return candidates[0];
    }
  }
  return name;
}

// ──────────────────────────────────────────────
// トリガー設定・テスト関数
// ──────────────────────────────────────────────

function setupTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(t => { if (t.getHandlerFunction() === 'syncNewTranscripts') ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('syncNewTranscripts').timeBased().everyHours(1).create();
  Logger.log('トリガー設定完了: 1時間ごとに syncNewTranscripts を実行');
}

function setupDiscordWebhook() {
  const webhookUrl = 'https://discord.com/api/webhooks/1470665385924886703/_RzEIe_OzrkDeCVYuGb1k2FeSKzHQNe6Lo_XGqf9xcwBFNtVqxqhEOCBDIE_adcldHZc';
  PropertiesService.getScriptProperties().setProperty('DISCORD_WEBHOOK_URL', webhookUrl);
  Logger.log('Discord Webhook URL を設定しました');
}

function testHealthCheck() {
  const testData = { postData: { contents: JSON.stringify({ action: 'health_check' }) } };
  const result = doPost(testData);
  Logger.log(result.getContent());
}

function testSync() {
  syncNewTranscripts();
}

function testListNotebooks() {
  const result = nlmListNotebooks();
  Logger.log(JSON.stringify(result));
}

function compareAssigneeNames() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);

  const keysSheet = ss.getSheetByName(ZOOMKEYS_SHEET_NAME);
  const keysData = keysSheet.getDataRange().getValues();
  const keysNames = new Set();
  for (let i = 1; i < keysData.length; i++) {
    const name = (keysData[i][0] || '').toString().trim();
    if (name) keysNames.add(name);
  }

  const custSheet = ss.getSheetByName('顧客一覧');
  const custData = custSheet.getDataRange().getValues();
  const custNamesCount = {};
  for (let i = 1; i < custData.length; i++) {
    const name = (custData[i][1] || '').toString().trim();
    if (name && name !== '担当者') {
      custNamesCount[name] = (custNamesCount[name] || 0) + 1;
    }
  }

  const zoomSheet = ss.getSheetByName(ZOOM_SHEET_NAME);
  const zoomData = zoomSheet.getDataRange().getValues();
  const zoomNamesCount = {};
  for (let i = 1; i < zoomData.length; i++) {
    const name = (zoomData[i][COL_ASSIGNEE] || '').toString().trim();
    if (name && name !== '担当者') {
      zoomNamesCount[name] = (zoomNamesCount[name] || 0) + 1;
    }
  }

  const allNames = new Set([...Object.keys(custNamesCount), ...Object.keys(zoomNamesCount)]);

  const results = [];
  for (const name of allNames) {
    const inKeys = keysNames.has(name);
    const inCust = custNamesCount[name] || 0;
    const inZoom = zoomNamesCount[name] || 0;

    let alias = null;
    let aliasInKeys = false;
    if (!inKeys) {
      if (NAME_ALIASES[name]) {
        alias = NAME_ALIASES[name];
        aliasInKeys = keysNames.has(alias);
      } else {
        const surnames = [name.substring(0, 3), name.substring(0, 2)];
        for (const surname of surnames) {
          const candidates = [...keysNames].filter(k => k.startsWith(surname));
          if (candidates.length === 1) {
            alias = candidates[0];
            aliasInKeys = true;
            break;
          }
        }
      }
    }

    results.push({
      name,
      inCustomerList: inCust,
      inZoomList: inZoom,
      inZoomKeys: inKeys,
      alias: alias,
      aliasInKeys: aliasInKeys,
      status: inKeys ? 'OK' : (aliasInKeys ? 'ALIAS' : 'NO_MATCH')
    });
  }

  const ok = results.filter(r => r.status === 'OK');
  const aliased = results.filter(r => r.status === 'ALIAS');
  const noMatch = results.filter(r => r.status === 'NO_MATCH');

  return {
    success: true,
    summary: {
      totalUnique: allNames.size,
      ok: ok.length,
      alias: aliased.length,
      noMatch: noMatch.length,
      keysTotal: keysNames.size,
      customerListRows: custData.length - 1,
      zoomListRows: zoomData.length - 1
    },
    noMatch, aliased, ok
  };
}

function deleteAllTriggers() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(t => ScriptApp.deleteTrigger(t));
  Logger.log('全トリガーを削除しました: ' + triggers.length + '件');
}

/**
 * DriveApp権限修復用 — これを実行して権限を再承認してください
 */
function fixDriveAuth() {
  Logger.log(DriveApp.getRootFolder().getName());
}
