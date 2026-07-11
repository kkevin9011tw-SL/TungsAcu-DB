#!/bin/bash
# 批次跑所有 pending 底圖(02_hand-dorsal 已驗證,跳過)。
# 每張之間留 12s 緩衝避開 Replicate 限速;失敗不中斷,記到 batch_log.txt。
cd "$(dirname "$0")" || exit 1
source ~/.zshrc 2>/dev/null

BASES=$(python3 -c "
import json
c=json.load(open('bases.json'))['bases']
for b,v in c.items():
    if v.get('skip'): continue
    if b=='02_hand-dorsal': continue
    print(b)")

: > batch_log.txt
for b in $BASES; do
  echo "=== $b ===" | tee -a batch_log.txt
  python3 pipeline.py run "$b" 2>&1 | tee -a batch_log.txt
  sleep 12
done
echo "ALL DONE" | tee -a batch_log.txt
