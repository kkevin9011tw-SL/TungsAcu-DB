# 穴位圖片提取功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `extract_images.py`，從 PDF 自動提取穴位圖，用 Claude Vision API 生成中文描述，存進資料庫，並讓 Streamlit app 顯示圖片。

**Architecture:** 三個獨立步驟——（1）資料庫 schema 升級；（2）新腳本提取圖片並呼叫 Claude Vision；（3）app.py 新增圖片顯示 tab。每步都能獨立測試。

**Tech Stack:** Python 3.11（Homebrew）、PyMuPDF（fitz）、anthropic SDK、SQLite、Streamlit

---

## 檔案異動一覽

| 動作 | 檔案 | 說明 |
|------|------|------|
| 建立 | `tcm-rag/extract_images.py` | 主要新腳本 |
| 建立 | `tcm-rag/migrate_add_image_data.py` | 一次性 DB schema 升級 |
| 修改 | `tcm-rag/app.py` | 新增穴位圖顯示 tab |
| 修改 | `tcm-rag/requirements.txt` | 不需修改（extract_images.py 為本機腳本，不部署） |

---

## Task 1：安裝套件

**Files:**
- 無需修改檔案

- [ ] **Step 1：安裝 PyMuPDF 與 anthropic**

```bash
/opt/homebrew/bin/pip3.11 install pymupdf anthropic
```

預期輸出：`Successfully installed pymupdf-... anthropic-...`

- [ ] **Step 2：確認安裝成功**

```bash
/opt/homebrew/bin/python3.11 -c "import fitz, anthropic; print('ok')"
```

預期輸出：`ok`

---

## Task 2：資料庫 schema 升級

**Files:**
- 建立：`tcm-rag/migrate_add_image_data.py`

`acupoint_images` 表原本只有 `image_path` 和 `caption`，需新增 `image_data`（base64）、`figure_ref`、`match_method` 欄位。

- [ ] **Step 1：建立 migrate_add_image_data.py**

```python
"""一次性執行：升級 acupoint_images 表的欄位"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "dongzhen_new.db"

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

# 取得現有欄位
cols = [row[1] for row in cur.execute("PRAGMA table_info(acupoint_images)").fetchall()]

if "image_data" not in cols:
    cur.execute("ALTER TABLE acupoint_images ADD COLUMN image_data TEXT")
    print("新增 image_data 欄位")

if "figure_ref" not in cols:
    cur.execute("ALTER TABLE acupoint_images ADD COLUMN figure_ref TEXT")
    print("新增 figure_ref 欄位")

if "match_method" not in cols:
    cur.execute("ALTER TABLE acupoint_images ADD COLUMN match_method TEXT")
    print("新增 match_method 欄位")

conn.commit()
conn.close()
print("完成")
```

- [ ] **Step 2：執行 migration**

```bash
cd "/Users/samuelmac81/Library/CloudStorage/SynologyDrive-中醫資料庫/AI_Projects/tcm-rag"
/opt/homebrew/bin/python3.11 migrate_add_image_data.py
```

預期輸出：
```
新增 image_data 欄位
新增 figure_ref 欄位
新增 match_method 欄位
完成
```

- [ ] **Step 3：確認欄位存在**

```bash
/opt/homebrew/bin/python3.11 -c "
import sqlite3
from pathlib import Path
conn = sqlite3.connect('dongzhen_new.db')
cols = [r[1] for r in conn.execute('PRAGMA table_info(acupoint_images)').fetchall()]
print(cols)
"
```

預期輸出包含：`['id', 'acupoint_id', 'image_path', 'caption', 'image_data', 'figure_ref', 'match_method']`

- [ ] **Step 4：commit**

```bash
cd "/Users/samuelmac81/Library/CloudStorage/SynologyDrive-中醫資料庫/AI_Projects/tcm-rag"
git add migrate_add_image_data.py
git commit -m "feat: add image_data columns to acupoint_images"
```

---

## Task 3：建立 extract_images.py

**Files:**
- 建立：`tcm-rag/extract_images.py`

