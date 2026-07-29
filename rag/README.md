# Emerald RAG Data Pipeline

這個資料夾提供可在本機或 GitHub Actions 執行的 RAG 文件索引流程。預設使用本機雜湊向量，不會把公司文件傳送給外部 AI 服務。

## 支援文件

- 直接支援：Markdown、TXT、JSON、CSV
- 安裝 `rag/requirements.txt` 後：PDF、DOCX

## 建立索引

在專案根目錄執行：

```bash
python -m rag.build_index
```

輸出：

```text
rag/storage/index.json
```

## 測試搜尋

```bash
python -m rag.cli "病假需要醫療證明嗎？"
```

## GitHub 自動管線

`.github/workflows/rag-pipeline.yml` 會在 `rag/documents/` 或 RAG 程式變更時：

1. 安裝文件讀取套件。
2. 重新切分文件並建立向量索引。
3. 執行管線測試。
4. 索引有變更時自動 commit 回 `main`。
5. 上傳索引為 Actions artifact。

## 資安提醒

公開 Repository 不可放入員工個資、醫療資料、內部機密或尚未公開的公司規章。私密文件應放在私人 Repository 或受控的物件儲存服務。`rag/documents/private/` 已加入 `.gitignore`。

## 目前限制

這是「文件擷取、切塊、向量化、索引、檢索」的可運行基礎版。預設回答是擷取式摘要，沒有呼叫外部大型語言模型。正式生成式回答可在後端加入受控的模型供應商，但密鑰只能放在伺服器環境變數或 GitHub Secrets。
