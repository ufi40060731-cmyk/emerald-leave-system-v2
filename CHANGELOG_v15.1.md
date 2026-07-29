# v15.1 — RAG Chatbot

- 將 AI 助理改為真正的對話式聊天介面。
- 支援對話歷史、Enter 送出、Shift+Enter 換行、清除對話及常見問題按鈕。
- 回答會顯示 RAG 文件來源。
- 新增 `POST /api/rag/chat`，支援多輪上下文。
- 可選擇連接 OpenAI-compatible chat completions 服務；未設定時仍可用本機 RAG 摘要回答。
- GitHub Pages 展示模式提供不需後端的聊天示範。
- API 金鑰只放後端環境變數，不會出現在公開 GitHub Pages。
