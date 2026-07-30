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
| SOP 管理後台 | https://emerald-app-production.up.railway.app/admin_sops.html |
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
| 出勤紀錄 | 員工看本人、主管看部門、缺卡修正申請＋**審核清單**（主管/HR/Admin，主管限自己部門） |
| 請假申請 | 主管 → HR 雙層簽核（主管只能核准/退回自己部門的請求，跟出勤查看範圍一致）、依 A/B 組班表與泰國假日自動計算工作天數 |
| A/B 組星期六輪班 | 排班規則、例外覆蓋、即將到來的班表預覽 |
| 泰國國定假日 | 每日自動同步＋年度展延，通知中心自動提醒未來 30 天假期 |
| 詢問 AI（RAG Chatbot） | 中／英／泰三語問答，可查詢工作規章與 SOP，選配真正 LLM 生成式回答 |
| 稽核紀錄 | 所有關鍵操作（規章異動、密碼重設、帳號停用…）留下可追溯紀錄 |
| 員工帳號管理 | 新增員工、修改密碼（自助／管理員代改）、**在職/離職狀態管理**、**員工照片**（HR 也可管理） |
| 多語系介面 | 繁體中文／英文／泰文完整覆蓋，含動態內容與稽核紀錄翻譯 |

> ⚠️ **重要歷史修正記錄**：主系統「請假申請」列表原本的核准／退回按鈕，
> 過去只會修改瀏覽器 `localStorage` 裡的假資料，**從未真正呼叫後端簽核
> API**（`manager-approve` / `hr-approve` / `reject`），也從未從後端重新
> 讀取真實的請假清單——每個瀏覽器看到的名單彼此獨立、互不同步。這個問題
> 已經修好：進入系統後會自動從 `GET /api/leaves` 載入真實清單，核准／退回
> 會真正呼叫對應的後端 API 並即時反映結果。「Excel 管理」頁的員工匯入按鈕
> 與「月報表匯出」的統計數字，過去也是完全沒有作用的假按鈕／寫死的假數字
> （86 名員工、94% 核准率等），現在也都已經改成真正會動、依實際資料計算。
> 順便統一了權限範圍：主管現在只能看到／核准／退回**自己部門**的請假申請，
> 跟出勤紀錄的查看範圍一致（之前後端沒有這層限制，任何主管理論上能核准
> 任一員工，只是因為按鈕從未真正連接後端而從未被觸發過）。
>
> 同一輪檢查也順便補上：員工管理後台的「輪班」欄位改成可以直接下拉選單
> 修改並即時儲存（原本建立帳號後就沒有地方能改輪班組），以及**缺卡修正
> 審核清單**（出勤頁面新增，主管/HR/Admin 可見，主管限自己部門）——這個
> 之前也是只有「員工可以申請」，完全沒有「審核」的畫面，申請永遠卡在
> 待審核狀態。
>
> 這兩個之前列在「已知還沒補上的功能」的項目，這次也一併補上了：
> **SOP 建立/編輯管理後台**（新的 `admin_sops.html`，用法跟規章、員工管理
> 後台一致）跟**出勤紀錄 Excel 匯入**（「Excel 管理」頁新增「匯入類型」
> 切換，可以選「員工名單」或「出勤紀錄」，各自對應真正的後端 API）。

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
- 清單上方有**搜尋框**，可即時依代碼／標題／分類／內容關鍵字過濾（純前端
  過濾已載入的清單，規章數量成長後找特定條文會方便很多）。

### 2. 員工管理後台（`admin_users.html`）

登入角色：`hr` 或 `admin`。權限設計原則：**HR 可以完整管理一般員工（employee／
manager），但不能動 `hr` 或 `admin` 角色的帳號；涉及其他 hr／admin 帳號一律
只有 `admin` 能操作**，避免權限互相牴觸或被拿來自我提升權限。清單上方同樣
有搜尋框，可依員工編號／姓名／部門即時過濾。

**`hr` 和 `admin` 都能做（僅限對象是 employee／manager）：**
- **新增員工帳號**（含初始密碼）。`hr` 登入時，角色下拉選單會**隱藏** `hr`
  和 `admin` 選項，只能新增 employee／manager；就算繞過前端直接打 API，
  後端也會回傳 403 擋下來。
- **重設密碼**：可指定新密碼或自動產生隨機密碼，只顯示一次。若目標帳號是
  `hr` 或 `admin` 角色，後端會回傳 403。
- **在職／離職狀態切換**：停用帳號後立即無法登入（包含既有的登入 session
  下一次 API 呼叫也會被擋下，重新整理頁面也會被立即登出），但完整保留該
  員工過去的出勤／請假／SOP 紀錄。無法停用自己的帳號，避免誤鎖；若目標帳號
  是 `hr` 或 `admin` 角色，後端一樣會回傳 403。離職員工若之後回來工作，建議
  直接**新增一個新帳號**，不需要重新啟用舊帳號。
- **員工照片**：清單最前面一欄，未上傳照片的員工會顯示姓名首字當預設圖示。
  點「更新照片」選一張圖片上傳，前端會自動用 `<canvas>` 縮圖壓縮（最大
  200×200px、JPEG 品質 0.7）後再上傳，避免原始大圖拖慢頁面或塞爆資料庫欄位。
  照片存成 base64 直接寫入 MySQL（`users.photo_data`），不是存在伺服器檔案
  系統，所以不會因為 Railway 重新部署而遺失。欄位型別是 `TEXT`（MySQL 限制
  約 64KB），後端也會擋超過 60,000 字元的內容，因此上傳大圖前務必先讓前端
  完成縮圖（正常使用不會碰到這個限制）。每次更新／移除照片都會寫進「稽核
  紀錄」（`user_photo_updated` / `user_photo_removed`）。上傳照片後，該員工
  下次登入主系統時，側邊欄個人資訊卡也會顯示自己的照片。
