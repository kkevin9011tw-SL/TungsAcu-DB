# 交班：董氏奇穴底圖套皮管線（給 Codex）

**日期**：2026-07-07
**狀態**：手背底圖（`02_hand-dorsal`）黃金樣本已驗證通過；其餘 16 張批次揭露三類問題待解。
**canonical repo**：`/Users/samue11in/Projects/TungsAcu-DB`
**工作目錄**：`assets/anatomy-prototypes/skin-pipeline/`

---

## 1. 任務目標

把 19 張 WHO 針灸線稿底圖（`../who-standard-bases-20260612/clean-bases/*.png`）換成「柔和寫實皮膚 + 保留骨骼透視」的版本，**且不動到既有的穴位標記 JSON**。董氏指穴靠指骨定位，不能把骨頭蓋掉，所以骨骼要半透明保留。

穴位標記真值在 `../../../marked-figures/`，每個穴一組 `穴號_穴名.json`，座標存**底圖 SVG viewBox 單位**。底圖換皮後尺寸與座標系必須跟原底圖**完全相同**，標記才能沿用。

---

## 2. 核心問題與解法原則（務必先懂這段）

**為什麼過去 AI 套皮穴點會飄**：標記座標綁在線稿那張圖的 viewBox。任何「叫 AI 重畫一張寫實手」都是產生**另一張沒有跟原圖對位（registration）的圖**，手指位置、比例、關節高度全變了，同一組像素座標貼上去就落在別的骨頭上。教材級失敗品在 `../../../marked-figures/一一部位/*套皮*.png`。

**解法三原則（不可違背）**：
1. **皮要鎖在原線稿的幾何上** —— 用 ControlNet（canny）把線稿當結構約束，生成的皮膚輪廓與線稿像素級一致。
2. **紅點永遠不進 AI** —— 由 Python 引擎在最後把 JSON 座標疊上去。
3. **骨骼由原 SVG 的向量骨骼層後製疊加**，不讓 AI 畫骨頭（AI 畫的骨頭永遠太重、位置不準，且是硬邊）。

---

## 3. 技術核心：手背黃金樣本的成功流程

程式在 `pipeline.py`，設定在 `bases.json`。指令：
```bash
source ~/.zshrc                          # 需要 REPLICATE_API_TOKEN
python3 pipeline.py plan [base]          # 檢視 work_box / FLUX bucket 建議
python3 pipeline.py run <base> [--reuse] # 跑單張;--reuse 沿用 cache 生成圖不花錢
python3 pipeline.py points <marked.json> <final.png> <out.png>  # 疊穴位紅點(r係數0.15)
```

完整流程（每張底圖一次，所有穴位共用）：

### Step 0 — 分離線稿的三層
`clean-bases` 的 PNG 是「外輪廓（黑）+ 骨骼（灰）」的線稿，viewBox×6 輸出（手部 1020×1440）。用灰階閾值切三層：
- **外輪廓+指甲線**：`v < 80` → 這是給 ControlNet 的控制圖，**骨頭線一定要去掉**，否則 AI 把骨頭當硬邊描出來、畫面銳利不自然。
- **骨骼層**：`80 ≤ v ≤ 248` → 後製疊回用。
- 這兩個閾值在 `bases.json` 的 `outline_thresh` / `bones_lo` / `bones_hi`。

### Step 1 — FLUX 比例預裁（work_box）
**關鍵坑**：`flux-canny-pro` 會把輸出改成它的原生 bucket 尺寸（32 倍數、約 1MP）。若控制圖長寬比不等於某個 bucket，出來會被拉伸 3-4%，穴點就偏。做法：把控制圖 pad/crop 到最接近的 bucket 比例（`suggest_work_box()` 會算），手背用 `work_box=[35,0,1020,1440]`（左裁 35px → 985×1440，比例對到 832×1216 bucket，誤差 <0.5%）。生成後再逆映射回原尺寸還原座標系。

### Step 2 — Replicate flux-canny-pro 生成皮膚
model `black-forest-labs/flux-canny-pro`，約 US$0.05/張。參數：`guidance=30, steps=50, seed=42, safety_tolerance=2`。
- **prompt 要點**：柔和寫實皮膚、`pure white background`、`acupuncture atlas style`、強調 soft/airbrushed 避免銳化。模板在 `bases.json` 的 `prompt_template`，`{subject}` 由各 base 填入。
- **限速**：帳號 credit < US$5 時 6 req/min，程式內建重試。
- **座標還原**：把生成圖 resize 回 work_box 尺寸，貼回原尺寸白底 canvas 的 `(box[0], box[1])`。
- 生成圖快取在 `cache/<base>_gen.png`，之後改後製參數用 `--reuse` 不用重花錢。

### Step 3 — 去背純白（floodfill）
從線稿重建「手區 interior mask」：線稿 `MinFilter(3)` 膨脹封髮絲縫 → 在開放邊（`open_sides`）畫封條 → 從影像四邊 floodfill 標記背景（值 128）→ interior = 非背景。背景區在最終圖強制刷白。
- **手背成功關鍵**：手只有「手腕」一個開放邊，封條畫在線稿末端（`rows.max()-2 ≈ y=1426`，注意不是 y=1439，線稿只畫到 1428，封條要封在線還在的高度否則洪水從手腕開口灌進去把整隻手刷白）。

