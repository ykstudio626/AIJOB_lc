/*****************************************************
 * 共通設定
 *****************************************************/
const MAX_ROWS = 30; // ✅ 取得最大行数（上限）
const SHEETS = {
  "yoin": "gmail要員情報",
  "anken": "gmail案件情報",
  "yoin_struct": "最新要員情報",
  "anken_struct": "最新案件情報"
};


/*****************************************************
 * GmailからSpreadsheetに生データ出力＆分類
 *****************************************************/
function exportGmailToSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // === 設定値 ===
  const LOOKBACK_DAYS = 1;
  const THREAD_LIMIT = 500;
  const CATEGORY_SHEETS = {
    "案件": "最新案件情報",
    "要員": "最新要員情報",
    "不明": "要確認"
  };
  const RAW_SHEETS = { // 👈 Dify用 未構造化データ
    "案件": "gmail案件情報",
    "要員": "gmail要員情報"
  };

  const now = new Date();
  const cutoffDate = new Date(now.getTime() - LOOKBACK_DAYS * 24 * 60 * 60 * 1000);

  // === 各シートの存在確認 ===
  for (const name of Object.values(CATEGORY_SHEETS)) {
    if (!ss.getSheetByName(name)) {
      const sheet = ss.insertSheet(name);
      sheet.appendRow(["ID", "受信日時", "From", "Subject", "本文", "分類", "ステータス"]);
      Logger.log(`🆕 シート「${name}」を作成しました。`);
    }
  }
  for (const name of Object.values(RAW_SHEETS)) {
    if (!ss.getSheetByName(name)) {
      const sheet = ss.insertSheet(name);
      // 👇 分類列（category）を追加
      sheet.appendRow(["ID", "受信日時", "件名", "本文", "分類"]);
      Logger.log(`🆕 シート「${name}」を作成しました。`);
    }
  }

  // === Gmail取得 ===
  const threads = GmailApp.getInboxThreads(0, THREAD_LIMIT);
  Logger.log(`📥 Gmailスレッド ${threads.length} 件を取得しました。`);

  let projectCount = 0;
  let resourceCount = 0;
  let unknownCount = 0;

  for (let i = 0; i < threads.length; i++) {
    try {
      const msg = threads[i].getMessages()[0];
      const rawDate = msg.getDate();
      if (rawDate < cutoffDate) continue;

      const formattedDate = Utilities.formatDate(rawDate, Session.getScriptTimeZone(), "yyyy/MM/dd HH:mm");
      const from = msg.getFrom();
      const subject = msg.getSubject();
      const body = msg.getPlainBody();

      // === スコア判定 ===
      const category = classifyMailType(subject, body);

      const prefix = (category === "案件")?"A":"Y";

      const id = prefix + Utilities.formatDate(now, Session.getScriptTimeZone(), "yyyyMMddHHmmss") + "-" + (i + 1);
      
      // === 未構造化データも別途出力 ===
      if (category === "案件" || category === "要員") {
        const rawSheet = ss.getSheetByName(RAW_SHEETS[category]);
        // 👇 分類も書き込む
        rawSheet.appendRow([id, formattedDate, subject, body, category]);
      }

      // === 進捗ログ ===
      const progress = ((i + 1) / threads.length * 100).toFixed(1);
      Logger.log(
        `📨 ${i + 1}/${threads.length}件目 (${progress}%)\n` +
        `受信日時: ${formattedDate}\n分類: ${category}\n件名: ${subject}\n送信者: ${from}\n`
      );

      if (category === "案件") projectCount++;
      else if (category === "要員") resourceCount++;
      else unknownCount++;

    } catch (e) {
      Logger.log(`⚠️ ${i + 1}件目でエラー: ${e.message}`);
    }
  }

  Logger.log(`✅ 完了 案件=${projectCount}, 要員=${resourceCount}, 不明=${unknownCount}`);
}

/*****************************************************
 * 案件／要員 判別ロジック
 *****************************************************/
function classifyMailType(subject, body) {
  // === スコア判定 ===
      let score_anken = 0;
      let score_yoin = 0;

      if (subject.match(/募集|急募|案件情報|案件/)) score_anken += 2;
      if (subject.match(/要員|要員情報|人材|個人|案件希望|社員/)) score_yoin += 2;
      if (body.match(/案件名|面談|契約形態|必須|尚可|作業場所|契約期間/)) score_anken += 2;
      if (body.match(/氏名|最寄|スキルシート|要員リスト|希望単価|所属/)) score_yoin += 2;

      let category = "不明";
      if (score_anken > score_yoin && score_anken >= 1) category = "案件";
      else if (score_yoin > score_anken && score_yoin >= 1) category = "要員";
      return category;
}

