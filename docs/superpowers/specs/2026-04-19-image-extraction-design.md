# 穴位圖片提取與描述功能設計文件

**日期：** 2026-04-19
**專案：** TungsAcu-DB 董氏奇穴檢索工具

---

## 背景與動機

現有 OCR 流程（`ocr_pdf.py`）只提取文字，PDF 中的穴位圖完全遺失。資料庫中已預留 `acupoint_images` 資料表但從未填入資料。本功能補足這個缺口。

---

## 目標

新增 `extract_images.py` 腳本，從 PDF 自動提取穴位圖片，用 Claude Vision API 生成中文描述，存入資料庫，並讓 Streamlit 公開網頁顯示圖片。

---

## 架構

### 新增腳本：`extract_images.py`

```
PDF 檔案
  ↓ PyMuPDF（fitz，已安裝）提取每頁圖片
  ↓
圖號比對（主要方式）
  - 掃描 OCR 文字找圖號（如 图1-1、圖1-1）
  - 比對 acupoints.figure_ref 欄位
  - 找到 → 取得 acupoint_id
  ↓ 若找不到圖號
頁碼比對（備援方式）
  - 用圖片所在頁碼，找最近的穴位
  ↓
Claude Vision API
  - 送圖片，取得穴位圖的中文描述
  ↓
存入資料庫
  - 圖片轉 base64 存入 acupoint_images.image_data
  - 描述存入 acupoint_images.caption
  - 關聯 acupoint_id
```

### 資料庫結構調整

`acupoint_images` 表需新增 `image_data` 欄位（TEXT，存 base64）：

```sql
CREATE TABLE acupoint_images (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    acupoint_id INTEGER NOT NULL,
    image_path  TEXT,               -- 保留，未來可選用
    image_data  TEXT,               -- base64 編碼圖片（用於 Streamlit Cloud）
    caption     TEXT,               -- Claude Vision 生成的中文描述
    figure_ref  TEXT,               -- 原始圖號（如 图1-1）
    match_method TEXT,              -- 'figure_ref' 或 'page_number'
    FOREIGN KEY (acupoint_id) REFERENCES acupoints(id)
);
```

### `app.py` 修改

在穴位詳情頁面，從 `acupoint_images` 讀取 base64 圖片並顯示，附上 Claude 生成的描述文字。

---

## 圖片存放方式

**選擇：base64 存入資料庫**

理由：DB 推送到 GitHub 後，Streamlit Cloud 直接讀取，無需額外的圖片主機或雲端儲存服務。兩台電腦透過 Synology Drive 同步，本機也能正常存取。

---

## 使用方式（規劃）

```bash
# 處理單本 PDF
python extract_images.py <pdf路徑>

# 指定頁碼範圍
python extract_images.py <pdf路徑> --pages 1-50

# 測試（只跑前3頁）
python extract_images.py <pdf路徑> --test
```

---

## 依賴套件

- `pymupdf`（fitz）：已安裝
- `anthropic`：需確認是否已安裝（Claude Vision API）
- `Pillow`：已安裝

---

## 限制與注意事項

- Claude Vision API 需要 API key（`ANTHROPIC_API_KEY`）
- 每張圖片消耗 API token，大量處理時注意費用
- 圖片 base64 會增加 DB 檔案大小，影響 GitHub push 速度
