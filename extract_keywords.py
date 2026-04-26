"""
extract_keywords.py — 批次精煉穴位主治關鍵字
使用 Claude API 將 dong_indications 原文轉換為臨床關鍵字
格式：關鍵字1、關鍵字2（原文節錄...）
"""
import sqlite3
import anthropic
from pathlib import Path

BASE = Path(__file__).parent
DB_PATH = BASE / "dongzhen_new.db"

GROUPS = [
    ["婦科穴", "還巢穴"],
    ["一重穴", "二重穴", "三重穴"],
    ["重子穴", "重仙穴"],
    ["天皇穴", "地皇穴", "人皇穴"],
    ["正筋穴", "正宗穴", "正士穴"],
    ["四花上穴", "四花中穴", "四花外穴"],
    ["水通穴", "水金穴"],
    ["側三里穴", "側下三里穴"],
]

SINGLES = [
    "靈骨穴", "大白穴", "下白穴", "火主穴", "水相穴",
    "通山穴", "火菊穴", "火山穴", "曲陵穴", "木留穴",
    "火硬穴", "天皇副穴",
]

PROMPT = """你是一位熟悉董氏奇穴的中醫師。以下是穴位主治的教科書原文（OCR 抽取，可能含簡體字）。

請提取 3-8 個繁體中文臨床關鍵字，只列症狀或病名，用「、」分隔。
不要書本句子，不要解釋，不要標點以外的符號。

原文：
{text}

只回傳關鍵字，例如：頭痛、肩膀痛、鼻過敏"""


def get_keywords(text: str, client: anthropic.Anthropic) -> str:
    if not text or not text.strip():
        return ""
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=150,
        messages=[{"role": "user", "content": PROMPT.format(text=text[:1500])}],
    )
    return msg.content[0].text.strip()


def process_group(names: list[str], conn: sqlite3.Connection, client: anthropic.Anthropic):
    placeholders = ",".join("?" * len(names))
    rows = conn.execute(
        f"SELECT id, name, dong_indications FROM acupoints WHERE name IN ({placeholders})",
        names,
    ).fetchall()

    if not rows:
        print(f"  ! 找不到：{names}")
        return

    combined = "\n".join(
        f"{name}：{ind}" for _, name, ind in rows if ind
    )
    if not combined:
        print(f"  ! 無主治原文：{[r[1] for r in rows]}")
        return

    label = " + ".join(r[1] for r in rows)
    print(f"  精煉穴組：{label}")
    kw = get_keywords(combined, client)
    print(f"  → {kw}")

    for ap_id, _, _ in rows:
        conn.execute("UPDATE acupoints SET indications_kw=? WHERE id=?", (kw, ap_id))
    conn.commit()


def process_single(name: str, conn: sqlite3.Connection, client: anthropic.Anthropic):
    row = conn.execute(
        "SELECT id, dong_indications FROM acupoints WHERE name=?", (name,)
    ).fetchone()

    if not row:
        print(f"  ! 找不到：{name}")
        return

    ap_id, ind = row
    if not ind:
        print(f"  ! 無主治原文：{name}")
        return

    print(f"  精煉單穴：{name}")
    kw = get_keywords(ind, client)
    print(f"  → {kw}")

    conn.execute("UPDATE acupoints SET indications_kw=? WHERE id=?", (kw, ap_id))
    conn.commit()


def main():
    conn = sqlite3.connect(str(DB_PATH))
    client = anthropic.Anthropic()

    print("=== 穴組 ===")
    for group in GROUPS:
        process_group(group, conn, client)

    print("\n=== 單穴 ===")
    for name in SINGLES:
        process_single(name, conn, client)

    # 統計結果
    filled = conn.execute(
        "SELECT COUNT(*) FROM acupoints WHERE indications_kw IS NOT NULL AND indications_kw != ''"
    ).fetchone()[0]
    print(f"\n完成！共 {filled} 個穴位已填入 indications_kw")
    conn.close()


if __name__ == "__main__":
    main()