/*****************************************************
 - gmail内の古いメールの削除
 * 特定の日付以前のものを削除
 * 動作未確認
 * TODO シート内も削除
 *****************************************************/
function deleteOldLabeledEmails() {
  // ★ ここを変更 ★
  const targetLabel = "SES要員";
  const beforeDate = "2025/07/31"; // YYYY/MM/DD 形式

  const query = `label:${targetLabel} before:${beforeDate}`;

  const threads = GmailApp.search(query, 0, 5000); // 最大5000件取得（必要ならループ）
  let count = 0;

  while (threads.length > 0) {
    for (const t of threads) {
      t.moveToTrash(); // ゴミ箱へ移動（30日後に完全削除）
      count++;
    }
    // 次の500件を取得
    threads = GmailApp.search(query, 0, 5000);
  }

  console.log(`削除したスレッド数: ${count}`);
}

/*****************************************************
 - gmail内の古いメールの削除
 * 2ヶ月以前のものを削除
 * TODO シート内も削除
 *****************************************************/
function deleteOldLabeledEmailsFixed() {
  // ★ここだけ変更してください★
  const targetLabel = "SES要員";  // 対象ラベル名
  
  // ▼ 今日から2ヶ月前の日付を計算
  const today = new Date();
  const MonthsAgo = new Date(
    today.getFullYear(),
    today.getMonth() - 2, // ２ヶ月
    today.getDate()
  );

  // Gmail 検索用に YYYY/MM/DD にフォーマット
  const formatted = Utilities.formatDate(MonthsAgo, Session.getScriptTimeZone(), "yyyy/MM/dd");

  // 特定の日付ならここでハードコーディング
  // const formatted = '2025/07/01'

  const query = `label:${targetLabel} before:${formatted}`;
  console.log("検索クエリ:", query);

  let threads = GmailApp.search(query, 0, 500);
  let count = 0;

  while (threads.length > 0) {
    for (const t of threads) {
      t.moveToTrash();   // ゴミ箱へ（安全）
      count++;
    }
    // 次の500件を再検索
    threads = GmailApp.search(query, 0, 500);
  }

  console.log(`削除したスレッド数: ${count}`);
}


/*****************************************************
 * ✅ getSheetData - 日付・limit・offset対応 完成版
 *****************************************************/
function getSheetData(sheetName, options) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    return { error: `シート「${sheetName}」が見つかりません` };
  }

  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();
  if (lastRow < 2) {
    return { type: sheetName, count_total: 0, count_returned: 0, records: [] };
  }

  const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];

  // --- オプション ---
  const limit    = Math.max(1, Number(options.limit || 200));
  const offset   = Math.max(0, Number(options.offset || 0));
  const colsList = (options.cols && options.cols.length) ? options.cols : null;
  const bodyLen  = (options.bodyLen === 0) ? 0 : (options.bodyLen ? Number(options.bodyLen) : null);
  const maxBytes = Number(options.maxBytes || 900000);
  const startIso = options.startIso || null; // YYYYMMDD
  const endIso   = options.endIso   || null; // YYYYMMDD

  // --- YYYYMMDD → JST Date ---
  function parseYmdToJst(ymd, isEnd) {
    if (!ymd) return null;
    const y = Number(ymd.slice(0, 4));
    const m = Number(ymd.slice(4, 6)) - 1;
    const d = Number(ymd.slice(6, 8));
    return isEnd
      ? new Date(y, m, d, 23, 59, 59, 999).getTime()
      : new Date(y, m, d, 0, 0, 0, 0).getTime();
  }


  const startTime = startIso ? parseYmdToJst(startIso, false) : null;
  const endTime   = endIso   ? parseYmdToJst(endIso, true)  : null;
  

  // --- 対象列 ---
  const colIdx = [];
  headers.forEach((h, i) => {
    if (!colsList || colsList.indexOf(h) !== -1) {
      if (h === "本文" && bodyLen === 0) return;
      colIdx.push(i);
    }
  });

  const recvIdx = headers.indexOf("受信日時");

  // --- 全データ取得（ヘッダ除外）→ 新しい順 ---
  const allValues = sheet.getRange(2, 1, lastRow - 1, lastCol).getValues().reverse();

  const out = [];
  let bytes = 0;
  const commaBytes = Utilities.newBlob(",").getBytes().length;
  let skipped = 0;

  for (const row of allValues) {
    if (!row.some(v => v !== "" && v != null)) continue;

    // --- 日付フィルタ ---
    if (recvIdx >= 0 && (startTime || endTime)) {
      const t = (row[recvIdx] instanceof Date)
        ? row[recvIdx].getTime()
        : new Date(row[recvIdx]).getTime();

      if (startTime && t < startTime) continue;
      if (endTime && t > endTime) continue;
    }

  
    // --- offset ---
    if (skipped < offset) {
      skipped++;
      continue;
    }

    // --- レコード生成 ---
    const obj = {};
    for (const i of colIdx) {
      let val = row[i];
      if (headers[i] === "本文" && typeof val === "string" && bodyLen && bodyLen > 0) {
        if (val.length > bodyLen) val = val.substring(0, bodyLen);
      }
      obj[headers[i]] = val;
    }

    const piece = JSON.stringify(obj);
    const addBytes = (out.length ? commaBytes : 0) + Utilities.newBlob(piece).getBytes().length;
    if (bytes + addBytes > maxBytes) break;

    out.push(obj);
    bytes += addBytes;

    if (out.length >= limit) break;
  }

  return {
    type: sheetName,
    count_total: lastRow - 1,
    count_returned: out.length,
    records: out
  };
}

