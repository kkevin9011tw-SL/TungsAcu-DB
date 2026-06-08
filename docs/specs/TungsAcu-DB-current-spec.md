# TungsAcu-DB Current Spec

**狀態**：現行唯一 spec  
**最後整理**：2026-06-07  
**取代**：`docs/archive/specs/` 內所有日期版 TungsAcu-DB 舊 spec。  
**工作日誌**：`docs/WORKLOG.md`。  
**Active TODO**：統一放在 `docs/WORKLOG.md` 結尾。

---

## 1. 核心原則

**資料與程式分離。** 後端是純檔案（CSV/MD/JPG），前端 Streamlit 只負責讀取與呈現。任何時候顥軒想改細部資料，直接用 Excel/Numbers/文字編輯器打開檔案改即可，不必懂 SQL，不必進 admin tab，不必跑遷移腳本。

---

## 2. 檔案結構

```
TungsAcu-DB/
├── app.py                       主程式
├── data_loader.py               pandas 查詢層 + @st.cache_data
├── migrate_to_csv.py            一次性遷移腳本（從 archive/ DB 重產 data/）
├── extract_images_v2.py         從 MinerU 輸出抽穴位圖到 extracted_images/
├── requirements.txt             Streamlit Cloud 相依
├── .streamlit/config.toml       固定 light theme
├── README_LOCAL_WORKSPACE.md    本機正式工作區說明
├── assets/
│   └── logo-seal.png            topbar 印章 logo
├── data/                        ★ 正式後端
│   ├── 穴位表.csv               234 列 × 13 欄
│   ├── 對針表.csv               146 列（限《區位易象特效對針》）
│   ├── 症狀治療.csv             5210 列（常見病/痛症/其他著作）
│   ├── 部位表.csv               13 列
│   ├── images/                  203 張 jpg
│   └── notes/                   233 份 md（每穴一份長文）
├── archive/                     歷史 SQLite 快照
├── docs/
│   ├── WORKLOG.md               唯一工作日誌 + Active TODO
│   ├── specs/
│   │   └── TungsAcu-DB-current-spec.md
│   └── archive/                 歷史 spec/plan
└── extracted_images/            圖片審核中介，.gitignore 不上傳
```

---

## 3. 資料表 schema

### 穴位表.csv（13 欄）

| 欄位 | 範例 | 說明 |
|------|------|------|
| 穴名 | 靈骨穴 | 必填、唯一 |
| 部位代碼 | 二二 | 對應部位表 |
| 部位 | 二二部位 | 從部位表帶 |
| 身體分區 | 手掌穴位 | 從部位表帶 |
| 穴號 | 圖2-11 | 對應 MinerU figure_ref |
| 取穴定位 | 手背拇指與食指叉骨間…… | 合併董師部位+取穴+location_detail |
| 針法 | 直刺 1.5–2 寸…… | |
| 主治關鍵字 | 頭痛,坐骨神經痛,腰痛 | 半形逗號分隔，每詞建議 ≤ 6 字 |
| 董楊思維 | 維傑新用前 200 字摘要 | 100–200 字精華；長文進 notes/ |
| 備註 | 孕婦禁針 | |
| 穴位圖 | images/圖2-11_靈骨穴.jpg | 相對 data/ 的路徑，無圖留空 |
| 詳細筆記 | notes/靈骨穴.md | 相對 data/ 的路徑 |
| 頁碼 | 72 | 《穴位詮釋解》原書頁碼 |

### 對針表.csv（7 欄）

| 欄位 | 範例 | 說明 |
|------|------|------|
| 穴組名稱 | 靈骨大白 | 兩穴去「穴」字串接 |
| 穴位 | 靈骨,大白 | 兩穴用半形逗號 |
| 主治關鍵字 | 坐骨神經痛 | |
| 排序 | 3 | 越小越優先；搜尋結果按此升冪 |
| 理論 | 大腸經與肝經臟腑別通…… | |
| 針法 | 透過重仙穴 | |
| 頁碼 | | 《區位易象特效對針》頁碼 |

**規則**：對針表**只收錄《區位易象特效對針》**。其他著作的對針配伍進「症狀治療表」。

### 症狀治療.csv（4 欄）

| 欄位 | 範例 |
|------|------|
| 症狀 | 頭痛 |
| 推薦穴位 | 靈骨配大白 |
| 來源 | 常見病特效一針療法 |
| 頁碼 | 45 |

**規則**：來源限定於楊維傑著作（《常見病》《痛證》以及其他著作如《治療析要》《五輸穴》《原理結構》），不包括區位易象（避免與對針表重複）。

### 症狀標準詞與相關關鍵字

《董氏奇穴治療析要》目錄作為全站「症狀標準詞表」。症狀頁、穴位詳情頁的主要主治症狀、對針主治分類，都應優先對齊這份標準詞表。

既有從《穴位詮釋解》與其他文字抽取出的 `主治關鍵字` 不丟棄，但定位為「相關關鍵字」：

