# skin-pipeline — 底圖套皮正式管線

2026-07-03 定案(E 方案)。把 19 張 WHO 線稿底圖換成柔和寫實皮膚版,
**marker JSON 標記全部沿用**(輸出尺寸與座標系跟原底圖完全相同)。

黃金樣本:`02_hand-dorsal`(已驗證)。試驗與風格演進史在 `../skin-trial-20260703/`。

## 流程(每張底圖一次,所有穴位共用)

1. 線稿 → 只留外輪廓+指甲的控制圖(骨頭線去除,AI 才不會把骨頭畫成硬邊)
2. Replicate `black-forest-labs/flux-canny-pro` 生成皮膚(約 US$0.05/張)
3. 還原座標系(work_box 逆映射回原尺寸)
4. 去背純白(輪廓 floodfill;開放邊自動找線稿末端封條)
5. 皮膚吸附真值輪廓(暖色+亮度判斷,3x3 位移平均補色)
6. 疊真值外輪廓線(60%)+骨骼層(45%,像素級精準,濃度可調不用重生成)
7. QC:數值統計 + 線稿疊圖,人工過目

## 用法

```bash
source ~/.zshrc   # 需要 REPLICATE_API_TOKEN
python3 pipeline.py plan                 # 檢視 19 張的 work_box 建議
python3 pipeline.py run 14_lower-leg-posterior          # 跑一張(花錢)
python3 pipeline.py run 02_hand-dorsal --reuse          # 沿用 cache 生成圖(不花錢)
python3 pipeline.py verify-points <marked.json> <final.png> [review.png]  # 先驗座標與輪廓
python3 pipeline.py points <marked.json> <final.png> <out.png>  # 驗證通過才疊穴位紅點(r=0.15)
```

設定在 `bases.json`:每張的 subject prompt、開放邊、work_box、參數覆寫。
產出:`output/<base>_final.png`;QC 在 `qc/`;生成快取在 `cache/`(重跑後製不用重新花錢)。

## 座標防呆

套皮圖的皮膚可有柔和質感，但不能改變穴位座標。`run` 若收到的 AI 圖比例與
`work_box` 相差超過 0.5%，會直接停止，不能再把它拉伸成原尺寸。

疊點前一律先跑 `verify-points`，或直接使用已內建驗證的 `points`。它會檢查：

1. marker JSON 的 `base_file`、SVG viewBox 與成圖尺寸一致。
2. 每一個穴點仍落在原始底圖的人體遮罩內。
3. 最終圖仍保留原始外輪廓至少 85%；尺寸剛好相同、但手勢不同的錯圖也會被拒絕。

若提供 `review.png`，會輸出青色輪廓與綠色十字的人工核對圖；這張圖只供 QC，
不可作為網站成品。

## 已知注意事項

- 帳號 credit < US$5 時 Replicate 限速 6 req/min,腳本會自動重試
- 07/08 頭部底圖:深色頭髮會撞 `fill_sum_min`(340)亮度下限,批次跑完視 QC 調參
- 18/19 骨骼圖底圖標記 skip,維持線稿
- 指尖類穴位(貼指甲角)驗收時特別看:柔和風格生成的指尖本來就有 ~8px 自由度,
  吸附已把輪廓鎖回真值,但指甲形狀是生成的
- 手腕/肢體截斷邊的皮膚邊緣偶有深棕色暈(生成圖自身邊緣陰影),放大才明顯,
  待批次 QC 時決定要不要再磨
