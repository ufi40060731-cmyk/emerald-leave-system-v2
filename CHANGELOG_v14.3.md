# v14.3 變更摘要

- GitHub Actions 改為直接產生並提交 GitHub Pages 可讀取的年度假日 JSON。
- 不再要求 GitHub Actions 連線至公開 FastAPI 網址，也不需要同步 Secret。
- 前端新增靜態 JSON 載入：API → GitHub JSON → 快取 → 內建備援。
- JSON 有實際差異才 commit，並由同一工作流程直接重新部署 Pages，避免 `GITHUB_TOKEN` 推送不觸發後續 Pages build 的限制。
- 泰國固定國定假日名稱加入繁體中文標準化。
- 移除來源名稱中的英文補充括號，保留必要的「補假」標記。
- `HR review` 在繁體中文介面改為「待 HR 確認」。
- 新增 GitHub Pages 自動更新狀態文字與資料版本時間。

## GitHub 使用

1. 推送至 `main`。
2. Pages 選擇 GitHub Actions。
3. Actions workflow permissions 允許 Read and write。
4. 手動執行一次 `Daily Thailand holiday update`。
