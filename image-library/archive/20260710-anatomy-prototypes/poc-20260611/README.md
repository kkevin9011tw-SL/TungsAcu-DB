# 穴位圖優化 PoC — 指駟馬穴（11.07）

2026-06-11 製作的三版示範圖，供顥軒挑選後續全面套用的風格。

## 成品

| 檔案 | 說明 |
|------|------|
| `指駟馬_A版_向量插畫.svg` / `.png` | 競品風格：向量手掌插畫（輪廓描自原書圖）＋ 淡化骨骼/伸指肌腱示意 ＋ 標註層 |
| `指駟馬_B版_書圖增強.svg` / `.png` | 原書圖增強照片當底（去噪、去原標記、銳化）＋ 同一套示意與標註疊層 |
| `指駟馬_C版_WHO線稿.svg` / `.png` | **WHO 標準經穴定位線稿當底**（手背觀＋全骨架透視）＋ 標註層 ＋ 食指第二節放大圈 |

PNG 為 2240px 高解析輸出（`qlmanage -t -s 2240`）。顥軒看過 A/B 後評為不可用；C 版採用
WHO 路線（同台灣中醫科普團隊做 LU10 魚際圖的方式）。

## C 版授權注意

底圖取自《WHO Standard Acupuncture Point Locations in the Western Pacific Region》(2008)，
IRIS：<https://iris.who.int/handle/10665/353407>。該書為 **WHO 傳統版權（非 CC）**，
版權頁明示歡迎申請重製授權。內部評估使用無虞；**公開上線前需向 WHO 西太平洋辦公室
（Manila）申請非商業教育用途的重製授權**。

## 標註層內容（兩版共用）

- 穴位紅點 ×3（理論四分點：遠端/近端指節橫紋間均分四等份）
- 中央線（金色虛線）與「外開二分」尺寸標註
- 遠端/近端指節橫紋虛線 ＋ 標籤（淡色光暈描邊，照片上仍可讀）
- 右側「四分點法」括線刻度
- 左側穴名框 ＋ 分散錨點引導線
- 11.07 編號帽徽、左下圖例

## 重建方式

依賴：

- `pip3 install --user --break-system-packages pymupdf pillow fonttools`
- macOS 內建字型（C 版文字外框化用）：`/System/Library/Fonts/STHeiti Light.ttc`、
  `STHeiti Medium.ttc`、`Supplemental/Songti.ttc`（text2path.py 引用，非 macOS 環境需改字型路徑）
- `who_acupoints.pdf` 不入版控，prepare_who_base.py 的 docstring 有下載 URL（WHO IRIS）

```bash
python3 build_poc.py          # A、B 版 SVG
python3 prepare_who_base.py   # 從 who_acupoints.pdf 抽乾淨手背線稿（向量手術）
python3 build_poc_c.py        # C 版 SVG（文字轉外框，需 fonttools＋上列字型）
qlmanage -t -s 2240 -o . *.svg   # SVG → PNG（macOS）
```

C 版管線：PDF p.168（TE3 圖）→ PyMuPDF SVG 匯出 → 刪文字 glyph / 紅灰標記 /
引導線 / 白色遮罩矩形 / 小字白色光暈 → 裁圖框 → 轉 180°（指尖朝上）→
`who_hand_dorsum_clean.svg`。錨點（食指 DIP/PIP 關節）由格線疊圖量測，
標註層全程式生成（`build_poc_c.py`），可批量套用到其他穴位。

## 素材與幾何

- 幾何錨點（DIP/PIP 橫紋、中央線、傾斜率）由程式自原書圖偵測，寫死在 `build_poc.py` 開頭，座標系為原圖 791×1044。
- `base_enhanced_2x.jpg`：原書圖經修補（移除原有黑點與紅鋸齒標記，迭代中值填補）→ 增強（去噪、色彩/對比/亮度、2x LANCZOS、銳化）。
- `hand_contour.json` / `hand_path.txt`：contourpy 抽出的手掌輪廓 → Douglas-Peucker 簡化 → Catmull-Rom 平滑貝茲路徑，A 版底圖用。