/*****************************************************
 * ✅ doGet - Difyから安全にデータ取得
 * ?type=yoin または ?type=anken
 * ?type=yoin_format&id=xxxxx で特定IDを取得
 * ?type=anken_format&id=xxxxx,yyyyy で複数IDを取得
 *****************************************************/
function doGet(e) {
  const GET_LIMIT = 100;
  const type = (e && e.parameter && e.parameter.type) || "yoin_struct";

  const p = (e && e.parameter) ? e.parameter : {};

  let sheetName = "gmail要員情報";
  if (type === "anken") sheetName = "gmail案件情報";
  if (type === "yoin_format") sheetName = "最新要員情報";
  if (type === "anken_format") sheetName = "最新案件情報";

  // ★ ID指定がある場合は別処理
  const idParam = e?.parameter?.id ? String(e.parameter.id) : null;
  if (idParam) {
    const ids = idParam.split(",").map(id => id.trim()).filter(id => id);
    const data = getSheetDataByIds(sheetName, ids);
    
    const json = JSON.stringify({
      debug: {
        hasE: !!e,
        keys: Object.keys(p),
        ids: ids
      },
      type: type,
      count: data.records.length,
      records: data.records
    });
    
    return ContentService.createTextOutput(json).setMimeType(ContentService.MimeType.JSON);
  }

  const limit = e.parameter.limit ? Number(e.parameter.limit) : GET_LIMIT;
  const offset = e.parameter.offset ? Number(e.parameter.offset) : 0;
  const cols  = e.parameter.cols ? String(e.parameter.cols).split(",") : null;
  const bodyLen = (e.parameter.body_len != null) ? Number(e.parameter.body_len) : null;
  const maxBytes = e.parameter.max_bytes ? Number(e.parameter.max_bytes) : 900000;

  // ★ 新しく追加
  const startIso = e?.parameter?.start_date ? String(e.parameter.start_date) : null;
  const endIso   = e?.parameter?.end_date   ? String(e.parameter.end_date)   : null;

  // === データ取得 ===
  const data = getSheetData(sheetName, {
    limit: limit,
    offset: offset,
    cols: cols,
    bodyLen: bodyLen,
    maxBytes: maxBytes,
    startIso: startIso,   // ★ 追加
    endIso: endIso        // ★ 追加
  });

  const json = JSON.stringify({
    debug: {
        hasE: !!e,
        keys: Object.keys(p),
        start_date_raw: p.start_date,
        end_date_raw: p.end_date,
        startIso,
        endIso
      },
    type: type,
    count: data.count_returned,
    records: data.records
  });

  return ContentService.createTextOutput(json).setMimeType(ContentService.MimeType.JSON);
}

/*****************************************************
 * ✅ getSheetDataByIds - 特定IDのデータを取得
 * @param {string} sheetName - シート名
 * @param {string[]} ids - 取得するIDの配列
 * @return {Object} { records: [...] }
 *****************************************************/
function getSheetDataByIds(sheetName, ids) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);
  
  if (!sheet) {
    return { error: `シート「${sheetName}」が見つかりません`, records: [] };
  }

  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();
  
  if (lastRow < 2) {
    return { records: [] };
  }

  const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  const allValues = sheet.getRange(2, 1, lastRow - 1, lastCol).getValues();
  
  // ID列のインデックスを探す
  const idIdx = headers.indexOf("ID");
  if (idIdx === -1) {
    return { error: "ID列が見つかりません", records: [] };
  }

  // IDセットを作成（高速検索用）
  const idSet = new Set(ids);
  
  const records = [];
  for (const row of allValues) {
    const rowId = String(row[idIdx]).trim();
    
    if (idSet.has(rowId)) {
      const obj = {};
      headers.forEach((h, i) => {
        obj[h] = row[i];
      });
      records.push(obj);
    }
  }

  return { records: records };
}

