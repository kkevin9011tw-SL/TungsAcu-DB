# TCM 論文追蹤流水線 設計文件

**日期**：2026-04-01
**專案**：tcm-rag（延伸）
**範圍**：每日自動抓取最新中醫相關論文、推薦、建檔、寫入 Notion

---

## 一、目標

建立一條全自動的論文追蹤流水線，每天定時執行，完成以下工作：

1. 從 PubMed 與頂尖期刊 RSS 抓取最新論文
2. 依使用者靜態關鍵字 + 本月主題，用 Claude API 推薦 Top 2-3 篇
3. 將每日論文快報寫入 Notion
4. 自動在 Zotero 建立條目
5. （選用，預留鉤子）對 open access 論文執行全文流水線：PDF → MD → 翻譯 → 筆記

---

## 二、專案結構

```
tcm-rag/
├── rag.py                        # 現有（不動）
├── paper_pipeline/
│   ├── fetch.py                  # 抓 PubMed / RSS
│   ├── recommend.py              # Claude API 評分推薦
│   ├── zotero.py                 # Zotero API 建檔
│   ├── notion.py                 # Notion API 寫入
│   ├── fulltext.py               # 全文流水線（預留，預設停用）
│   └── run.py                    # 主入口，launchd 呼叫
├── config/
│   ├── keywords.yaml             # 靜態興趣關鍵字（使用者維護）
│   └── topics.yaml               # 本月重點主題（使用者每月更新）
├── logs/
│   └── pipeline.log
├── papers.db                     # SQLite，追蹤處理狀態
├── .env                          # API keys（不進 git）
└── docs/superpowers/specs/
    └── 2026-04-01-tcm-paper-pipeline-design.md
```

---

## 三、資料流

```
launchd（每天 07:00）
    └── run.py
          ├── fetch.py
          │     ├── PubMed E-utilities API → 中醫期刊新論文
          │     └── RSS → NEJM / Nature / Science / Lancet（關鍵字初篩）
          ├── recommend.py
          │     ├── 讀 config/keywords.yaml
          │     ├── 讀 config/topics.yaml
          │     └── Claude API 評分 → Top 2-3 篇 + 推薦理由
          ├── notion.py
          │     └── 寫入 Notion「每日論文快報」子頁面
          ├── zotero.py
          │     └── 建立 Zotero 條目（作者、標題、期刊、DOI、摘要）
          └── [fulltext.py，ENABLE_FULLTEXT=true 時啟用]
                ├── Unpaywall API → 確認 open access
                ├── 下載 PDF
                ├── 轉 Markdown + 存圖
                ├── Claude API 翻譯
                └── Claude API 寫結構化筆記 → Notion
```

---

## 四、論文來源

| 來源 | 方式 | 說明 |
|------|------|------|
| PubMed | E-utilities API（免費） | 搜尋 JTCM、ECAM 等 TCM 專門期刊 |
| NEJM | RSS feed | 關鍵字過濾 TCM 相關 |
| Nature | RSS feed | 同上 |
| Science | RSS feed | 同上 |
| Lancet | RSS feed | 同上 |
| 全文 | Unpaywall API（免費，需 email） | 查 DOI open access 連結 |

---

## 五、推薦邏輯

- **`keywords.yaml`**：長期靜態興趣詞（如：針灸、腸道菌、方劑藥理、RCT）
- **`topics.yaml`**：本月動態重點（如：癌症輔助治療、睡眠障礙），每月手動更新一次
- Claude API 收到論文列表後，依兩份 config 評分，輸出：
  - Top 2-3 篇標題 + 推薦理由（一句話）
  - 每篇摘要導讀（3-5 句）

---

## 六、Notion 輸出格式

- 每天一個子頁面：`YYYY-MM-DD 論文快報`
- 結構：
  ```
  ## 今日推薦
  1. [標題](DOI 連結) — 期刊名
     推薦理由：...
     摘要導讀：...

  ## 其他本日論文
  - [標題](DOI 連結) — 期刊名
  ```
- 若全文流水線啟用，翻譯稿與筆記附加於同一頁下方

---

## 七、Zotero 整合

- 使用 Zotero Web API（需申請 API key）
- 每篇論文建立條目：作者、標題、期刊、年份、DOI、摘要
- 標籤對應 Zotero 現有分類規則（使用者設定）
- 失敗時記錄至 `papers.db`，下次執行補跑

---

## 八、狀態追蹤（papers.db）

SQLite，主要資料表 `papers`：

| 欄位 | 說明 |
|------|------|
| doi | 主鍵 |
| title | 標題 |
| source | 來源（pubmed / rss） |
| fetched_at | 抓取時間 |
| recommended | 是否被推薦（bool） |
| zotero_key | Zotero 條目 key |
| notion_page_id | Notion 頁面 ID |
| fulltext_done | 全文流水線是否完成 |

---

## 九、錯誤處理

| 情況 | 處理方式 |
|------|------|
| PubMed / RSS 網路失敗 | 跳過當天該來源，繼續執行其他來源 |
| Claude API 失敗 | 略過推薦步驟，仍建 Zotero 條目 |
| Zotero API 失敗 | 記錄至 papers.db，下次補跑 |
| Notion API 失敗 | 同上 |
| Unpaywall 查無全文 | 靜默跳過 |

---

## 十、排程（macOS launchd）

- plist 路徑：`~/Library/LaunchAgents/com.tcm.paper_pipeline.plist`
- 執行時間：每天 07:00
- 機器關機時跳過，不補跑
- Log：`tcm-rag/logs/pipeline.log`

---

## 十一、環境變數（.env）

```
ANTHROPIC_API_KEY=
ZOTERO_API_KEY=
ZOTERO_USER_ID=
NOTION_API_KEY=
NOTION_DATABASE_ID=
UNPAYWALL_EMAIL=
ENABLE_FULLTEXT=false
```

---

## 十二、不在此次範圍

- 全文流水線的實作（預留 `fulltext.py` 鉤子，`ENABLE_FULLTEXT=false`）
- 自動學習閱讀偏好
- 將新論文嵌入向量加入 ChromaDB（獨立任務）
