#!/usr/bin/env python3
"""Standardize pair-treatment keywords with the curated symptom mapping table."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
SOURCE = DATA_DIR / "pair_rebuild" / "對針表_重建草稿.csv"
MAPPINGS = DATA_DIR / "症狀映射表.csv"
STANDARDS = DATA_DIR / "症狀標準詞表.csv"
OUTPUT = DATA_DIR / "pair_rebuild" / "對針表_關鍵字標準化.csv"
UNMAPPED = DATA_DIR / "pair_rebuild" / "對針關鍵字_未映射.csv"
REPORT = DATA_DIR / "pair_rebuild" / "對針關鍵字_標準化報告.json"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(
    path: Path, rows: list[dict[str, str]], fieldnames: list[str]
) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def split_keywords(value: str) -> list[str]:
    normalized = value.replace("，", ",").replace("、", ",").replace("；", ",")
    return [part.strip() for part in normalized.split(",") if part.strip()]


def main() -> int:
    source_rows = read_rows(SOURCE)
    standard_rows = read_rows(STANDARDS)
    mapping_rows = read_rows(MAPPINGS)
    standard_names = {row["標準症狀"].strip() for row in standard_rows}

    mapping: dict[str, list[str]] = {}
    invalid_targets: list[dict[str, str]] = []
    for row in mapping_rows:
        keyword = row["關鍵字"].strip()
        target = row["標準症狀"].strip()
        if not keyword or not target:
            continue
        if target not in standard_names:
            invalid_targets.append({"關鍵字": keyword, "標準症狀": target})
            continue
        mapping.setdefault(keyword.casefold(), [])
        if target not in mapping[keyword.casefold()]:
            mapping[keyword.casefold()].append(target)

    unmapped_counter: Counter[str] = Counter()
    unmapped_pairs: dict[str, set[str]] = {}
    changed_groups: set[str] = set()
    result_rows: list[dict[str, str]] = []

    for row in source_rows:
        original = split_keywords(row.get("主治關鍵字", ""))
        standardized: list[str] = []
        for keyword in original:
            targets = mapping.get(keyword.casefold(), [])
            if not targets and keyword in standard_names:
                targets = [keyword]
            if not targets:
                targets = [keyword]
                unmapped_counter[keyword] += 1
                unmapped_pairs.setdefault(keyword, set()).add(
                    row.get("穴組名稱", "")
                )
            for target in targets:
                if target not in standardized:
                    standardized.append(target)

        value = ",".join(standardized)
        if value != row.get("主治關鍵字", ""):
            changed_groups.add(row.get("穴組名稱", ""))
        updated = dict(row)
        updated["主治關鍵字"] = value
        result_rows.append(updated)

    fieldnames = list(source_rows[0].keys())
    write_rows(OUTPUT, result_rows, fieldnames)
    write_rows(
        UNMAPPED,
        [
            {
                "未映射關鍵字": keyword,
                "涉及穴組數": len(unmapped_pairs[keyword]),
                "穴組名稱": "、".join(sorted(unmapped_pairs[keyword])),
            }
            for keyword, count in sorted(unmapped_counter.items())
        ],
        ["未映射關鍵字", "涉及穴組數", "穴組名稱"],
    )

    report = {
        "source": str(SOURCE.relative_to(ROOT)),
        "output": str(OUTPUT.relative_to(ROOT)),
        "row_count": len(result_rows),
        "pair_count": len({row["目錄排序"] for row in result_rows}),
        "changed_pair_count": len(changed_groups),
        "changed_pairs": sorted(changed_groups),
        "unmapped_keyword_count": len(unmapped_counter),
        "ignored_nonstandard_mapping_count": len(invalid_targets),
    }
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