- **重新整理頁面會即時刷新使用者資料**：主系統偵測到已登入的 session 時，
  會重新呼叫 `/api/me` 取得最新的姓名／角色／部門／照片／在職狀態，而不是
  沿用瀏覽器裡的舊快取；如果帳號已被停用，重新整理頁面也會立刻被登出。

**只有 `admin` 才能操作 `hr`／`admin` 角色的帳號**（新增、重設密碼、停用／
啟用皆同）。這些權限判斷都寫在後端 API 裡，不是只有前端畫面隱藏而已，就算
用 API 文件（`/api/docs`）直接呼叫也一樣會被擋下。

### 3. 一般使用者自助修改密碼

登入主系統 → 側邊欄「設定」→「修改密碼」，需輸入目前密碼＋新密碼（至少 8
碼）。

### 4. Excel 批次匯入（主系統「Excel 管理」頁，`hr` / `admin` 可見）

⚠️ 這個功能原本是專案範本裡的**假展示按鈕**（按下去不會真的做任何事），
目前已經改成真正會動的批次匯入，並支援兩種「匯入類型」：

**員工名單**
1. 按「下載範本」拿到欄位正確的 CSV 檔（員工編號、姓名、角色、部門、輪班、
   初始密碼）。初始密碼欄位留空，系統會自動產生一組隨機密碼。
2. 依範本格式填好員工名單，存成 CSV 或 XLSX（用 Excel 另存新檔即可，兩種
   格式都支援；XLSX 解析用前端 [SheetJS](https://cdnjs.cloudflare.com/ajax/libs/xlsx/)
   函式庫，透過 CDN 載入）。
3. 選擇檔案 →「解析預覽」，會列出解析出來的欄位讓你確認（角色只接受
   employee/manager/hr/admin，輪班只接受 A/B/NONE，格式不符會自動改成
   預設值 employee／NONE，不會讓匯入失敗）。
4. 確認無誤後按「確認匯入」，會逐筆呼叫新增員工 API：
   - 代碼已存在 → 略過（不會覆蓋既有帳號）
   - 新增成功 → 計入「新增」，若密碼是自動產生的，會在匯入完成後**跳出視窗
     顯示一次**，記得馬上分發給對應員工
   - HR 上傳的名單裡如果有 `hr`／`admin` 角色 → 後端會擋下來，計入「失敗」
     （跟員工管理後台一樣的權限限制，HR 不能批次新增高權限帳號）

**出勤紀錄（打卡資料）**
1. 「匯入類型」切換成「出勤紀錄」，按「下載範本」拿到欄位正確的 CSV
   （員工編號、日期、預計上下班時間、實際打卡時間、狀態、來源、備註）。
2. 依範本格式填好資料 → 選擇檔案 →「解析預覽」確認。
3. 確認無誤後按「確認匯入」，會**一次性**把整批紀錄送到後端（跟員工匯入
   逐筆呼叫不同，出勤匯入本來就是設計成批次寫入的 API）。
   同一位員工同一天若已有紀錄，會直接覆蓋更新，不會重複。

### 5. SOP 管理後台（`admin_sops.html`，`hr` / `admin` 可見，也可從主系統側邊欄「SOP 管理」開啟）

- 新增/編輯 SOP：代碼、分類、版本、適用範圍（角色或部門，`all` 代表全公司）、
  狀態（`draft` 草稿或 `published` 已發布）、是否必讀、排序、以及**中/英/泰
  三語標題與摘要**。
- 只有 `published` 狀態的 SOP，員工才會在「SOP 知識中心」看到、才能確認
  閱讀；新建立的 SOP 預設是 `draft`，故意設計成這樣避免內容還沒寫完就被
  員工看到。
- 清單上的「發布」/「改回草稿」按鈕可以快速切換狀態，不用整份重新編輯。
- 刪除是**永久刪除**（不像工作規章是軟刪除），但刪除當下會把完整內容
  備份進稽核紀錄的 detail 欄位，需要復原可以請工程師手動從稽核紀錄還原。
- HR/Admin 登入這個頁面時，看得到系統裡**所有** SOP（包含依角色/部門限定
  可見範圍的），不受一般員工瀏覽時的權限篩選影響，方便管理。

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

**內建的用量保護（不需另外設定，預設就有開啟）**：每個使用者每小時最多問
`CHATBOT_RATE_LIMIT_PER_HOUR`（預設 30）次問題，超過會回傳 429，前端會顯示
「這一小時問太多次了」的提示，而不是誤導成系統故障。這是為了避免程式錯誤、
無限迴圈或惡意濫用把 LLM 費用燒爆，屬於應用層面的第二道保護（跟 OpenAI 帳號
本身的用量上限互相搭配）。

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
| `CHATBOT_RATE_LIMIT_PER_HOUR` | 否 | 預設 30，每位使用者每小時最多問幾次「詢問 AI」，超過回傳 429 |

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
GET    /api/sops
GET    /api/sops/progress
POST   /api/sops/{sop_id}/acknowledge
POST   /api/admin/sops
PUT    /api/admin/sops/{sop_id}
DELETE /api/admin/sops/{sop_id}

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
frontend/admin_sops.html     SOP 管理後台
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
