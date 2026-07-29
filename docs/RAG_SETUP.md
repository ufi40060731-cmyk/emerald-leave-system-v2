# RAG 文件管線設定

## 放入文件

把已經核准、可以交給系統查詢的文件放入：

```text
rag/documents/
```

支援 `.md`、`.txt`、`.json`、`.csv`、`.pdf`、`.docx`。

公開 GitHub Repository 請只使用公開或示範資料。機密文件不要上傳。

## 本機重建

```bash
python -m pip install -r rag/requirements.txt
python -m rag.build_index
python -m rag.cli "特休如何申請？"
```

## GitHub 自動重建

上傳到 `main` 後，進入：

```text
Actions → Build RAG knowledge index → Run workflow
```

之後只要 `rag/documents/` 有變更，工作流程會自動建立新索引並提交 `rag/storage/index.json`。

## 後端 API

完整 Docker 模式啟動後可使用：

```text
POST /api/rag/search
Authorization: Bearer <登入 token>
Content-Type: application/json

{"question":"病假需要醫療證明嗎？","top_k":3}
```

GitHub Pages 本身只能執行靜態前端，不能執行 RAG Python API；正式 AI 助理仍需部署 FastAPI 後端。


## 啟用對話生成

`/api/rag/chat` 預設使用本機 RAG 摘要模式，不需要 API 金鑰。若要更自然的多輪回答，請在後端部署平台設定：

```env
CHATBOT_API_URL=https://your-provider.example/v1/chat/completions
CHATBOT_API_KEY=your-secret
CHATBOT_MODEL=your-model-name
```

此端點必須採用 OpenAI-compatible chat-completions JSON 格式。不要把金鑰寫入 GitHub Pages 的 JavaScript。