/*****************************************************
 * YYYYMMDD → ISO文字列（YYYY-MM-DD）
 *****************************************************/
function convertDate(str) {
  if (!str || str.length !== 8) return null;
  const y = str.substring(0, 4);
  const m = str.substring(4, 6);
  const d = str.substring(6, 8);
  return `${y}-${m}-${d}`;
}

/*****************************************************
 * 値のトリム（正規化）
 *****************************************************/
function normalizeValue(val) {
  if (val === null || val === undefined) return "";
  return String(val).trim();
}

/*****************************************************
 * 年齢のマッチ
 *****************************************************/
function ageMatches(a, b) {
  const na = Number(a);
  const nb = Number(b);
  if (isNaN(na) || isNaN(nb)) return false;
  return Math.abs(na - nb) <= 1;
}

/*****************************************************
 * Pinecone削除機能
 *****************************************************/

/**
 * Pinecone設定を確認・設定するヘルパー関数
 * 手動実行でスクリプトプロパティを設定
 */
function setupPineconeConfig() {
  const props = PropertiesService.getScriptProperties();
  
  // 現在の設定を確認
  const currentApiKey = props.getProperty('PINECONE_API_KEY');
  const currentHost = props.getProperty('PINECONE_INDEX_HOST');
  
  console.log("=== Pinecone設定確認 ===");
  console.log("PINECONE_API_KEY:", currentApiKey ? `設定済み (${currentApiKey.slice(0, 8)}...)` : "未設定");
  console.log("PINECONE_INDEX_HOST:", currentHost || "未設定");
  
  // 未設定の場合の設定例
  if (!currentApiKey || !currentHost) {
    console.log("\\n=== 設定方法 ===");
    console.log("以下のコードを実行して設定してください:");
    console.log(`
PropertiesService.getScriptProperties().setProperties({
  'PINECONE_API_KEY': 'your-pinecone-api-key-here',
  'PINECONE_INDEX_HOST': 'https://your-index-host.pinecone.io'
});
    `);
  }
  
  return { apiKey: currentApiKey, host: currentHost };
}

/**
 * PineconeからベクターIDを削除
 * @param {string[]} vectorIds - 削除するベクターIDの配列
 * @return {Object} 削除結果
 */
function deletePineconeVectors(vectorIds) {
  if (!vectorIds || vectorIds.length === 0) {
    return { success: true, deletedCount: 0, message: "削除対象なし" };
  }

  // Pinecone設定（PropertiesServiceから取得）
  const PINECONE_API_KEY = PropertiesService.getScriptProperties().getProperty('PINECONE_API_KEY');
  const PINECONE_INDEX_HOST = PropertiesService.getScriptProperties().getProperty('PINECONE_INDEX_HOST');
  
  if (!PINECONE_API_KEY || !PINECONE_INDEX_HOST) {
    Logger.log("⚠️ Pinecone設定が見つかりません。スクリプトプロパティを確認してください。");
    return { success: false, error: "Pinecone設定未構成" };
  }

  try {
    const deleteUrl = `${PINECONE_INDEX_HOST}/vectors/delete`;
    
    const payload = {
      ids: vectorIds,
      deleteAll: false
    };

    const options = {
      method: 'POST',
      headers: {
        'Api-Key': PINECONE_API_KEY,
        'Content-Type': 'application/json'
      },
      payload: JSON.stringify(payload)
    };

    Logger.log(`🗑️ Pineconeから${vectorIds.length}件のベクター削除を実行...`);
    Logger.log(`削除対象ID: ${vectorIds.join(', ')}`);

    const response = UrlFetchApp.fetch(deleteUrl, options);
    const responseCode = response.getResponseCode();
    
    if (responseCode === 200) {
      Logger.log(`✅ Pinecone削除成功: ${vectorIds.length}件`);
      return { 
        success: true, 
        deletedCount: vectorIds.length,
        message: `Pinecone削除完了: ${vectorIds.length}件`
      };
    } else {
      const errorText = response.getContentText();
      Logger.log(`❌ Pinecone削除エラー (${responseCode}): ${errorText}`);
      return { 
        success: false, 
        error: `HTTP ${responseCode}: ${errorText}`,
        deletedCount: 0
      };
    }
    
  } catch (error) {
    Logger.log(`❌ Pinecone削除例外: ${error.message}`);
    return { 
      success: false, 
      error: error.message,
      deletedCount: 0
    };
  }
}