### Step 4 — 皮膚吸附真值輪廓（snap）
柔和 prompt 天生讓生成的手指輪廓有 ~8px 自由度。用「真值輪廓 = 已知」的優勢把皮膚掰回去：
- 皮膚判斷：**暖色** `R-B > 12` **且亮度** `340 < sum < 740`（亮度下限排除 AI 沿輪廓畫的深棕色描邊渣，這是踩過的坑）。
- interior 內缺皮膚處：3×3 位移平均迭代補色（最多 30 輪 ≈ 補 30px），縫隙用鄰近膚色填。
- 手區外一律刷白。

### Step 5 — 疊真值外輪廓 + 骨骼層
- 外輪廓線（Step 0 的 `v<80`）以 **60%** 灰（`outline_alpha`）multiply 疊回，線條乾淨同源。
- 骨骼層（Step 0 的灰階）以 **45%**（`bone_alpha`，顥軒定案）multiply 疊回，**位置像素級精準**（就是原圖座標），濃度是參數，要調濃淡改數字重疊即可、不用重生成。
- 開放邊封條帶（含封條本身）刷白，比線稿截斷早 4px，不損解剖內容。

### Step 6 — 疊穴位紅點（驗收/出圖）
`cmd_points()`：讀 JSON，座標換算 `px=(x-viewbox原點)*6`，紅點半徑 `r = ann.r * 6 * 0.15`（**0.15 是顥軒定案值**），白描邊 + 紅點畫最上層。

### QC 產出
`qc/<base>_stats.json`（缺皮膚/溢出/補色輪數/未補像素）+ `qc/<base>_QC_line_over_final.png`（線稿疊成品的對位檢查圖）。

---

## 4. 目前狀態：批次揭露的三類問題（待解）

跑 `run_batch.sh` 對 16 張 pending 底圖批次，結果分三類：

| 類別 | 底圖 | 問題 | 修法方向 | 花費 |
|---|---|---|---|---|
| **A. 四肢皮膚被洗掉** | `04 前臂`、`06 後前臂`、`14 小腿後` | 生成成功但 interior mask 崩壞（實測前臂 interior 只剩 2.2%），皮膚幾乎全刷白 | **Step 3 的 floodfill 對「兩端開口 + 底部有手指縫」的四肢不 watertight**。手背成功是因單一開口、輪廓封閉。四肢頂/底兩開口高度不齊（前臂頂部左右緣起點差 ~50 列），單一水平封條蓋不住；底部手指縫造成多個外部入口。需改用穩健 interior 演算法（形態學閉運算補縫 / 只從真實 frame 角落 flood / 取最大外部連通域）。**可用 --reuse 免費重試** | 免費 |
| **B. 頭面五官對不上** | `07 正面頭`、`08 後頭` | AI 自己重畫一張臉，與線稿的眼鼻嘴內部線條錯位（正面頭出現雙重眼睛）；缺皮膚 127k-283k | 頭部線稿含**內部特徵線**，「只餵外輪廓」的策略不適用。需改：控制圖保留五官線 / 換方法 / 或直接跳過（董氏頭部穴少） | 需重生成 |
| **C. 安全過濾器擋掉（9 張）** | `03/05 上臂`、`10 背`、`11/12 足`、`13 小腿前`、`15/16 大腿`、`17 肩` | FLUX 把大面積裸露皮膚誤判裸體（E005）。**注意 `flux-canny-pro` 吃控制圖時 `safety_tolerance` 被強制鎖在最嚴格的 2，無法調寬** | 線索：9 張錯誤碼尾 ID 全相同 `(uIJ6l3ruRD)`，且胸腹（更敏感）反而過了、足部（不敏感）卻失敗 → 疑似部分為暫時性/系統性誤殺，值得先換 seed 重試。真的攻不下再換非 FLUX 的 ControlNet 模型（但品質參數要重調） | 重試 US$0.05-0.2/張 |

**優先級（顥軒的董氏穴集中在手/前臂/足/小腿）**：先修 A 類（免費）、再攻 C 類的足部與小腿，頭/背/軀幹低價值可緩。

---

## 5. 關鍵檔案

```
skin-pipeline/
  pipeline.py          # 主程式(6 步流程 + plan/run/points)
  bases.json           # 19 張各自的 subject/open_sides/work_box/參數覆寫
  run_batch.sh         # 批次跑 pending
  README.md            # 使用說明
  HANDOVER-codex.md    # 本檔
  cache/<base>_gen.png # FLUX 生成快取(改後製用 --reuse 不花錢)
  output/<base>_final.png  # 成品
  qc/                  # QC 疊圖與 stats
../who-standard-bases-20260612/clean-bases/*.{png,svg}  # 19 張線稿底圖
../skin-trial-20260703/   # 風格演進史(A-E 五版變體 + 決策過程)
../../../marked-figures/  # 穴位標記真值 JSON(套皮後全部沿用)
```

環境：`REPLICATE_API_TOKEN` 在 `~/.zshrc`（帳號 kkevin9011tw-SL，預付制）。相依：Pillow、numpy（無 scipy）。

## 6. 給 Codex 的第一件事

修 **A 類 interior mask**（最高價值 + 免費驗證）。建議做穩健版 `sealed_interior()`：不要依賴薄輪廓 watertight。可行方向 —— (1) 線稿二值化後大 kernel 形態學閉運算補縫；(2) flood 只從影像四角這種**保證是外部**的種子出發；(3) interior = 影像 − 最大外部連通域 − 輪廓。改完用 `python3 pipeline.py run 04_forearm-anterior --reuse` 驗證（cache 已有生成圖，零花費），QC 圖看皮膚是否完整回填、穴點是否對位。前臂穴位可用 `../../../marked-figures/` 對應穴號疊點驗收。