- 可用於搜尋命中。
- 可顯示在穴位頁作為補充提示。
- 可作為標準症狀詞的同義詞、近義詞、病機詞、部位詞或臨床提示詞。
- 不作為症狀頁與對針頁的主分類。

已新增：

- `data/治療析要目錄候選.csv`：從《治療析要》Markdown 正文標題抽出的目錄候選與匹配狀態，供人工校對。
- `data/症狀標準詞表.csv`：收錄《治療析要》目錄校對後的正式症狀詞。`matched` 項目會轉為「目錄標準詞」；`not_in_standard_terms` 先留在候選表，不進正式詞表。
- `data/症狀映射表.csv`：將原始標題、括號內別名、同義詞、抽取詞映射到標準症狀詞。舊抽取詞先保留搜尋命中，待人工映射到目錄標準詞。

同步規則：

- `匹配標準症狀` 是正式詞來源。
- 括號內文字只作別名或輔助詞，不拆成正式詞。
- 頂層 `、` 會拆成多個正式詞；括號內的 `、` 不拆正式詞，只拆映射別名。
- `目錄症狀` 原始標題一律進 `症狀映射表.csv`，保留原書標題搜尋命中。
- 英文專有名詞如 `Bell's palsy`、`TMJ`、`TMD` 放在括號內作別名，不加雙引號，不作正式詞。

`data/症狀標準詞表.csv` 欄位：

| 欄位 | 說明 |
|------|------|
| 標準症狀 | 全站顯示與分類用症狀詞 |
| 分類 | 目錄標準詞帶入《治療析要》正文節名；抽取詞待整理 |
| 排序 | 前端顯示用連續排序 |
| 詞表層級 | 目前正式詞表皆為 `目錄標準詞` |
| 目錄排序 | 對應 `data/治療析要目錄候選.csv` 的原始目錄序號 |
| 目錄症狀 | 目錄候選中的原始標題文字 |
| 目錄節 | 目錄候選中的節名 |
| 來源行 | 目錄候選來自 Markdown 的行號 |
| 來源 | 董氏奇穴治療析要 |
| 條目數 | 此症狀在 `症狀治療.csv` 中出現幾列 |
| 空推薦穴位數 | 推薦穴位為空的列數，用於人工審核 |
| 備註 | 人工審核註記 |

`data/症狀映射表.csv` 欄位：

| 欄位 | 說明 |
|------|------|
| 關鍵字 | 使用者搜尋詞、抽取詞或同義詞 |
| 標準症狀 | 對應到 `症狀標準詞表.csv` 的標準詞 |
| 類型 | 原始症狀、同義詞、近義詞、部位詞、病機詞、抽取詞 |
| 來源 | 該映射來源 |
| 備註 | 人工審核註記 |

顯示原則：

- 症狀頁：預設清單只列標準症狀詞；搜尋可命中標準詞與相關關鍵字。
- 穴位詳情頁「主治原理」：主要顯示標準症狀詞；相關關鍵字以次要文字或折疊區呈現。
- 對針頁：主治分類應對齊標準症狀詞；原始主治內容保留為說明，不作為主分類。
- 臨床配伍 tab：仍保留來源分區（對針、常見病、痛症、其他著作），但《治療析要》資料可在後續 UI 中升級為更清楚的臨床索引來源。

### 部位表.csv（3 欄）

13 列固定：一一、二二、三三、四四、五五、六六、七七、八八、九九、十十、背腰、胸腹、增補。

### notes/{穴名}.md 結構

```markdown
# 穴名

**穴號**：圖N-X　**部位**：N-N部位　身體分區

## 董師原文
- **部位**：…
- **主治**：…
- **取穴**：…
- **手術**：…
- **注意**：…

## 詮解發揮
### 穴名闡釋
…
### 維傑新用 / 董楊思維
…
### 解說及發揮
…
### 比較
…
### 引申
…

## 現代解剖
…

---
《穴位詮釋解》p.XX
```

app.py 詳情頁 Tab 1 用 regex 抽 `### 標籤` 段落分開顯示；Tab 0 抽 `## 現代解剖`；其餘整段塞「📜 詳細筆記」expander。

---

## 4. 前端架構

### 模式

三個頂層模式（左 sidebar selectbox）：
- 📍 穴位 — 部位 pills + 列表 + 搜尋
- 💊 症狀 — 預設清單（依身體區位分組） + 自由搜尋
- 🔗 對針 — 預設清單（依排序欄） + 自由搜尋

切換模式自動清空搜尋欄並回到該模式預設視圖。

### 詳情頁三 tab（固定，不要動）

1. **取穴定位**：左欄 位置 / 針法 / 備註，右欄 穴位圖（width=320）；下方 現代解剖 + 詳細筆記 expander
2. **主治原理**：主治關鍵字 buttons（點擊跳症狀模式）+ 董楊思維 + 五段原理小標
3. **臨床配伍**：對針（區位易象）→ 常見病 → 痛症 → 其他著作 四個分區