/**
 * 重複除去（挿入前に呼び出す）+ Pinecone同期削除
 * @param {Object} data
 * @param {'yoin'|'anken'} type
 * @return {Object} 削除結果 {sheetDeletedCount, pineconeResult}
 */
function removeDuplicates(data, type) {
  const sheetName = SHEETS[type];
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  if (!sheet) return { sheetDeletedCount: 0, pineconeResult: { success: true, deletedCount: 0 } };

  const values = sheet.getDataRange().getValues();
  if (values.length < 2) return { sheetDeletedCount: 0, pineconeResult: { success: true, deletedCount: 0 } };

  const headers = values[0];
  const rows = values.slice(1);

  let deleteRows = [];
  let deletePineconeIds = []; // Pinecone削除対象のID

  rows.forEach((row, idx) => {
    const rowObj = {};
    headers.forEach((h, i) => rowObj[h] = normalizeValue(row[i]));

    let matched = false;

    if (type === "anken_struct") {
      matched =
        rowObj["案件名"] === normalizeValue(data["案件名"]) &&
        rowObj["必須スキル"] === normalizeValue(data["必須スキル"]) &&
        rowObj["作業場所"] === normalizeValue(data["作業場所"]) &&
        rowObj["勤務形態"] === normalizeValue(data["勤務形態"])
        // rowObj["時期"] === normalizeValue(data["時期"]) &&
        // rowObj["単価"] === normalizeValue(data["単価"])
        ;
    }

    if (type === "yoin_struct") {
      matched =
        rowObj["氏名"] === normalizeValue(data["氏名"]) &&
        rowObj["氏名"] === normalizeValue(data["氏名"]) &&
        ageMatches(rowObj["年齢"], data["年齢"]) &&
        // rowObj["スキル"] === normalizeValue(data["スキル"]) &&
        rowObj["最寄駅"] === normalizeValue(data["最寄駅"]);
    }

    if (matched) {
      deleteRows.push(idx + 2); // header + 1
      
      // Pinecone削除用にIDを収集（要員データのみ）
      if (type === "yoin_struct" && rowObj["ID"]) {
        deletePineconeIds.push(normalizeValue(rowObj["ID"]));
      }
      
      console.log(`重複が見つかりました: ${rowObj["件名"] || rowObj["氏名"] || "不明"} (ID: ${rowObj["ID"]})`);
    }
  });

  // シートから削除
  deleteRows.reverse().forEach(r => sheet.deleteRow(r));
  if(deleteRows.length > 0){
    console.log(`${deleteRows.length}行の重複をシートから削除しました`);
  }

  // Pineconeから削除（要員データのみ）
  let pineconeResult = { success: true, deletedCount: 0, message: "要員データ以外またはPineconeIDなし" };
  if (type === "yoin_struct" && deletePineconeIds.length > 0) {
    pineconeResult = deletePineconeVectors(deletePineconeIds);
  }

  return {
    sheetDeletedCount: deleteRows.length,
    pineconeResult: pineconeResult
  };
}

/**
 * 手動実行用：全行の重複を除去
 * @param {'yoin'|'anken'} type
 * 手動実行の場合は引数を渡せないのでtypeを記入する
 * @return {number} 削除行数
 */
/*
function removeAllDuplicates() {
  type = 'anken_struct'
  const sheetName = SHEETS[type];
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  if (!sheet) return 0;

  const values = sheet.getDataRange().getValues();
  if (values.length < 2) return 0;

  const headers = values[0];
  let totalDeleted = 0;

  // 下から処理（安全）
  for (let i = values.length - 1; i >= 1; i--) {
    const row = values[i];
    const data = {};
    headers.forEach((h, idx) => data[h] = row[idx]);

    const deleted = removeDuplicates(data, type);
    totalDeleted += deleted > 0 ? deleted - 1 : 0; 
    // 自分自身は除外
  }

  return totalDeleted;
}
*/

