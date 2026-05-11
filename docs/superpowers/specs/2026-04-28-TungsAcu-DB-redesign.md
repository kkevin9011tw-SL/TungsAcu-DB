# TungsAcu-DB 重新設計 Spec

> **狀態：✅ 已實作（2026-05-12）**  
> 當前架構文件請看 `2026-05-12-CSV-backend-final.md`。本份保留作為歷史規劃參考。

**日期**：2026-04-28  
**目標**：以 CSV + MD 檔取代 SQLite，讓資料可直接用 Excel 維護，搭配 MinerU OCR + AI 解析自動建立初版資料，Streamlit 前端讀取呈現。

---

## 1. 資料架構

```
TungsAcu-DB/
├── data/
│   ├── 穴位表.csv
│   ├── 對針表.csv
│   └── acupoints/
│       ├── 靈骨.md
│       ├── 大白.md
│       └── ...（每穴一個 md）
├── legacy_ocr/          ← 舊 Apple Vision OCR 輸出統一存放
└── 董氏-rag/            ← Streamlit app
```

### 穴位表.csv 欄位

| 欄位 | 說明 |
|------|------|
| 穴名 | 例：靈骨 |
| 部位代碼 | 一一、二二… |
| 部位 | 部位文字描述 |
| 取穴 | 含解剖、針法、針深 |
| 穴位圖 | 圖檔相對路徑 |
| 主治關鍵字 | 逗號分隔，例：頭痛,坐骨神經痛 |
| 董楊思維 | 100 字內精華解說 |
| 備註 | 其他補充 |

### 對針表.csv 欄位

| 欄位 | 說明 |
|------|------|
| 穴組名稱 | 例：靈骨大白 |
| 穴位 | 逗號分隔，例：靈骨,大白 |
| 主治關鍵字 | 逗號分隔 |
| 排序 | 整數，越小越優先（預設 1） |
| 解說 | 用法說明 |

**排序邏輯**：搜尋症狀時先篩選含該關鍵字的列，再按排序欄升冪排列。排序是「這個穴組在它自己的主治裡的重要性」，不同症狀的結果互不干擾。只有需要調整相對順序時才手動修改 CSV。

### 每穴 md 檔

內容混合三類：楊維傑書中詮釋解原文、AI 整理後的結構化解說、臨床筆記。  
供穴位詳情頁的「展開完整內容」按鈕讀取。

---

## 2. 資料來源

| 資料表 | 來源書籍 |
|--------|----------|
| 穴位表 | 楊維傑《董氏奇穴穴位詮釋解》（唯一參考書） |
| 對針表 | 楊維傑《區位易象特效對針》（初版，之後擴增） |

---

## 3. 建立流程

```
PDF
 ↓  Step 1：MinerU OCR（桌機 SSH，分段跑）
Markdown 文字
 ↓  Step 2：Claude AI 解析
穴位表.csv + 對針表.csv + acupoints/*.md
 ↓  Step 3：人工校對（直接開 Excel 修改）
最終資料
 ↓  Streamlit 讀取
網站
```

### Step 1：PDF 分段 OCR

PDF 超過約 100 頁時分段處理，避免 MinerU 中斷。

```python
# split_pdf.py（在桌機 SSH 執行）
import fitz
import argparse

def split_pdf(input_path, chunk_size=80):
    doc = fitz.open(input_path)
    total = len(doc)
    base = input_path.rsplit('.', 1)[0]
    for i, start in enumerate(range(0, total, chunk_size), 1):
        end = min(start + chunk_size, total)
        out = fitz.open()
        out.insert_pdf(doc, from_page=start, to_page=end-1)
        out_path = f"{base}_part{i}.pdf"
        out.save(out_path)
        print(f"Part {i}: 頁 {start+1}–{end} → {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--chunk", type=int, default=80)
    args = parser.parse_args()
    split_pdf(args.pdf, args.chunk)
```

```bash
python3 split_pdf.py dongzhen_quanshi.pdf --chunk 80
magic-pdf -p dongzhen_quanshi_part1.pdf -o output/part1/
magic-pdf -p dongzhen_quanshi_part2.pdf -o output/part2/
# 依此類推
```

### Step 2：AI 解析

Claude 讀取 MinerU 輸出的 Markdown，識別每穴區塊，填入 CSV 欄位並生成 md 檔。（解析腳本待實作）

### Step 3：人工校對

直接用 Excel 開啟 CSV 修改。對應 md 檔用文字編輯器開啟。

---

## 4. Streamlit 網站結構

### 導覽

左側 sidebar 頂部下拉選單切換三個模式：穴位 / 症狀 / 對針。

### 穴位模式

- **左欄**：搜尋框（輸入穴名）、部位篩選按鈕（大字部位代碼＋小字中文說明）、穴位列表
- **右欄**：穴位詳情（部位、取穴、主治關鍵字、董楊思維、穴位圖）＋「展開完整內容」按鈕（載入 md 檔）

部位按鈕格式：
```
一一        二二        三三        四四
手指部      手掌部      前臂部      後臂部

五五        六六        七七        八八
足趾部      足掌部      小腿部      大腿部

九九        十十        背腰部      胸腹部
耳部        頭面部
```

### 症狀模式

搜尋框搭配類別分組（痛症、五官科、腸胃科等），細節待後續討論。  
搜尋流程：輸入症狀 → 篩選對針表主治關鍵字 → 按排序欄升冪 → 顯示結果。  
結果中每個穴名為可點擊連結，跳回穴位模式對應穴位。

### 對針模式

完整列出對針表所有穴組，按筆畫排序，穴名可點擊跳回穴位模式。

---

## 5. UI 風格

參考 ZaraLcy/tung-acupoints 的雙欄佈局與中醫古籍配色（羊皮紙色、金色、朱紅），後續再優化。

---

## 待定事項

- 症狀模式的類別分組設計（痛症子分類、五官科、腸胃科等）
- AI 解析腳本的 prompt 設計與驗證
- 穴位圖的存放與命名規則
