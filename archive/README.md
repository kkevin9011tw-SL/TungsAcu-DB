# archive/

舊版 SQLite 後端，**已退役**。app.py 自 2026-05-12 起改吃 `data/` 下的 CSV + MD + JPG。

保留這些檔案的原因：
- 歷史快照（含 4/19–5/9 期間累積的編輯）
- 萬一 CSV 路徑出問題可回查比對
- `migrate_to_csv.py` 之後若要重跑可從這裡讀

如果想完整重產 `data/`，把 `archive/*.db` 暫時移回上層目錄，跑 `python migrate_to_csv.py` 即可。

正式編輯入口已改為直接修改 `data/*.csv`（用 Excel/Numbers）或 admin tab 改 CSV。
