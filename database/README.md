# Database

預設 Docker Compose 使用 MySQL 8.4。資料表由 SQLAlchemy 在 API 啟動時建立。

`work_rules_schema.sql`／`work_rules_seed.sql` 是給想直接用 MySQL 客戶端（例如 `mysql` CLI 或 phpMyAdmin）手動建表、匯入工作規章條文時參考用的純 SQL；一般啟動流程不需要手動執行，SQLAlchemy 會自動處理。

正式導入前請加入：
- Alembic migration
- 加密備份與還原演練
- 最小權限資料庫帳號
- 正式、測試與開發環境隔離


## v15.2 輪休資料表

- `users.rotation_group`：`A`、`B` 或 `NONE`
- `rotation_schedules`：基準星期六、基準上班組別、是否啟用星期六輪休
- `calendar_overrides`：特殊補班日或特殊休假日，可套用全部或指定組別
- `leave_requests.workdays`：依假日、星期日與輪休規則算出的實際扣假天數

目前專案含簡易相容欄位更新；正式環境應改用 Alembic migration。