admin 模式登入後多出第 4 個 tab「✏️ 編輯」（短欄位編輯 + 危險區刪除）。

### 視覺風格

宣紙硃砂：parchment 底色、vermillion 主色、gold 點綴。Noto Serif TC + Noto Sans TC 字體。自訂全寬 topbar 蓋 Streamlit 預設 header。`show_detail` 用 `@st.fragment` 包，內部互動只重跑詳情區（緩解 FOUC）。

---

## 5. Admin 後台

### 進入方式

sidebar 最下方「🔐 管理員」展開 → 輸入密碼（本機 fallback `admin123`，Cloud 從 secrets 讀 `admin_password`）。

### 三個 admin 功能

1. **➕ 新增穴位**（sidebar 按鈕 → 表單頁）：填穴名 / 部位代碼 / 穴號 + 五個短欄位 → 寫一列到 `data/穴位表.csv`，跳到新穴詳情
2. **🖼 圖片審核**（sidebar 按鈕 → 審核頁）：讀 `extracted_images/manifest.json`，逐張過濾、採用、跳過、重置；採用會複製到 `data/images/` 並更新 CSV「穴位圖」欄
3. **✏️ 編輯 + 🗑 刪除**（詳情頁第 4 tab）：改 6 個短欄位寫回 CSV；底部「危險區」勾選確認後刪整列

長文編輯（notes/*.md）目前**不在 admin tab 內**，請直接用文字編輯器開檔案改。

---

## 6. 部署流程

```
本機改 (改 data/*.csv 或改 app.py)
  ↓
streamlit run app.py --server.port 8519   ← 本機測試（port 任選，目前慣用 8519）
  ↓ 確認 OK
git add data/ app.py …
git commit -m "..."
git push
  ↓ 1–2 分鐘
Streamlit Cloud 自動重新部署
公開網址：https://tungsacu-db-9fkdgtsgxtshtxxmnodl4i.streamlit.app/
```

**SynologyDrive 路徑下 Streamlit 檔案監看不可靠**，本機改完常需手動重啟才生效（kill 原 process → 重跑）。

---

## 7. 常見維護任務

### 修一格資料
Numbers 打開 `data/穴位表.csv` → 改 → 存（CSV 格式）→ 瀏覽器刷新

### 改某穴的長文
CotEditor 打開 `data/notes/{穴名}.md` → 改 → 存

### 新增一穴
- 走 admin 新增穴位介面（推薦），或
- 直接在 Numbers 加一列；長文要的話另外建 `notes/{穴名}.md`

### 刪一穴
- 走詳情頁編輯 tab「危險區」（連帶刪 md），或
- Numbers 刪該列 + 手動刪 `notes/{穴名}.md`

### 重產所有 CSV（緊急復原用）
```
python migrate_to_csv.py
```
腳本會從 `archive/*.db` 重新匯出所有 data/ 內容。⚠️ **會覆寫你的手改**。

### 加更多穴位圖
1. PDF 用 MinerU 跑 OCR → 4 個 part 的 content_list.json
2. `python extract_images_v2.py` → 寫 `extracted_images/manifest.json`
3. admin 圖片審核介面逐張採用

---

## 8. 重要 npm/pip 相依

`requirements.txt`：
```
streamlit==1.56.0
pandas>=2.0,<3.0
opencc-python-reimplemented>=0.1.7,<0.2.0
```

`extract_images_v2.py` 額外需要 pymupdf、Pillow（不放 requirements，因為 Streamlit Cloud 不會跑這支腳本）。

---

## 9. 不在這份 spec 範圍但已有的東西

- `assets/logo-seal.png` 印章 logo
- `.streamlit/config.toml` 強制宣紙淺色主題
- `.streamlit/secrets.toml`（gitignore）放 admin 密碼
- `archive/` 歷史 SQLite 備份
- `docs/archive/specs/`：日期版舊 spec，留作歷史參考
- `docs/archive/plans/`：舊 plan/todo，留作歷史參考

---

## 10. 給未來接手者

**不要做**：
- 不要再把 SQLite 接回來
- 不要動 archive/
- 不要動 tab 名稱與順序（取穴定位／主治原理／臨床配伍）
- 不要把區位易象、常見病、痛症的對針混在一起（規則：對針表只收區位易象，其餘進症狀治療表）
- 不要加醫案頁（顥軒明確說不要）

**可以做**：
- 改 CSS 視覺
- 加新 admin 功能（例如 notes/ md 編輯器）
- 把症狀預設清單加二級分類
- 對針排序從「排序欄」改成筆畫排序或其他
- 加新欄位（要同步改 `migrate_to_csv.py` 與 `data_loader.py`）

**遇到問題去哪查**：
- 為什麼 X 這樣設計 → 看 `docs/WORKLOG.md` 對應日期的「背景與動機」
- 程式怎麼跑的 → `app.py` + `data_loader.py` 兩個檔案就是全部
- 資料怎麼長的 → 直接打開 `data/*.csv`