// =====================
// 正規化ユーティリティ
// =====================
function norm(v) {
  if (v === null || v === undefined) return "";
  if (v instanceof Date) return v.toISOString();

  return String(v)
    .replace(/\uFEFF/g, "")
    .replace(/\u3000/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function toAgeOrNull(v) {
  const s = norm(v);
  if (!s) return null;
  const n = Number(s.replace(/[^\d]/g, ""));
  return Number.isFinite(n) ? n : null;
}

function parseReceivedAt(v) {
  if (v instanceof Date) return v.getTime();
  const s = norm(v);
  if (!s) return null;
  const t = new Date(s).getTime();
  return Number.isFinite(t) ? t : null;
}

// =====================
// 要員：年齢±1で重複クラスタ作成
// =====================
function buildAgeClusters(items) {
  // items: [{rowNumber, receivedAt, age|null}]
  // ルール:
  // - age が null 同士は同一扱い（同一クラスタ）
  // - age が片方 null の場合は一致扱いにしない（誤削除防止）
  // - age が数値同士は |diff| <= 1 なら同一扱い（連結もOK：57-58,58-59 → 同一クラスタ）

  const aged = [];
  const nullAge = [];

  for (const it of items) {
    if (it.age === null) nullAge.push(it);
    else aged.push(it);
  }

  // age=null クラスタ（複数ある場合だけ削除対象が出る）
  const clusters = [];
  if (nullAge.length) clusters.push(nullAge);

  // ageありを age昇順で並べて「差<=1 で連結」クラスタ化
  aged.sort((a, b) => a.age - b.age || b.receivedAt - a.receivedAt || b.rowNumber - a.rowNumber);

  let current = [];
  for (let i = 0; i < aged.length; i++) {
    const it = aged[i];
    if (current.length === 0) {
      current.push(it);
      continue;
    }
    const prev = current[current.length - 1];

    // 連結条件：年齢差 <= 1
    if (Math.abs(it.age - prev.age) <= 1) {
      current.push(it);
    } else {
      clusters.push(current);
      current = [it];
    }
  }
  if (current.length) clusters.push(current);

  return clusters;
}

// =====================
// メイン：全重複除去（最新を残す）
// =====================
/**
 * type: 'yoin_struct' | 'anken_struct'
 * return: {sheetDeletedCount, pineconeDeletedCount}
 */
function removeAllDuplicates(type) {
  const sheetName = SHEETS[type];
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  if (!sheet) throw new Error(`sheet not found: ${sheetName}`);

  const values = sheet.getDataRange().getValues();
  if (values.length < 2) return { sheetDeletedCount: 0, pineconeDeletedCount: 0 };

  const headers = values[0].map(norm);
  const idx = (name) => headers.indexOf(name);

  const recvCol = idx("受信日時"); // なくても動く（行番号で代替）
  const idCol = idx("ID"); // Pinecone削除用

  // 列チェック
  if (type === "yoin_struct") {
    ["氏名", "年齢", "最寄駅"].forEach(c => {
      if (idx(c) < 0) throw new Error(`missing column: ${c}`);
    });
  }
  if (type === "anken_struct") {
    ["案件名","必須スキル","作業場所","勤務形態","単価"].forEach(c => {
      if (idx(c) < 0) throw new Error(`missing column: ${c}`);
    });
  }

  // 1) 大枠グルーピング（キー）
  const groups = new Map(); // key -> items[]

  for (let r = 1; r < values.length; r++) {
    const row = values[r];
    const rowNumber = r + 1;

    let key = "";
    if (type === "yoin_struct") {
      const name = norm(row[idx("氏名")]);
      const station = norm(row[idx("最寄駅")]);
      if (!name || !station) continue; // 事故防止
      key = `name=${name}__station=${station}`;
    } else {
      const name = norm(row[idx("案件名")]);
      const skill = norm(row[idx("必須スキル")]);
      const place = norm(row[idx("作業場所")]);
      const style = norm(row[idx("勤務形態")]);
      const price = norm(row[idx("単価")]);
      if (!name || !skill || !place) continue;
      key = `name=${name}__skill=${skill}__place=${place}__style=${style}__price=${price}`;
    }

    const receivedAt = (recvCol >= 0) ? (parseReceivedAt(row[recvCol]) ?? -1) : -1;

    const item = {
      rowNumber,
      receivedAt,
      age: (type === "yoin_struct") ? toAgeOrNull(row[idx("年齢")]) : null,
      id: (idCol >= 0) ? norm(row[idCol]) : null, // Pinecone削除用ID
    };

    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(item);
  }

  // 2) 削除対象決定（最新を残す）
  const toDelete = [];
  const pineconeIdsToDelete = []; // Pinecone削除対象ID

  for (const [key, items] of groups.entries()) {
    if (items.length <= 1) continue;

    if (type === "yoin_struct") {
      // 年齢±1でクラスタ分割
      const clusters = buildAgeClusters(items);

      for (const cl of clusters) {
        if (cl.length <= 1) continue;

        // 最新を残す（受信日時→行番号）
        cl.sort((a, b) => {
          if (b.receivedAt !== a.receivedAt) return b.receivedAt - a.receivedAt;
          return b.rowNumber - a.rowNumber;
        });

        const keep = cl[0].rowNumber;
        for (let i = 1; i < cl.length; i++) {
          toDelete.push(cl[i].rowNumber);
          
          // Pinecone削除対象IDを収集（要員データのみ）
          if (cl[i].id) {
            pineconeIdsToDelete.push(cl[i].id);
          }
        }

        console.log(`[DUP yoin] key=${key} ageCluster=${cl.map(x=>x.age).join(",")} keepRow=${keep} delete=${cl.slice(1).map(x=>x.rowNumber).join(",")}`);
      }

    } else {
      // 案件はキー完全一致グループで最新残し
      items.sort((a, b) => {
        if (b.receivedAt !== a.receivedAt) return b.receivedAt - a.receivedAt;
        return b.rowNumber - a.rowNumber;
      });

      const keep = items[0].rowNumber;
      for (let i = 1; i < items.length; i++) {
        toDelete.push(items[i].rowNumber);
      }

      console.log(`[DUP anken] key=${key} keepRow=${keep} delete=${items.slice(1).map(x=>x.rowNumber).join(",")}`);
    }
  }

  // 3) シートから削除
  toDelete.sort((a, b) => b - a);
  for (const r of toDelete) sheet.deleteRow(r);

  console.log(`Deleted ${toDelete.length} rows from sheet`);

  // 4) Pineconeから削除（要員データのみ）
  let pineconeDeletedCount = 0;
  if (type === "yoin_struct" && pineconeIdsToDelete.length > 0) {
    const pineconeResult = deletePineconeVectors(pineconeIdsToDelete);
    if (pineconeResult.success) {
      pineconeDeletedCount = pineconeResult.deletedCount;
      console.log(`Deleted ${pineconeDeletedCount} vectors from Pinecone`);
    } else {
      console.log(`Pinecone deletion failed: ${pineconeResult.error}`);
    }
  }

  return {
    sheetDeletedCount: toDelete.length,
    pineconeDeletedCount: pineconeDeletedCount
  };
}

// =====================
// 手動実行エントリ
// =====================
function removeAllDuplicates_yoin() {
  return removeAllDuplicates("yoin_struct");
}
function removeAllDuplicates_anken() {
  return removeAllDuplicates("anken_struct");
}


/*****************************************************
 * ✅ doPost - Difyから構造化データをシートに書き戻す
 *****************************************************/

function doPost(e) {
  try {
    if (!e || !e.postData) throw new Error("No postData received");

    const raw = e.postData.contents;
    const data = JSON.parse(raw);

    const record = data.record?.record || data.record || data || {};
    Logger.log(record);

    // 外部からの type (yoin / anken) を struct に正規化
    const baseType = data.type || record.type || "yoin";
    const type = (baseType === "anken") ? "anken_struct" : "yoin_struct";

    const sheetName = SHEETS[type];
    if (!sheetName) throw new Error(`Unknown type: ${type}`);
    
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) throw new Error(`シート「${sheetName}」が見つかりません`);

    // ----------------------------
    // ★ ここが肝：removeDuplicates 用にヘッダ名へ寄せる
    // ----------------------------
    const dupKey = (type === "yoin_struct")
      ? {
          "氏名": record.name || "",
          "年齢": record.age || "",
          "最寄駅": record.station || ""
          // "スキル": record.skill || ""  // 使うならここも追加
        }
      : {
          "案件名": record.name || "",
          "必須スキル": record.skill || "",
          "作業場所": record.station || "",      // ← あなたの列設計に合わせてる
          "勤務形態": record.work_style || ""
          // "時期": record.schedule || "",
          // "単価": record.price || ""
        };

    // ★ 挿入前に重複削除（古い方が消える）
    const deleteResult = removeDuplicates(dupKey, type);
    const logMessage = `事前重複削除: シート${deleteResult.sheetDeletedCount}行, Pinecone${deleteResult.pineconeResult.deletedCount}件`;
    Logger.log(logMessage);
    
    // 詳細ログ
    if (deleteResult.pineconeResult.message) {
      Logger.log(`Pinecone削除詳細: ${deleteResult.pineconeResult.message}`);
    }
    if (!deleteResult.pineconeResult.success) {
      Logger.log(`Pinecone削除エラー: ${deleteResult.pineconeResult.error}`);
    }
    
    // シートにログ記録
    const logSheet = ss.getSheetByName('logs');
    if (logSheet) {
      logSheet.appendRow([
        new Date(),
        logMessage,
        `Pinecone: ${deleteResult.pineconeResult.success ? '成功' : '失敗'}`,
        deleteResult.pineconeResult.error || '-'
      ]);
    }

    // ----------------------------
    // 挿入
    // ----------------------------
    if (type === "yoin_struct") {
      sheet.appendRow([
        record.id || "",
        record.date || "",
        record.name || "",
        record.age || "",
        record.skill || "",
        record.station || "",
        record.work_style || "",
        record.price || "",
        record.etc || "",
        record.subject || "",
        record.raw_input || ""
      ]);
    } else {
      sheet.appendRow([
        record.id || "",
        record.date || "",
        record.name || "",
        record.skill || "",
        record.station || "",
        record.work_style || "",
        record.schedule || "",
        record.price || "",
        record.etc || "",
        record.subject || "",
        record.raw_input || ""
      ]);
    }

    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      type,
      sheet: sheetName,
      deletedDuplicates: {
        sheet: deleteResult.sheetDeletedCount,
        pinecone: deleteResult.pineconeResult.deletedCount,
        pineconeSuccess: deleteResult.pineconeResult.success,
        pineconeError: deleteResult.pineconeResult.error || null
      },
      recordCount: sheet.getLastRow() - 1
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: err.message
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

// DEBUG
function debugFunc() {
  const sheetName = 'gmail要員情報'
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);

  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();
  if (lastRow < 2) {
    return { type: sheetName, count_total: 0, count_returned: 0, records: [] };
  }
  const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  const recvIdx = headers.indexOf("受信日時");

  console.log("idx=" + recvIdx);
}

function dumpHeadersDebug() {
  sheetName = '最新要員情報'
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];

  const show = (s) => {
    s = String(s);
    const codes = [...s].map(ch => ch.charCodeAt(0).toString(16).padStart(4, "0")).join(" ");
    return { raw: s, len: s.length, codes };
  };

  headers.forEach((h, i) => {
    console.log(`${i}:`, show(h));
  });

  console.log("indexOf('氏名') =", headers.map(h => String(h)).indexOf("氏名"));
}

function dumpCellDebug_yoin_AN() {
  const sheetName = "最新要員情報"; // ←あなたのシート名
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);

  const values = sheet.getDataRange().getValues();
  const headers = values[0];

  const idxName = headers.indexOf("氏名");
  const idxAge  = headers.indexOf("年齢");
  const idxSta  = headers.indexOf("最寄駅");

  const show = (s) => {
    s = String(s ?? "");
    const codes = [...s].map(ch => ch.charCodeAt(0).toString(16).padStart(4,"0")).join(" ");
    return { raw: s, len: s.length, codes };
  };

  for (let r = 1; r < values.length; r++) {
    const name = values[r][idxName];
    if (String(name).includes("A") && String(name).includes("N")) { // ゆるめに拾う
      console.log("row=", r+1,
        "氏名=", show(name),
        "年齢=", show(values[r][idxAge]),
        "最寄駅=", show(values[r][idxSta])
      );
    }
  }
}

