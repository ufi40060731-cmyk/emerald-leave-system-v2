# Emerald Enterprise HR + SOP Platform

企業人資與 SOP 一站式平台：請假、A/B 組星期六輪班、泰國國定假日、出勤紀錄、
新人 Onboarding、SOP 知識中心、工作規章知識庫、稽核紀錄，以及支援中／英／泰
三語的 RAG + LLM 詢問 AI（Chatbot）。前後端已整合成單一 Docker 服務，可直接
部署到 Railway（MySQL 8 為資料庫）。

---

## 🌐 目前的正式部署（Railway）

| 項目 | 網址 |
|---|---|
| 網站（前端＋API 同一網域） | https://emerald-app-production.up.railway.app |
| 規章管理後台 | https://emerald-app-production.up.railway.app/admin_rules.html |
| 員工管理後台 | https://emerald-app-production.up.railway.app/admin_users.html |
| API 文件（Swagger） | https://emerald-app-production.up.railway.app/api/docs |
| API 規格書（OpenAPI JSON） | https://emerald-app-production.up.railway.app/api/openapi.json |
| 健康檢查 | https://emerald-app-production.up.railway.app/api/health |
| GitHub 原始碼 | https://github.com/ufi40060731-cmyk/emerald-leave-system-v2 |
| Railway 專案 | https://railway.com/project/011961c0-af1d-42d9-a992-0681b590a219 |

**帳號**：`E001`、`E002`、`M001`、`HR001`、`A001`。密碼請洽 HR/Admin（demo 密碼
`1234` 已在正式環境輪換過，詳見下方「密碼與帳號安全」）。

> GitHub Pages 只能部署靜態前端。真實員工、出勤、請假、SOP 確認與稽核資料
> 必須連接 FastAPI + MySQL 後端（也就是現在這個 Railway 部署）。

---

## 系統架構

```text
瀏覽器
  │  HTTPS（單一網域）
  ▼
Railway：emerald-app（Docker，FastAPI 同時serve /frontend 靜態檔＋/api/*）
  │
  ▼
Railway：MySQL 8（私有網路連線，DATABASE_URL）
```

- `frontend/`：純 HTML + Vanilla JS（`app.js`、`i18n.js`），無建置流程，可直接
  雙擊 `index.html` 以純前端 demo 模式試用（資料存在瀏覽器 `localStorage`，
  不連真實資料庫）。
- `backend/app/main.py`：單檔 FastAPI 應用，SQLAlchemy ORM，DB-agnostic
  （MySQL / PostgreSQL / SQLite 皆可，靠 `DATABASE_URL` 切換）。
- `rag/`：規章／SOP 文件轉成向量索引，供 Chatbot 檢索用（見下方「詢問 AI」）。
- `railway.json` + 根目錄 `Dockerfile`：Railway 直接偵測建置，無需手動設定
  Build 指令。

---

## 功能清單

| 模組 | 說明 |
|---|---|
| 新人 Onboarding | 第 1／7／30 天檢查清單，HR 可自訂項目 |
| SOP 知識中心 | 版本控管、測驗、閱讀確認、僅 `published` 文件可被員工確認 |
| 工作規章知識庫 | 條文管理（新增/編輯/刪除/批次匯入整份文件）＋ Chatbot 即時查詢 |
| 出勤紀錄 | 員工看本人、主管看部門、HR/Admin 可匯入匯出、缺卡修正流程 |
| 請假申請 | 主管 → HR 雙層簽核、依 A/B 組班表與泰國假日自動計算工作天數 |
| A/B 組星期六輪班 | 排班規則、例外覆蓋、即將到來的班表預覽 |
| 泰國國定假日 | 每日自動同步＋年度展延，通知中心自動提醒未來 30 天假期 |
| 詢問 AI（RAG Chatbot） | 中／英／泰三語問答，可查詢工作規章與 SOP，選配真正 LLM 生成式回答 |
| 稽核紀錄 | 所有關鍵操作（規章異動、密碼重設、帳號停用…）留下可追溯紀錄 |
| 員工帳號管理 | 新增員工、修改密碼（自助／管理員代改）、**在職/離職狀態管理**、**員工照片**（HR 也可管理） |
| 多語系介面 | 繁體中文／英文／泰文完整覆蓋，含動態內容與稽核紀錄翻譯 |

---

## 管理後台使用說明

### 1. 規章管理後台（`admin_rules.html`）

登入角色：`hr` 或 `admin`（也可從主系統登入後、側邊欄「工作規章管理」按鈕
直接開啟新分頁）。

- **新增/編輯/刪除單筆規章**：填代碼、分類、標題、內容、排序即可，刪除為
  軟刪除（`active=false`），不會真的清除歷史資料。
