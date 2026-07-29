# Emerald Enterprise HR + SOP v16.3.5

適合放入 GitHub Repository 的企業人資入口範本，整合請假、A/B 組星期六輪班、泰國假日、出勤紀錄、新人 SOP、三語介面與 RAG Chatbot。

> 重要：GitHub Pages 只能部署靜態前端。真實員工、出勤、請假、SOP 確認與稽核資料必須連接 FastAPI + MySQL 後端。


## v16.3.5 GitHub + MySQL + HTTPS full-stack deployment

This version is designed for a single Railway HTTPS service:

```text
Browser -> HTTPS Railway domain -> FastAPI -> private Railway MySQL
```

FastAPI also serves the `frontend/` directory, so the website and API share one
domain. GitHub stores the full source repository and Railway can automatically
redeploy after pushes.

See `部署到GitHub_Railway_MySQL_HTTPS.txt`.

## v16.0 企業版重點

- **新人 1／7／30 天快速路徑**：第一天、第一週、第三十天該完成的項目一目了然。
- **SOP 知識中心**：依角色顯示必讀 SOP、版本、狀態、測驗與閱讀確認。
- **防止假規章**：只有 `Published` 文件能被員工正式確認；`HR-DRAFT` 一律顯示待 HR 核准。
- **出勤紀錄**：員工看本人、主管看部門、HR／管理員可匯入與匯出。
- **缺卡修正流程**：申請時間、原因、審核狀態與稽核軌跡保留。
- **企業稽核事件**：記錄 SOP 確認、出勤匯入、修正申請與審核。
- **RAG Chatbot**：繁中、英文、泰文問答；可引用已發布 SOP，不得編造未發布內規。
- **請假與班表**：泰國假日每日更新、A/B 組星期六輪班、特殊補班／休假與實扣工作日計算。

完整導入順序請看：`docs/ENTERPRISE_SOP_QUICKSTART.md`。

## 快速試用

1. 解壓縮。
2. 打開 `frontend/index.html`。
3. 使用展示帳號：

```text
E001 / 1234   員工 A 組
E002 / 1234   員工 B 組
M001 / 1234   主管
HR001 / 1234  HR
A001 / 1234   管理員
```

4. 依序查看：

```text
新人專區 → SOP 知識中心 → 我的出勤 → 星期六輪班 → 請假申請 → 詢問 AI
```

## GitHub 上傳

建議使用 GitHub Desktop：

1. Clone 你的 Repository。
2. 將本專案資料夾「裡面的全部內容」複製到 Clone 資料夾。
3. `Commit to main` → `Push origin`。
4. GitHub：`Settings → Pages → Source → GitHub Actions`。
5. GitHub：`Settings → Actions → General → Workflow permissions → Read and write permissions`。
6. 到 Actions 手動執行 Pages、Thailand holiday update、RAG pipeline 與 CI。

不可把 `.github/`、`frontend/`、`backend/`、`rag/`、`scripts/` 攤平。

## 本機完整系統

```bash
docker compose up --build
```

開啟：

```text
網站：http://localhost:8080
API 文件：http://localhost:8080/api/docs
健康檢查：http://localhost:8080/api/health
```

## 主要企業 API

```text
GET  /api/sops
GET  /api/sops/progress
POST /api/sops/{id}/acknowledge

GET  /api/attendance
GET  /api/attendance/summary
POST /api/attendance/import
POST /api/attendance/{id}/corrections
GET  /api/attendance/corrections
POST /api/attendance/corrections/{id}/review

GET  /api/enterprise/audit
POST /api/rag/chat
```

出勤匯入範本：`data_templates/attendance_import_template.csv`。

## 正式 SOP 上線方式

目前安全、PPE、品質、保密、緊急事件與工作秩序內容是 **HR-DRAFT 範本**。正式使用前：

1. HR／EHS／QA／IT 提供核准文件。
2. 每份文件填寫擁有者、版本、生效日、適用廠區、部門與角色。
3. 放入 `rag/documents/`，重建 RAG 索引。
4. 將資料庫 SOP 狀態改為 `published`。
5. 用三種語言測試 Chatbot 回答與來源。
6. 要求員工完成測驗並確認新版本。

公開 Repository 不可上傳真實員工個資、醫療證明、薪資、打卡明細、內部機密或 API 金鑰。

## 正式上線前必做

- `frontend/config.js` 改成 `APP_MODE: "production"` 並設定 HTTPS 後端網址。
- 移除展示密碼與共享帳號。
- 使用 MySQL（8.0 以上）、強密碼、密鑰管理、HTTPS、備份與還原演練。
- 建立 Alembic migration，取代示範用 schema compatibility。
- 設定 CORS、登入失敗限制、Token 期限、日誌保存與最小權限。
- 先以單一部門試行，再逐步全公司部署。

## 驗證

```bash
node --check frontend/config.js
node --check frontend/i18n.js
node --check frontend/app.js
node scripts/check_frontend_i18n.js
python scripts/validate_holiday_json.py
python -m rag.build_index
python -m unittest discover -s rag/tests -v
cd backend && python -m pytest -q
```


## v16.1 泰國國定假日通知

登入後的通知中心會依每日同步的泰國國定假日資料，自動列出未來 30 天提醒，並在側邊選單顯示未讀數量。通知可逐則或全部標示已讀。GitHub Pages 只能提供站內通知；Email、LINE 或關閉網頁後的推播需要正式後端通知服務。

## v16.3 新人內容管理

- 使用 `HR001` 或 `A001` 登入後，可在「新人專區」管理必讀清單。
- 可在「SOP 知識中心」管理核心測驗題目、正確答案與及格分數。
- 支援新增、編輯、刪除與恢復預設內容。
- 題庫或及格分數變更後，舊的測驗通過狀態會失效，使用者需重新作答。
- GitHub Pages／純前端模式會將設定保存在目前瀏覽器的 `localStorage`；正式多人共用需將內容管理設定接到後端資料庫。



## v16.3.1 language-switch fix

- Fixed the dynamic sidebar, role label, active page title, and notification navigation after switching languages.
- Navigation buttons now carry `data-i18n` keys and preserve the currently open page.
- Language refreshes are isolated so one stale browser-data renderer cannot stop the rest of the UI from translating.
- `frontend/index.html` now loads `i18n.js` and `app.js` directly, eliminating the duplicated embedded code that could become inconsistent.
- A visible `v16.3.1` marker appears below the company name in the sidebar.

## v16.3 multilingual UI

- Traditional Chinese, English, and Thai now update together across the dashboard, sidebar, dynamic tables, notifications, attendance data sources, and management panels.
- HR/admin content editors require all three translations for each onboarding item and quiz question.
- The single-file `frontend/index.html` is synchronized with `i18n.js` and `app.js` for local demo use.
- Run `node scripts/check_full_i18n.js` to validate key coverage and untranslated UI attributes.


## SQL 工作規章 API

詳見 `docs/WORK_RULES_SQL_API.md`。本版本會把繁體中文工作規章自動寫入 SQLite `work_rules` 資料表，並提供查詢及搜尋 API。
