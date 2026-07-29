# v14.4 變更摘要

- 前端整理為 `index.html`、`config.js`、`i18n.js`、`app.js`，方便 GitHub 維護。
- 語言精簡為繁體中文、英文、泰文三種完整翻譯。
- 修正未翻譯的假別、日期、姓名、部門、時間、使用者、錯誤訊息及稽核動作。
- 假別改用固定代碼保存，切換語言不會改變資料內容。
- 泰國假日 JSON 新增 `names.zh-TW`、`names.en`、`names.th`。
- 每日 GitHub Action 產生 JSON 時同步建立三語假日名稱。
- 補假與「僅曼谷」標記會分別翻譯成三種語言。
- GitHub Pages 以相對路徑載入所有資源，支援專案子路徑。
- 假日 JSON 使用 `no-store` 與版本參數，降低瀏覽器顯示舊日期的情況。
- 新增 `frontend/config.js`，可在展示模式與正式後端模式之間切換。
- 正式模式不允許後端失敗時使用示範帳號。
- 新增前端翻譯完整性檢查與假日 JSON 驗證。
- GitHub CI 新增 JavaScript 語法、三語鍵值及 JSON 結構檢查。