- **批次匯入整份文件**：把整份規章文件的文字（例如從 PDF 複製、含「第 1
  條」「第 2 條」…的內容）貼上，按「解析預覽」自動依條號切成一筆一筆，
  確認無誤後「確認匯入全部」。代碼相同會自動改為更新，可重複匯入做版本
  更新。
- 所有異動**即時反映**在 Chatbot 查詢結果，不需要重新部署。

### 2. 員工管理後台（`admin_users.html`）

登入角色：`hr` 或 `admin`（兩者都能登入，但畫面顯示的功能不同）。

**`hr` 和 `admin` 都能用：**
- **員工照片**：清單最前面一欄，未上傳照片的員工會顯示姓名首字當預設圖示。
  點「更新照片」選一張圖片上傳，前端會自動用 `<canvas>` 縮圖壓縮（最大
  200×200px、JPEG 品質 0.7）後再上傳，避免原始大圖拖慢頁面或塞爆資料庫欄位。
  照片存成 base64 直接寫入 MySQL（`users.photo_data`），不是存在伺服器檔案
  系統，所以不會因為 Railway 重新部署而遺失。欄位型別是 `TEXT`（MySQL 限制
  約 64KB），後端也會擋超過 60,000 字元的內容，因此上傳大圖前務必先讓前端
  完成縮圖（正常使用不會碰到這個限制）。每次更新／移除照片都會寫進「稽核
  紀錄」（`user_photo_updated` / `user_photo_removed`）。

**只有 `admin` 才看得到、才能操作：**
- **新增員工帳號**（含初始密碼）：`hr` 登入時這張表單會整個隱藏起來。
- **重設密碼**：可指定新密碼或自動產生隨機密碼，只顯示一次。
- **在職／離職狀態切換**：停用帳號後立即無法登入（包含既有的登入 session
  下一次 API 呼叫也會被擋下），但完整保留該員工過去的出勤／請假／SOP 紀錄。
  無法停用自己的帳號，避免誤鎖。

（`hr` 角色如果直接呼叫這幾個 admin-only API，後端會回傳 403，不是只有前端
畫面隱藏而已，屬於伺服器端強制的權限控管。）

### 3. 一般使用者自助修改密碼

登入主系統 → 側邊欄「設定」→「修改密碼」，需輸入目前密碼＋新密碼（至少 8
碼）。

---

## 密碼與帳號安全

- 密碼一律使用 bcrypt 雜湊儲存，資料庫裡看不到明碼。
- 登入錯誤達 5 次會鎖定該帳號 5 分鐘（`LOGIN_LOCKOUT_MAX_ATTEMPTS` /
  `LOGIN_LOCKOUT_WINDOW_SECONDS` 可調整）。
- CORS 只允許白名單網域（自動包含目前的 Railway 網域）。
- **`ROTATE_DEFAULT_PASSWORDS=true`**：啟動時把仍是 demo 密碼 `1234` 的帳號
  換成隨機密碼，新密碼印在部署 log（只印一次）。自我保護：密碼一旦不是
  `1234` 就不會再動，可以永久保持開啟。
- **`FORCE_RESET_ALL_PASSWORDS=true`**：**無條件**重設「所有」帳號密碼並印
  在 log。不是自我保護型開關，**用完務必馬上改回 `false`**，否則之後每次
  部署都會再重設一次、覆蓋掉使用者自己改過的密碼。
- 部署 log 會保留一段時間，透過上述兩個機制印出的明碼密碼，之後仍看得到
  歷史紀錄。**正式使用建議所有帳號透過「自助修改密碼」再改一次**，讓真正
  在用的密碼不曾出現在任何 log 裡。

---

## 稽核紀錄（Audit Trail）事件類型參考

「稽核紀錄」頁面（前端稱 Audit log）目前會記錄以下事件，全部都有中／英／泰
三語翻譯，不會顯示未翻譯的原始英文代碼：

| 後端事件代碼 | 說明 |
|---|---|
| `work_rule_created` | 新增工作規章 |
| `work_rule_updated` | 更新工作規章 |
| `work_rule_deactivated` | 刪除（軟刪除）工作規章 |
| `sop_created` | 新增 SOP |
| `sop_updated` | 更新 SOP |
| `sop_acknowledged` | 員工確認已閱讀 SOP |
| `attendance_import` | 匯入出勤紀錄 |
| `attendance_correction_requested` | 員工提出缺卡修正申請 |
| `attendance_correction_approved` / `attendance_correction_rejected` | 主管/HR 審核缺卡修正 |
| `password_changed` | 使用者自行修改密碼 |
| `admin_password_reset` | 管理員代為重設密碼 |
| `user_activated` / `user_deactivated` | 員工帳號啟用／停用 |
| `user_photo_updated` / `user_photo_removed` | 員工照片更新／移除 |