- [ ] **Step 1：建立完整腳本**

```python
"""
穴位圖片提取工具
從 PDF 提取圖片 → Claude Vision 描述 → 存入 acupoint_images 資料庫

用法：
  python extract_images.py <pdf路徑>              # 全本
  python extract_images.py <pdf路徑> --test       # 只跑前5頁
  python extract_images.py <pdf路徑> --pages 1-20 # 指定頁碼
"""
import argparse
import base64
import io
import re
import sqlite3
import sys
from pathlib import Path

import anthropic
import fitz
from PIL import Image

BASE    = Path(__file__).parent
DB_PATH = BASE / "dongzhen_new.db"

# 圖號模式：图1-1、圖1-1、图 1-1 等變體
FIGURE_PAT = re.compile(r"[图圖]\s*(\d+[-–]\d+)")

client = anthropic.Anthropic()


def load_figure_ref_map(conn: sqlite3.Connection) -> dict[str, int]:
    """回傳 {figure_ref: acupoint_id}，例如 {'图1-1': 3}"""
    rows = conn.execute(
        "SELECT id, figure_ref FROM acupoints WHERE figure_ref IS NOT NULL AND figure_ref != ''"
    ).fetchall()
    result = {}
    for ap_id, ref in rows:
        # 正規化：移除空格，統一用半形數字
        key = re.sub(r"\s", "", ref).lower()
        result[key] = ap_id
    return result


def normalize_figure_ref(raw: str) -> str:
    return re.sub(r"\s", "", raw).lower()


def find_acupoint_by_figure(
    ocr_text_near_page: str,
    figure_map: dict[str, int],
) -> tuple[int | None, str | None]:
    """
    在頁面 OCR 文字中找圖號，比對 figure_map。
    回傳 (acupoint_id, 圖號) 或 (None, None)。
    """
    for m in FIGURE_PAT.finditer(ocr_text_near_page):
        candidate = normalize_figure_ref(m.group(0))
        if candidate in figure_map:
            return figure_map[candidate], m.group(0)
    return None, None


def find_acupoint_by_page(page_num: int, conn: sqlite3.Connection) -> int | None:
    """備援：用書本頁碼找最近的穴位"""
    row = conn.execute(
        """
        SELECT id FROM acupoints
        WHERE page_number IS NOT NULL
        ORDER BY ABS(page_number - ?) LIMIT 1
        """,
        (page_num,),
    ).fetchone()
    return row[0] if row else None


def describe_image(img_bytes: bytes) -> str:
    """送圖片給 Claude Vision，取得繁體中文描述"""
    b64 = base64.standard_b64encode(img_bytes).decode("utf-8")
    msg = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "這是一張來自中醫董氏奇穴教科書的圖片。"
                            "請用繁體中文描述圖片內容，包含：穴位位置、體表標誌、針刺方向（若有）。"
                            "若非穴位圖（如裝飾、目錄、文字頁），請回答「非穴位圖」。"
                            "回答限 150 字以內。"
                        ),
                    },
                ],
            }
        ],
    )
    return msg.content[0].text.strip()


def extract_page_images(page: fitz.Page, min_size: int = 100) -> list[bytes]:
    """從單頁提取所有圖片，過濾太小的（裝飾用小圖）"""
    results = []
    for img_info in page.get_images(full=True):
        xref = img_info[0]
        base_img = page.parent.extract_image(xref)
        w = base_img.get("width", 0)
        h = base_img.get("height", 0)
        if w < min_size or h < min_size:
            continue
        img_bytes = base_img["image"]
        # 統一轉成 PNG
        pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        results.append(buf.getvalue())
    return results


def load_page_ocr_text(ocr_txt_path: Path, page_num: int) -> str:
    """從已存在的 OCR 文字檔讀取指定頁的內容（前後各一頁）"""
    if not ocr_txt_path.exists():
        return ""
    text = ocr_txt_path.read_text(encoding="utf-8")
    # 找第 page_num 頁（1-indexed）的區塊
    pat = re.compile(
        rf"={'{'}10,{'}'}\n第 {page_num} 頁\n={'{'}10,{'}'}(.*?)(?==={'{'}10,{'}'}|$)",
        re.DOTALL,
    )
    m = pat.search(text)
    return m.group(1) if m else ""


def process_pdf(pdf_path: Path, page_range: range, ocr_txt_path: Path | None):
    conn = sqlite3.connect(str(DB_PATH))
    figure_map = load_figure_ref_map(conn)

    doc = fitz.open(str(pdf_path))
    inserted = skipped = 0

    for page_num in page_range:
        if page_num >= len(doc):
            break
        page = doc[page_num]
        book_page = page_num + 1  # 1-indexed

        images = extract_page_images(page)
        if not images:
            continue

        # 取得此頁 OCR 文字（用於圖號比對）
        ocr_near = ""
        if ocr_txt_path:
            ocr_near = load_page_ocr_text(ocr_txt_path, book_page)

        for img_bytes in images:
            # 方法 B：圖號比對
            ap_id, fig_ref = find_acupoint_by_figure(ocr_near, figure_map)
            match_method = "figure_ref"

            # 方法 A 備援：頁碼比對
            if ap_id is None:
                ap_id = find_acupoint_by_page(book_page, conn)
                match_method = "page_number"
                fig_ref = None

            if ap_id is None:
                print(f"  第 {book_page} 頁：找不到對應穴位，略過")
                skipped += 1
                continue

            # Claude Vision 描述
            print(f"  第 {book_page} 頁：送 Claude Vision 描述中...")
            description = describe_image(img_bytes)

            if description == "非穴位圖":
                print(f"  第 {book_page} 頁：非穴位圖，略過")
                skipped += 1
                continue

            b64 = base64.standard_b64encode(img_bytes).decode("utf-8")
            conn.execute(
                """
                INSERT INTO acupoint_images
                  (acupoint_id, image_data, caption, figure_ref, match_method)
                VALUES (?, ?, ?, ?, ?)
                """,
                (ap_id, b64, description, fig_ref, match_method),
            )
            conn.commit()
            inserted += 1
            print(f"  ✓ 穴位 id={ap_id}，方法={match_method}，描述={description[:40]}...")

    conn.close()
    doc.close()
    print(f"\n完成：插入 {inserted} 張，略過 {skipped} 張")


def main():
    parser = argparse.ArgumentParser(description="PDF 穴位圖片提取")
    parser.add_argument("pdf", help="PDF 檔案路徑")
    parser.add_argument("--test", action="store_true", help="只跑前 5 頁")
    parser.add_argument("--pages", help="頁碼範圍，例如 1-20")
    parser.add_argument("--ocr-txt", help="對應的 OCR 文字檔路徑（用於圖號比對）")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"找不到檔案：{pdf_path}")
        sys.exit(1)

    doc = fitz.open(str(pdf_path))
    total = len(doc)
    doc.close()

    if args.test:
        page_range = range(min(5, total))
        label = "測試（前5頁）"
    elif args.pages:
        s, e = args.pages.split("-")
        page_range = range(int(s) - 1, min(int(e), total))
        label = f"第{s}~{e}頁"
    else:
        page_range = range(total)
        label = f"全本（{total}頁）"

    ocr_txt_path = Path(args.ocr_txt) if args.ocr_txt else None

    print(f"PDF：{pdf_path.name}")
    print(f"範圍：{label}")
    process_pdf(pdf_path, page_range, ocr_txt_path)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2：確認 ANTHROPIC_API_KEY 已設定**

```bash
echo $ANTHROPIC_API_KEY
```

若為空，執行：
```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # 填入實際 key
```

- [ ] **Step 3：測試跑前 5 頁（指定《穴位詮釋解》PDF 與 OCR 文字）**

```bash
cd "/Users/samuelmac81/Library/CloudStorage/SynologyDrive-中醫資料庫/AI_Projects/tcm-rag"
/opt/homebrew/bin/python3.11 extract_images.py \
  "/Users/samuelmac81/Library/CloudStorage/SynologyDrive-中醫資料庫/AI_Projects/董針資料/楊維傑醫師著作/楊維傑-董氏奇穴穴位詮釋解.pdf" \
  --test \
  --ocr-txt "ocr_output/楊維傑-董氏奇穴穴位詮釋解_full.txt"