/*****************************************************
 * Pinecone削除機能のテスト
 *****************************************************/

/**
 * Pinecone削除機能のテスト
 * 少数のテストデータで動作確認
 */
function testPineconeDelete() {
  console.log("=== Pinecone削除テスト開始 ===");
  
  // 設定確認
  const config = setupPineconeConfig();
  if (!config.apiKey || !config.host) {
    console.log("エラー: Pinecone設定が未完了です");
    return;
  }
  
  // テスト用のダミーIDで削除テスト
  const testIds = ["test-id-1", "test-id-2"];
  console.log("テスト削除ID:", testIds);
  
  try {
    const result = deletePineconeVectors(testIds);
    console.log("削除結果:", result);
    
    if (result.success) {
      console.log("✅ Pinecone削除テスト成功");
    } else {
      console.log("❌ Pinecone削除テスト失敗:", result.error);
    }
  } catch (error) {
    console.log("❌ テスト中にエラー:", error.message);
  }
  
  console.log("=== テスト終了 ===");
}

/**
 * 重複削除の統合テスト
 * Google SheetとPinecone両方の削除をテスト
 */
function testIntegratedDuplicateRemoval() {
  console.log("=== 統合重複削除テスト開始 ===");
  
  try {
    // 要員シートの重複削除をテスト
    const yoinResult = removeDuplicates(null, "要員");
    console.log("要員シート削除結果:", yoinResult);
    
    // 成果物シートの重複削除をテスト
    const seikabResult = removeDuplicates(null, "成果物");
    console.log("成果物シート削除結果:", seikabResult);
    
    console.log("✅ 統合テスト完了");
    
  } catch (error) {
    console.log("❌ 統合テスト中にエラー:", error.message);
  }
  
  console.log("=== 統合テスト終了 ===");
}