每筆紀錄都會存操作者帳號、時間、以及一段自由文字說明（例如異動了哪些欄位）。
稽核紀錄目前沒有對外匯出功能，僅供系統內查看。

---

## 詢問 AI（RAG Chatbot）設定

Chatbot 回答問題時的判斷順序：

1. 行事曆／班表相關問題 → 直接查資料庫回答。
2. 工作規章相關問題 → **即時**查詢 MySQL `work_rules` 資料表（比對相關度），
   一定是最新資料。
3. 都不符合 → 交給 RAG 靜態知識庫（`rag/documents/*.md` 預先建好的索引，
   **啟動時載入一次、常駐記憶體**，改文件檔案需要重新部署才會生效）。
4. 如果有設定 LLM，會用真正的語言模型生成自然語句回答並支援跨語言翻譯；
   沒設定則直接顯示比對到的規章原文＋來源。

設定真正的 LLM（目前使用 OpenAI，任何相容 OpenAI Chat Completions API 格式
的服務都可以）：

```
CHATBOT_API_URL=https://api.openai.com/v1/chat/completions
CHATBOT_MODEL=gpt-4o-mini
CHATBOT_API_KEY=sk-...
```

⚠️ 記得去 OpenAI 帳號設定「Monthly budget / usage limit」，避免被大量使用
或誤用時產生超乎預期的費用。

---

## 環境變數完整參考

| 變數 | 必填 | 說明 |
|---|---|---|
| `DATABASE_URL` | 是 | 例如 `mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4`；本機測試預設 `sqlite:///./data/emerald.db` |
| `EMERALD_SECRET` | 是（正式環境） | JWT 簽章金鑰，務必換成高強度亂碼，不可留預設值 |
| `ACCESS_TOKEN_MINUTES` | 否 | 登入 token 有效分鐘數，預設 60 |
| `CORS_ORIGINS` | 否 | 允許的前端網域（逗號分隔），Railway 網域會自動加入 |
| `LOGIN_LOCKOUT_MAX_ATTEMPTS` | 否 | 預設 5 |
| `LOGIN_LOCKOUT_WINDOW_SECONDS` | 否 | 預設 300 |
| `ROTATE_DEFAULT_PASSWORDS` | 否 | `true` 時，啟動把仍為 `1234` 的帳號換成隨機密碼（自我保護，建議常駐開啟） |
| `FORCE_RESET_ALL_PASSWORDS` | 否 | `true` 時，無條件重設「所有」帳號密碼（**用後即關**，非自我保護） |
| `HOLIDAY_SYNC_KEY` | 是（若用假日同步 API） | 呼叫 `/api/holidays/sync/{year}` 等端點需要的密鑰 |
| `HOLIDAY_AUTO_SYNC_ENABLED` | 否 | 預設 `true`，每日自動同步泰國假日 |
| `CHATBOT_API_URL` / `CHATBOT_MODEL` / `CHATBOT_API_KEY` | 否 | 設定後 Chatbot 才會用真正 LLM 生成回答（見上一節） |

---

## 本機開發

**方式一：純前端 demo（不需要任何安裝）**

直接雙擊打開 `frontend/index.html`，資料存在瀏覽器本機，適合單純看 UI、
不需要真實資料庫時使用。

**方式二：完整系統（Docker，含 MySQL）**

```bash
docker compose up --build
```

```text
網站：http://localhost:8080
API 文件：http://localhost:8080/api/docs
健康檢查：http://localhost:8080/api/health
```

---

## 部署到 Railway（目前正式環境用的方式）

1. Railway 建立專案 → `Deploy from GitHub repo` → 選這個 repo
2. `+ New → Database → Add MySQL`
3. 後端服務 `Variables → Raw Editor` 貼上：
   ```
   DATABASE_URL=${{MySQL.MYSQL_URL}}
   EMERALD_SECRET=<自己產生一組長亂碼>
   HOLIDAY_SYNC_KEY=<另一組長亂碼>
   ACCESS_TOKEN_MINUTES=60
   ```
   （`MYSQL_URL` 預設是 `mysql://` 開頭，程式碼會自動改寫成
   `mysql+pymysql://`，不用手動處理）
4. `Settings → Networking → Generate Domain` 取得公開網址
5. 之後只要 `git push` 到 `main`，Railway 會自動重新建置部署（`railway.json`
   已經設定好用根目錄 `Dockerfile` 建置、監聽 Railway 指派的 `$PORT`）

---

## 免費替代方案（如果不想付費用 Railway）

若 Railway 試用額度用完又還沒有預算，可以考慮完全免費的組合：