```

預期輸出：看到每頁的處理結果，至少有一筆 `✓` 成功。

- [ ] **Step 4：確認資料存入 DB**

```bash
/opt/homebrew/bin/python3.11 -c "
import sqlite3
conn = sqlite3.connect('dongzhen_new.db')
rows = conn.execute('SELECT acupoint_id, figure_ref, match_method, caption FROM acupoint_images LIMIT 5').fetchall()
for r in rows:
    print(r[0], r[1], r[2], r[3][:40])
"
```

- [ ] **Step 5：commit**

```bash
git add extract_images.py migrate_add_image_data.py
git commit -m "feat: add extract_images.py for PDF image extraction with Claude Vision"
```

---

## Task 4：app.py 新增穴位圖 tab

**Files:**
- 修改：`tcm-rag/app.py:117-128`（新增 load_acupoint_images 函式）
- 修改：`tcm-rag/app.py:186`（新增 tab）
- 修改：`tcm-rag/app.py:191-224`（新增 tab 內容）

- [ ] **Step 1：在 app.py 的 `load_acupoint` 函式之後加入 load_acupoint_images**

在 `app.py` 第 128 行之後插入：

```python
@st.cache_data
def load_acupoint_images(ap_id: int):
    return q(
        "SELECT image_data, caption, figure_ref FROM acupoint_images WHERE acupoint_id=?",
        (ap_id,)
    )
