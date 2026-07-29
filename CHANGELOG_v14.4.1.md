# v14.4.1

- 修正登入頁語言選單空白。
- 三個語言選單加入靜態備援選項：繁體中文、English、ไทย。
- `index.html` 內嵌 i18n 與主程式備援，避免從 ZIP 直接預覽時外部 JavaScript 沒有被一起解壓造成初始化失敗。
- 保留 `config.js` 外部覆寫能力與 GitHub Pages / GitHub Actions 架構。