- **資料庫**：[Aiven](https://aiven.io/free-mysql-database) 有永久免費的
  MySQL 方案（1GB 儲存空間），適合小規模使用。
- **應用程式**：[Render](https://render.com) 免費 Web Service 方案，缺點是
  太久沒人用會自動休眠，下次打開網站第一次載入會慢 30–60 秒。
- 兩者搭配設定方式與 Railway 大致相同，只是 `DATABASE_URL` 換成 Aiven 給的
  連線字串（一樣需要加上 `mysql+pymysql://` 前綴）。

---

## API 端點總覽

```text
認證
POST /api/auth/login
POST /api/auth/token
GET  /api/me
POST /api/me/change-password

員工管理（admin）
GET   /api/admin/users
POST  /api/admin/users
POST  /api/admin/users/{user_id}/reset-password
PATCH /api/admin/users/{user_id}/status
PATCH /api/admin/users/{user_id}/photo
PUT   /api/users/{user_id}/rotation-group

工作規章
GET    /api/work-rules
GET    /api/work-rules/search
GET    /api/work-rules/{rule_code}
POST   /api/admin/work-rules
PUT    /api/admin/work-rules/{rule_code}
DELETE /api/admin/work-rules/{rule_code}
POST   /api/admin/work-rules/reseed

SOP
GET  /api/sops
GET  /api/sops/progress
POST /api/sops/{sop_id}/acknowledge
POST /api/admin/sops
PUT  /api/admin/sops/{sop_id}

出勤與缺卡修正
GET  /api/attendance
GET  /api/attendance/summary
POST /api/attendance/import
POST /api/attendance/{attendance_id}/corrections
GET  /api/attendance/corrections
POST /api/attendance/corrections/{correction_id}/review

請假
GET  /api/leaves
POST /api/leaves
GET  /api/leaves/calculate
POST /api/leaves/{leave_id}/manager-approve
POST /api/leaves/{leave_id}/hr-approve
POST /api/leaves/{leave_id}/reject

排班／星期六輪班
GET /api/schedules/me
GET /api/schedules/upcoming-saturdays
GET /api/schedules/settings
GET /api/schedules/overrides
POST/DELETE /api/schedules/overrides/{override_id}

泰國假日
GET  /api/holidays
POST /api/holidays/sync/{year}
GET  /api/holidays/sync-status
POST /api/holidays/auto-sync
POST /api/holidays/annual-rollover
POST /api/holidays/initialize/{year}
POST /api/holidays/{holiday_id}/confirm

稽核與 Chatbot
GET  /api/enterprise/audit
POST /api/rag/chat
GET  /api/rag/search

系統
GET /api/health
GET /api/docs
GET /api/openapi.json
```

出勤匯入範本：`data_templates/attendance_import_template.csv`

---

## 正式上線前檢查清單

- [ ] `frontend/config.js` 設定為 `APP_MODE: "production"` 並填入正確後端網址
- [ ] 所有 demo 密碼已改成個人專屬密碼，不再是 `1234`
- [ ] `EMERALD_SECRET`、`HOLIDAY_SYNC_KEY` 都是高強度亂碼，不是預設值
- [ ] `FORCE_RESET_ALL_PASSWORDS` 確認是 `false`（用完即關）
- [ ] MySQL 已設定自動備份
- [ ] OpenAI（或其他 LLM）已設定用量上限
- [ ] 已刪除專案中沒用到的多餘服務
- [ ] CORS、登入鎖定次數、Token 期限依實際需求調整
- [ ] 先以單一部門試行，確認無誤再全公司推廣

---

## 驗證與測試

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

---

## 目錄結構

```text
backend/app/main.py     FastAPI 主程式（所有 API、資料模型、業務邏輯）
backend/app/rag_service.py   RAG 靜態知識庫檢索與 LLM 呼叫
frontend/index.html     主系統（單頁應用）
frontend/admin_rules.html    規章管理後台
frontend/admin_users.html    員工管理後台
frontend/app.js / i18n.js    前端邏輯與三語翻譯
rag/documents/           規章／SOP 原始文件（Markdown）
rag/storage/index.json   建好的向量索引（啟動時載入、常駐記憶體）
database/                MySQL 參考 SQL（供手動查看，非必要執行）
docs/                    詳細功能文件（SOP 上線、RAG 設定等）
railway.json             Railway 建置設定
Dockerfile               單一服務同時包含前端＋後端
docker-compose.yml       本機完整系統（含 MySQL）
```

---

## 授權與資料安全提醒

公開 Repository 不可上傳真實員工個資、醫療證明、薪資、打卡明細、內部機密
文件或任何 API 金鑰／密碼。`.gitignore` 已排除 `.env`、`backend/data/`
等本機檔案，但仍請上傳前自行再次確認。