```

- [ ] **Step 2：在 show_acupoint_detail 中新增圖片 tab**

將 `app.py` 第 186 行的 `st.tabs(...)` 修改為：

```python
tab_dong, tab_jie, tab_img, tab_sym, tab_pairs = st.tabs(
    ["📜 董師原文", "🔬 詮解發揮", "🖼 穴位圖", "💊 其他書籍主治", "🔗 對針組合"]
)
```

- [ ] **Step 3：加入穴位圖 tab 內容**

在 `tab_jie` 的 with 區塊結束後，插入：

```python
    # ── 穴位圖 ──
    with tab_img:
        images = load_acupoint_images(ap_id)
        if not images:
            st.info("此穴位尚無圖片資料")
        else:
            for img_data, caption, fig_ref in images:
                import base64
                img_bytes = base64.b64decode(img_data)
                st.image(img_bytes, use_container_width=True)
                if fig_ref:
                    st.caption(f"圖號：{fig_ref}")
                if caption:
                    st.markdown(f"""
                    <div class="detail-section">
                      <div class="field-label">圖片描述</div>
                      <div class="field-value">{caption}</div>
                    </div>""", unsafe_allow_html=True)
```

- [ ] **Step 4：本機測試**

```bash
"/Users/samuelmac81/Library/CloudStorage/SynologyDrive-中醫資料庫/AI_Projects/tcm-rag/venv/bin/streamlit" run \
  "/Users/samuelmac81/Library/CloudStorage/SynologyDrive-中醫資料庫/AI_Projects/tcm-rag/app.py"
```

打開 http://localhost:8501，點進有圖片的穴位，確認「🖼 穴位圖」tab 正常顯示。

- [ ] **Step 5：push 到 Streamlit Cloud**

```bash
cd "/Users/samuelmac81/Library/CloudStorage/SynologyDrive-中醫資料庫/AI_Projects/tcm-rag"
git add app.py dongzhen_new.db
git commit -m "feat: show acupoint images in Streamlit app"
git push
```

等 1-2 分鐘後至公開網址確認。

---

## 注意事項

- `extract_images.py` 需要 `ANTHROPIC_API_KEY` 環境變數，每張圖片約消耗 500-1000 tokens
- 全本 PDF 一次跑完圖片可能很多，建議先用 `--pages 1-50` 分批測試
- 若 PDF 找不到路徑，請確認 PDF 存放位置（可能在 Synology Drive 某資料夾）
