TungsAcu-DB 董氏奇穴檢索工具
建立日期：2026-04-17
====================================================

【2026-07-10】圖庫資料夾整理：image-library 正式結構
====================================================

本輪目標：依使用者指定，先暫停圖像生成本身，改整理目前已產生的套皮／底圖素材位置，統一放到 `image-library/`，避免合格圖、來源圖與失敗實驗混在同一層。

已完成：
- 建立正式圖庫結構：
  - `image-library/production/`
  - `image-library/extracted_images/`
  - `image-library/marked-figures/`
  - `image-library/anatomy-sources/`
  - `image-library/experiments/`
  - `image-library/archive/`
- 將原 `extracted_images/` 移入 `image-library/extracted_images/`，不再另設 `book-extracted/`，避免分類過細。
- 將 topbar 印章 logo 改放 `image-library/logo-seal.png`；`image-library/extracted_images/` 繼續作為圖片審核中介資料夾。
- 將可重用來源圖移入 `image-library/anatomy-sources/`：
  - `hand-skeleton-palmar_CC-BY.png`（原 `指駟馬穴_手骨底圖_CC-BY.png`）
- 將目前使用者標為合格或可接受的底圖候選放到 `image-library/production/`：
  - `02_hand-dorsal_styleE_final.png`
  - `02_hand-dorsal_pipeline_final.png`
  - `04_forearm-anterior_final.png`
  - `14_lower-leg-posterior_final.png`
- 將人工穴位標定成果移到 `image-library/marked-figures/`。
- 將人工穴位標定工具移到 `image-library/marked-figures/marker-tool/`，保留其原 README 與資料檔。
- 將仍未正式驗收的套皮、表面圖、WHO 底圖流程移到 `image-library/experiments/anatomy-prototypes/`。
- 將舊 POC 與早期批次資料夾封存到 `image-library/archive/20260710-anatomy-prototypes/`，未刪除，以保留歷史輸出與可追溯性。
- 移除根目錄 `assets/`，目前圖庫不再以 `assets/` 作為入口。

注意事項：
- `production/` 目前只是人工驗收後的候選存放區，尚未接入 app 或批次製圖流程。
- 兩張 02 手背圖先保留為不同版本，尚未決定唯一 canonical。
- `image-library/anatomy-sources/hand-skeleton-palmar_CC-BY.png` 後續若公開使用，仍需補齊精確授權與 attribution。
- `image-library/extracted_images/` 作為書籍／PDF 擷取圖入口；目前沒有搬動 app 正在使用的 `data/images/`。

====================================================

【2026-07-10】WHO 01–19 套皮圖像批次：暫停於競品式表面圖／骨骼透視圖階段
====================================================

本輪目標：將 WHO 01–19 類底圖各產出一張競品式簡化表面圖，以及一張保留解剖線稿的骨骼透視圖；先不疊加穴位點與放大鏡。

已完成：
- 新增批次產生器：`image-library/experiments/anatomy-prototypes/surface-illustration-trials/2026-07-10/build_all_surface_layers.py`
- 目前批次輸出位置：
  `image-library/experiments/anatomy-prototypes/surface-illustration-trials/2026-07-10/all/`
- 已產出 01–19 共 19 組「表面圖／骨骼透視圖」，另有兩張總覽：
  - `01-19_表面圖總覽.png`
  - `01-19_骨骼透視圖總覽.png`
- 18、19 已納入表面上色與骨骼透視，不再只保留骨架底圖。
- 10 原清理底圖沒有可用骨骼像素；暫時加入手繪式脊柱、椎體、肩胛與肋骨線，僅作為失敗的驗證版本。

目前驗收結果與問題：
- 02 為目前唯一明確合格的實際套皮基準；04、06、14 的膚色質地曾達可接受程度。
- 03、05：目前手動封閉遮罩過寬，皮膚溢出 WHO 原輪廓太多。
- 07、08：目前雖已補成完整頭部色塊，但尚未取得使用者確認，仍列為待驗收。
- 15、16：目前遮罩過度簡化，已看不出自然的大腿外形，不能視為合格。
- 17：目前仍是過度簡化的肩部區塊，未達可用標準。
- 10：目前骨骼透視看起來像另外繪製的 AI／手繪骨架，不符合原 WHO 視角；後續必須以 18、19 的實際骨骼底圖做幾何對位與拼接，不能再自由繪製。
- 目前尚未進行穴位標記對位驗證；所有圖像只到「表面／透視層試作」階段。

暫停決策：
- 使用者要求暫停圖像部分，原因是各輪遮罩與視覺效果反覆，品質不穩定。
- 暫停期間不要再批次重跑、不要再調膚色參數，也不要把目前輸出視為正式底圖。
- 恢復時應先重新設計幾何策略，再做單張驗收；優先處理 10 的 18／19 骨骼對位，其次重建 03、05、15、16、17 的原輪廓，不沿用本輪過寬或過度簡化的手動多邊形。

====================================================

【給 Claude 的提示】
繼續這個專案時，請先讀這兩份文件再動手：

「我要繼續 TungsAcu-DB 專案，請先讀：
1. 工作日誌（時間線、決策脈絡）：
   /Users/samue11in/Projects/TungsAcu-DB/docs/WORKLOG.md
2. 當前架構 spec（檔案結構、schema、do/don't）：
   /Users/samue11in/Projects/TungsAcu-DB/docs/specs/TungsAcu-DB-current-spec.md」

重點：後端是 data/*.csv + data/notes/*.md + data/images/*.jpg。SQLite 已退役在 archive/，不要再接回來。

====================================================

【公開網址】
https://tungsacu-db-9fkdgtsgxtshtxxmnodl4i.streamlit.app/

【GitHub Repo】
https://github.com/kkevin9011tw-SL/TungsAcu-DB


====================================================
本機檔案位置
====================================================

專案資料夾（唯一正式開發 repo）：
/Users/samue11in/Projects/TungsAcu-DB/

SynologyDrive 內同名資料夾僅供歷史參考，不在該副本修改程式、資料或 spec。

主要檔案（CSV 後端版，2026-05-12 起）：
- app.py              網頁介面程式
- data_loader.py      pandas 查詢層（CSV/MD 統一讀取）
- data/穴位表.csv     234 穴主表
- data/對針表.csv     146 組對針（限《區位易象特效對針》）
- data/症狀治療.csv   5210 筆症狀-穴位推薦
- data/部位表.csv     13 部位
- data/images/        203 張穴位圖
- data/notes/         233 份每穴詳細筆記 md
- archive/            退役 SQLite 備份（不要再接回來）
- migrate_to_csv.py   一次性遷移腳本（從 archive/ DB 重產 data/）
- extract_images_v2.py 從 MinerU 輸出抽穴位圖
- requirements.txt    streamlit + pandas + opencc


====================================================
本機啟動 app（預覽用）
====================================================

在 Terminal 執行：

cd "/Users/samue11in/Projects/TungsAcu-DB"
NODE_OPTIONS="" streamlit run app.py --server.port 8519

開啟後在瀏覽器輸入：http://localhost:8519

※ NODE_OPTIONS="" 是為了清掉系統可能設定的 Node options，避免 Streamlit 子進程啟動異常。
※ 如果 8519 掛了，先確認沒有殘留進程（lsof -iTCP:8519 -sTCP:LISTEN），再用上面這行重啟即可。
（port 任選，習慣用 8519）


====================================================
修改後更新到公開網址
====================================================

【基本概念】
git 就像寄信：
- git add    → 把要上傳的檔案放進「信封」
- git commit → 把信封封起來，寫上說明
- git push   → 把信封寄出去（上傳到 GitHub）
GitHub 收到後，Streamlit Cloud 看到新版本，自動更新公開網址。

【不需要本機測試的情況】
直接修改 app.py → 執行下面三行 → 等 1-2 分鐘 → 公開網址自動更新

在 Terminal 執行以下指令（依序執行）：

cd "/Users/samue11in/Projects/TungsAcu-DB"

git add app.py data/ data_loader.py

git commit -m "更新說明（可改成本次修改的描述）"

git push

執行完畢後，Streamlit Cloud 會自動偵測並重新部署，約 1-2 分鐘後公開網址生效。

【需要本機測試的情況】
修改資料庫（.db 檔）時，建議先在本機確認資料正確再 push。
本機啟動方式見上方「本機啟動 app」章節。


====================================================
GitHub 登入說明
====================================================

- 帳號：kkevin9011tw-SL
- 密碼：使用 Personal Access Token（不是 Google 密碼）
- Token 位置：GitHub → Settings → Developer settings → Personal access tokens
- 若 Token 過期，需重新產生並勾選 repo 權限


====================================================
資料庫架構
====================================================

【資料庫建立流程】

1. PDF 轉文字（ocr_pdf.py）
   - 使用 Apple Vision OCR（macOS 內建，M4 Max GPU 加速）
   - 輸出：ocr_output/<書名>_full.txt（每頁用 === 分隔）

2. 解析文字並存入資料庫（parse_dongzhen.py）
   - 針對《穴位詮釋解》書籍格式，用 regex 逐穴解析
   - 簡體→繁體轉換（opencc）
   - 輸出：dongzhen_new.db

3. 補充頁碼（add_page_numbers.py）
   - 補入書本原始頁碼，方便對照實體書

4. 提取穴位圖片（extract_images.py，規劃中）
   - 用 PyMuPDF 從 PDF 提取圖片
   - 主要：用圖號（如 图1-1）比對穴位
   - 備援：用頁碼找最近穴位
   - 用 Claude Vision API 生成中文描述
   - 圖片轉 base64 存入 acupoint_images 資料表

【資料庫表格說明】

dongzhen_new.db：
- regions        部位（一一部位～增補，共 13 個）
- acupoints      穴位（196 個，含董師原文＋詮解發揮各欄位）
- acupoint_images 穴位圖片（base64 圖片 + Claude Vision 描述）

dongshi.db：
- 對針組合、症狀主治（來自楊維傑其他著作）

【設計文件】
詳細架構：docs/archive/specs/2026-04-19-image-extraction-design.md


====================================================
建立日誌
====================================================

【2026-04-17】初版建立
- 建立 SQLite 資料庫（dongzhen_new.db），196 個董氏奇穴
- 用 Apple Vision OCR（ocr_pdf.py）將《穴位詮釋解》PDF 轉文字
- 用 parse_dongzhen.py 解析 OCR 文字，抽取各穴位欄位存入 DB
- 建立 Streamlit 網頁介面（app.py），部署至 Streamlit Cloud
- 建立補充資料庫（dongshi.db），含對針組合與症狀主治
- 部署至 GitHub + Streamlit Cloud 自動更新

【2026-04-19】新增穴位圖功能
- 新增 extract_images.py：從 PDF 提取穴位圖，本機 Ollama gemma4 視覺模型描述圖片
- DB schema 升級：acupoint_images 表新增 image_data（base64）、figure_ref、match_method 欄位
- app.py 新增「🖼 穴位圖」tab，讀取 base64 圖片在穴位詳情頁顯示
- 在 samuelmac81 電腦初始化 git repo，連結 GitHub 遠端

【2026-04-20】完成部署、清除錯誤圖片
- 修正 extract_images.py 圖片壓縮邏輯（JPEG quality=75, max 800px）
- 解決 git 歷史大檔案問題（reset --soft + force push），DB 約 5.9 MB
- Streamlit Cloud 部署成功，🖼 穴位圖 tab 上線
- 測試發現 3 張圖片全為頁碼比對（誤判穴位），已清除
- 目前 acupoint_images 為空，待正式跑全書提取

【環境與技術清單】

| 技術/工具 | 用途 | 版本/備註 |
|-----------|------|-----------|
| Python | 執行所有腳本 | 3.11（/opt/homebrew/bin/python3.11） |
| PyMuPDF（fitz） | 從 PDF 提取圖片 | pip install pymupdf |
| ocrmac | Apple Vision OCR | macOS 專用，M 系列 GPU 加速 |
| opencc-python-reimplemented | 簡體→繁體轉換 | pip install opencc-python-reimplemented |
| Ollama + gemma4:26b | 穴位圖視覺描述（本機，免費） | ollama pull gemma4:26b |
| SQLite | 資料庫 | 內建於 Python |
| Streamlit | 網頁介面 | pip install streamlit |
| Git + GitHub | 版本控制與部署觸發 | repo: kkevin9011tw-SL/TungsAcu-DB |
| Streamlit Cloud | 免費公開部署 | 連結 GitHub 自動更新 |

【複製到新環境的步驟】
1. 安裝 Python 3.11（Homebrew）
2. clone GitHub repo：git clone https://github.com/kkevin9011tw-SL/TungsAcu-DB.git
3. 安裝套件：pip install streamlit opencc-python-reimplemented pymupdf Pillow
4. 安裝 Ollama 並拉取視覺模型：ollama pull gemma4:26b
5. 執行 app.py 本機測試，或直接 push 觸發 Streamlit Cloud 更新


====================================================
工作日誌（復盤用）
====================================================

【2026-04-19】資料審計 + 後台編輯模式

─── 背景與動機 ───

找到一份 Gemini 擬的「董氏奇穴智慧系統建立大綱 V4.0」，架構比目前的 app 理想許多。
主要差距在：資料分層（四層書籍整合）、原理欄位結構化、後台可編輯、對針分級顯示。
決策：不換框架（Streamlit 維持），用漸進式優化取代全部重寫。理由是工程量差太多，且現有 196 穴的資料結構已足夠好。

─── 今日完成 ───

1. 資料完整性審計
   - 直接用 Python 對 dongzhen_new.db 跑 SQL，統計各欄位填充率
   - 發現嚴重缺口：
     * 比較（comparison_text）：99% 空白（194/196 筆）
     * 引申（extension_text）：88% 空白（173/196 筆）
     * 穴名闡釋（name_explanation）：80% 空白（156/196 筆）
     * 董師原文-注意（dong_caution）：83% 空白（162/196 筆）
     * 維傑新用（new_applications）：42% 空白（83/196 筆）
   - 這些欄位正好是 Gemini 大綱最重視的內容，也是未來要優先填入的方向

2. 後台編輯模式（Admin Mode）
   - 在 app.py 加入密碼保護的管理員登入（sidebar 最下方）
   - 登入後穴位詳情頁多出「✏️ 編輯資料」tab
   - 支援直接修改 12 個欄位，儲存後即時寫回 SQLite 並清除快取
   - 密碼存放位置：
     * 本機：董氏-rag/.streamlit/secrets.toml（已加入 .gitignore，不會上傳）
     * 公開網站：Streamlit Cloud → Settings → Secrets

─── 遇到的問題與解法 ───

問題 1：Google Docs API 未啟用
- 試圖用 google-workspace MCP 讀取 Google Doc，但 API 被禁用（403）
- 改用 firecrawl scrape 工具，成功讀出文件內容

問題 2：git push 認證失效
- 舊 Token 存在 macOS 鑰匙圈但過期，Claude Code 終端無法互動輸入帳密
- 解法：把 PAT 嵌入 remote URL（git remote set-url origin https://TOKEN@github.com/...）
- 注意：Token 不能貼在 AI 對話裡（有外洩兩個 token，已撤銷）
- 建議未來：產新 token 後直接在自己的 Terminal 跑 set-url，不要複製貼上到聊天視窗

問題 3：git rebase 衝突
- 遠端比本機多了幾個 commit，pull --rebase 時本機有未提交改動又有未追蹤檔案
- 過程：stash → clean 衝突檔 → pull --rebase → 解衝突 → rebase --continue → push
- 衝突原因：遠端的 app.py 和我們改的 app.py 在同一段有不同版本

─── 下一步規劃 ───

優先順序（已確認）：
1. Phase 3：從 ocr_output/ 的 OCR 文字自動提取缺失欄位（打底）
2. Phase 2（後台）：用管理員介面手動校對 OCR 提取結果
3. Phase 4：對針對穴分級（在 dongshi.db 的 1,276 筆加上針數標記）
4. Phase 5：診間醫案筆記 CRUD

─── 對未來類似專案的啟示 ───

- OCR → 結構化資料 → Streamlit 這個流程很順，適合沒有後端工程師的個人專案
- SQLite 放在 git repo 裡是可行的（只要不超過 100MB），方便部署到 Streamlit Cloud
- 後台編輯介面應該在一開始就做，不然補資料很痛苦
- Token 安全：設定好 osxkeychain 或 SSH 金鑰，避免每次要重設

【2026-04-20】完成圖片提取功能並部署上線

─── 背景與動機 ───

延續 4/19 的穴位圖功能建置。前一段 session 已完成 extract_images.py 撰寫、DB schema 升級、app.py 新增圖片 tab，以及在 samuelmac81 桌電初始化 git repo。
本次 session 的目標是解決遺留的 git 歷史問題（舊 commit 有 215 MB 未壓縮 DB），清理後推上 GitHub，讓 Streamlit Cloud 完成部署。

─── 今日完成 ───

1. 修復 extract_images.py 的圖片壓縮邏輯
   - 上次 session 的版本被 linter 還原成 PNG 格式（每張 1.5-2 MB）
   - 修正為：max 800px 寬度縮放 + JPEG quality=75 壓縮，大幅降低 DB 體積

2. 完成 git 歷史清理並 force push
   - 原因：215 MB 的大 DB commit 導致無法 push 到 GitHub（100 MB 限制）
   - 解法：git reset --soft 65421bc → 回到初始 commit 但保留所有工作目錄改動
   - 重新 commit 所有檔案（app.py、dongzhen_new.db、extract_images.py、migrate_add_image_data.py、requirements.txt）
   - 使用者在自己的 Terminal 執行 force push，成功上傳（DB 約 5.9 MB）

3. 驗證 Streamlit Cloud 部署
   - Push 後 Streamlit Cloud 自動重新部署
   - 🖼 穴位圖 tab 成功出現在公開網站
   - 圖片未顯示問題：原因是 Streamlit cache 殘留，透過 Reboot app 解決
   - 確認圖片可正常顯示

4. 發現圖片比對問題並清除錯誤資料
   - 資料庫中的 3 張圖全為頁碼比對（match_method='page_number'），精確度不足
   - 驗證後確認圖片與穴位不符（例如：存入心膝穴的圖實為三眼穴的說明圖）
   - 執行 DELETE 清除 acupoint_images 所有筆數，還原乾淨狀態

─── 遇到的問題與解法 ───

問題 1：git rebase 多次失敗
- 前一 session 嘗試 rebase --onto 移除大 commit，因 binary 檔案衝突多次卡住
- 本 session 改用 git reset --soft 直接回退到初始 commit，再重新 commit 一次
- 教訓：binary 檔案（.db）不適合做 rebase/cherry-pick，遇到衝突直接 reset + 重 commit 最省事

問題 2：🖼 穴位圖顯示空白（Streamlit cache 問題）
- 新部署後 load_acupoint_images 有 @st.cache_data，推測快取了舊的空結果
- 透過 Streamlit Cloud 控制台 → Reboot app 清除快取後恢復正常

問題 3：桌電與筆電同時修改 DB
- 發現兩台電腦在本次 session 結束時同步衝突風險
- 暫停後續操作，待釐清兩台 DB 版本差異後再繼續

─── 下一步規劃 ───

1. 解決多電腦 DB 衝突：確認桌電與筆電的 DB 版本，以正確版本為準後再繼續
2. 正式跑全書圖片提取：需提供 PDF 路徑，搭配 OCR 文字檔做圖號比對（避免頁碼比對的誤差）
3. 確認 extract_images.py 使用 figure_ref 比對為主、頁碼比對為輔的邏輯有正確觸發

─── 對未來類似專案的啟示 ───

- 多電腦共用同一個 SQLite DB 時，要有明確的「以哪台為主」原則，Synology Drive 同步不能取代版本控制
- git force push 前務必確認 DB 大小在 100 MB 以內（用 ls -lh 檢查）
- Streamlit Cloud 有快取問題時，直接 Reboot app 是最快解法，不需要重新 push

【2026-04-21】跨機器衝突排查 + Bug 修復（筆電 samue11in）

─── 背景與動機 ───

延續 4/19 在筆電做的後台編輯模式，此時桌電（samuelmac81）已在 4/20 完成圖片功能並 push。
筆電發現網站有三個問題需要排查，同時發現兩台電腦曾同時編輯 DB，需確認有無衝突。

─── 今日完成 ───

1. 網站 Bug 排查
   - 問題一（頁碼消失）：確認正常，頁碼顯示邏輯沒有問題
   - 問題二（Tab 錯誤）：根本原因是 Streamlit Cloud 的 DB 缺少 image_data/figure_ref 欄位
     → acupoint_images schema 升級（migrate_add_image_data.py）在桌電本機跑過，但 DB 沒有 commit
     → 透過 Synology Drive 同步，筆電本機已有正確 schema，但 GitHub 沒有
     → 修法：在 load_acupoint_images 加 try/except，並 commit 更新後的 DB
   - 問題三（穴位圖空白）：正常，acupoint_images 目前 0 筆，需跑提取腳本才有圖片

2. 跨機器衝突確認
   - 確認兩台電腦沒有 git 衝突，原因是所有改動都在同一個 Synology Drive 同步資料夾
   - 桌電改的 extract_images.py（JPEG 壓縮邏輯）透過 Synology Drive 自動同步到筆電，
     呈現為筆電本機的「未提交改動」
   - 一次 commit 三個檔案（app.py、extract_images.py、dongzhen_new.db）一起 push 解決

3. 資料欄位調查
   - 查詢各書籍在 dongshi.db 的頁碼填充率
   - 有頁碼的書籍：《常見病特效一針療法》（70%）、《痛證特效一針療法》（62-92%）
   - 其餘書籍（含《區位易象對針》、《針灸五輸穴》等）頁碼全空

─── 遇到的問題與解法 ───

問題：push 被拒（remote contains work you do not have locally）
- 原因：桌電在 4/20 有 force push，改寫了部分 git 歷史，筆電的 remote tracking 過時
- 解法：git pull --rebase（自動 rebase 到新 history）後再 push 成功
- 補充：git log 會出現兩筆 WIP stash commit（ff45dd4、2a96ebf），是之前 stash 留下的紀錄，不影響功能

─── 下一步規劃 ───

1. 正式跑全書圖片提取（需在桌電 samuelmac81 執行，因為有 Ollama）
2. Phase 3：從 OCR 文字自動提取缺失欄位（穴名闡釋、比較、引申等）
3. 管理員密碼更新至 Streamlit Cloud Secrets（目前預設 admin123）

─── 對未來類似專案的啟示 ───

- Synology Drive 同步 + git 混用時，要意識到「檔案改了但 git 不知道」的盲點
- 多台電腦的工作日誌要標明是哪台執行，方便追溯
- push 前先跑 git status 確認哪些檔案有未提交改動，避免漏掉重要更新

【2026-04-29】Part2~4 穴位資料解析與匯入

─── 背景與動機 ───

延續 4/21 的工作。MinerU OCR 已完成全書四個 part 的輸出同步，本次目標是解析 part2~4 的穴位資料、填入 acupoints.csv，再匯入 dongzhen_new.db。
因顥軒使用 Claude Pro 訂閱而非 API Key，改用純 regex 解析方案取代原本的 LLM 呼叫腳本。

─── 今日完成 ───

1. 調查 OCR 結構
   - Part1：41 穴（一一手指部）、Part2：79 穴（三三~七七）、Part3：91 穴（八八~一二）、Part4：3 穴（增補）
   - 穴位標題格式：`# 穴名(图N-X)`，兩種段落格式：
     * 標準格式（Part2-3）：含【董師原文】+【詮解發揮】區塊
     * 增補格式（Part4）：穴名釋義+定位及取穴+維傑經驗主治+解說及發揮

2. 撰寫 parse_ocr_regex.py（純 regex，無需 API Key）
   - 欄位提取邏輯：部位（圖號→部位代碼）、取穴（部位+取穴+手術+運用合併）、主治關鍵字（分詞）、董楊思維（維傑新用+解說及發揮前兩點）、備註（禁忌字串比對）
   - 支援斷點續跑、多 part 批次處理
   - 跑完：41（Part1 已有）+ 165（Part2-4 新增）= 206 穴

3. 撰寫 convert_to_traditional.py（簡繁轉換）
   - 使用 opencc s2twp（台灣繁體＋慣用詞）
   - 偵測到 201 穴含簡體字元，轉換後統一為繁體
   - Part1 原有繁體 5 穴自動略過

4. 撰寫 import_csv_to_db.py（CSV → dongzhen_new.db）
   - 168 筆重疊穴位：更新 indications_kw（全覆蓋）+ new_applications（只填空白）
   - 38 筆 CSV 獨有穴位：INSERT 新列，region_id 由部位文字推算
   - 結果：DB 從 195 穴擴充至 234 穴，indications_kw 填充率 88%

5. git commit dongzhen_new.db（待 push，與 UI 調整一起送出）

─── 發現的資料問題 ───

- DB 有 27 筆 OCR 殘留錯誤名稱（如「圖4-4 首英穴」、「。耳背穴」），已保留不動，待後續手動清理
- CSV 獨有 vs DB 獨有有些是同穴異名（如「中九穴」vs「中九里穴」），未合併
- 部分董楊思維欄位只有維傑新用，解說及發揮深層詮釋需後續用管理員介面補充

─── 新增腳本清單（位於 data/ 資料夾）───

| 腳本 | 用途 |
|------|------|
| parse_ocr_regex.py | OCR → acupoints.csv（純 regex，不需 API） |
| parse_ocr_to_csv.py | OCR → acupoints.csv（Claude API 版，保留備用） |
| convert_to_traditional.py | 簡體→繁體批次轉換（opencc s2twp） |
| import_csv_to_db.py | acupoints.csv → dongzhen_new.db 匯入 |

─── 下一步規劃 ───

1. UI 調整（本次 session 繼續）：調整 app.py 顯示邏輯後再 push
2. 清理 DB 中的 OCR 殘留錯誤名稱（27 筆）
3. 手動補充董楊思維欄位（用管理員介面）

─── 對未來類似專案的啟示 ───

- 沒有 API Key 時，pure regex 解析結構化 OCR 文字效果出乎意料地好
- opencc s2twp 轉台灣繁體優於 s2t（多轉換慣用詞，如「軟體」→「軟體」、「組件」→「元件」）
- CSV 作為中間格式很有用：可獨立編輯、版本控制、也方便匯入不同 DB schema

【2026-04-29 續】UI 改版進行中（本機測試階段，尚未 push）

─── 已完成 ───

1. app.py 完整重寫（ZaraLcy 宣紙硃砂風格）
   - CSS 注入改為 _inject_css() 函式 + @import（修正舊版 <link> 導致 CSS 渲染成文字的 bug）
   - session_state.mode key 衝突修正：改用 mode_idx + _pending_mode pending 機制
   - 穴名放大至 2.4em，Noto Serif TC 加粗
   - Sidebar：深色 header bar（仿 ZaraLcy）、橫向部位 pills、穴位清單
   - 詳情面板：圓形穴號徽章、section-label 分隔、主治關鍵字可點擊跳症狀
   - 首頁：13 部位卡片 grid
   - .streamlit/config.toml：強制宣紙淺色主題

2. DB 更新（已 commit，待 push）
   - dongzhen_new.db 從 195 穴擴充至 234 穴（新增 part2~4 解析結果）

─── 待辦（下次繼續）───

【P0 Bug / 體驗問題】
1. Header 滿版問題
   - 現況：header bar 只在 sidebar 寬度內，右側主區域沒有
   - 解法：用 CSS position:fixed + z-index 覆蓋全寬，或在 main() 頂部另外渲染一個 HTML header
   - 需加深到更飽和的硃砂紅（目前 #8B3A2A，建議改 #7B2D1E 或 #6B2A1A）

2. Sidebar 收折按鈕問題
   - 現況：Streamlit 預設有 collapse 按鈕，不小心按到後叫不回來
   - 解法：用 CSS 隱藏 [data-testid="collapsedControl"] 及 [data-testid="stSidebarCollapseButton"]

3. 症狀 & 對針模式沒有預設清單
   - 現況：搜尋框下方空白，需輸入才有結果
   - 需求：
     * 症狀模式：預設顯示症狀清單，依「頭→腳」身體順序排列
       排列原則：頭面、眼耳鼻喉、頸肩、上肢、胸背、腰腹、下肢（膝踝）、生殖泌尿
     * 對針模式：預設顯示對針列表，依筆畫排列
       （從 dongshi.db acupoint_pairs 表抓不重複的 point1+point2 組合）
   - 這兩個清單可以用 st.sidebar 顯示，點選後帶入搜尋

─── 技術筆記 ───

Streamlit CSS 關鍵 selector：
- 隱藏收折按鈕：[data-testid="stSidebarCollapseButton"] { display:none !important }
- 隱藏已收折的展開控制：[data-testid="collapsedControl"] { display:none !important }
- 全寬 fixed header：position:fixed; top:0; left:0; right:0; z-index:999
  （要同時加 main area padding-top 避免內容被蓋住）

─── Git 狀態 ───

共 4 個 commit 在本機，尚未 push：
1. Part2-4 穴位資料（dongzhen_new.db）
2. .streamlit/config.toml（宣紙主題）
3. UI 改版第一版（CSS 顯示成文字的版本）
4. UI 改版第二版（本機測試版，目前這個）

下次 push 前先在本機確認 P0 問題都修好。

─── Codex 交辦的問題 ───

嘗試用 Codex CLI 交辦 UI 任務，發現：
- Codex CLI 預設模型是 gpt-5.5，需要 OpenAI API Key（開發者帳號，按量付費）
- ChatGPT Plus/Pro 訂閱帳號「不支援」這個模型，會報 400 錯誤
- 兩者是不同產品：ChatGPT 訂閱 ≠ OpenAI API Key
- 結論：Codex CLI 目前對顥軒不可用，UI 續修請直接開新 Claude Code session

─── 給下次 Claude 的提示 ───

繼續這個專案時：
1. 先讀這份日誌
2. app.py 位於 董氏-rag/app.py，本機測試後再 push
3. 三個 P0 問題按順序修，每修完一個先在本機確認
4. DB 的 commit 已在 git history，push 時會一起送出（git log 可確認）
5. 還原指令：git checkout HEAD app.py（若改壞）

【2026-04-29 續（二）】Codex 執行 UI P0 修正（本機測試完成，尚未 push）

─── 執行者 ───

- 本段修改與測試由 Codex 執行

─── 已完成 ───

1. Header 滿版與色彩修正
   - 嘗試兩種作法：先用 main() 內 fixed topbar，後改為覆寫 Streamlit 原生 stHeader
   - 硃砂紅加深為 #7B2D1E，並加上右上角「234 穴」徽章
   - 提高 z-index，避免 header 被 sidebar 蓋住

2. 隱藏 sidebar 收折按鈕
   - 已用 CSS 隱藏 [data-testid="stSidebarCollapseButton"]
   - 已用 CSS 隱藏 [data-testid="collapsedControl"]

3. 症狀模式預設清單
   - 從 dongzhen_new.db 的 indications_kw 拆出預設症狀
   - 依頭面、眼耳鼻喉、頸肩、上肢、胸背、腰腹、下肢、生殖泌尿、其他分組
   - 原先做成大量 button，後改為「分組預覽 + selectbox」以避免 Streamlit/本機 Python 閃退
   - 點選預設症狀後可正常帶入查詢結果

4. 對針模式預設清單
   - 從 dongshi.db 的 acupoint_pairs 抓不重複 point1+point2 組合
   - 原先嘗試簡繁正規化與 locale 排序，疑似觸發本機 Python process crash
   - 已改回純 Python 穩定版本，先以字串排序顯示預設清單
   - 點選預設對針後可顯示內容，並新增「← 返回對針清單」按鈕

─── 除錯過程 ───

- 先發現 Streamlit 1.56 對空 label 更嚴格，已將 selectbox/text_input 改成有 label + label_visibility="collapsed"
- 症狀模式初版會直接修改 st.session_state.search_kw，導致：
  streamlit.errors.StreamlitAPIException: st.session_state.search_kw cannot be modified after the widget with key search_kw is instantiated.
- 已改為用 _set_search_kw / _set_pending_pair 暫存，於 widget 建立前套用，問題排除
- OpenCC + locale.strxfrm 版本在切換症狀/對針時曾出現 macOS「Python 未預期結束」，目前已移除這條路徑

─── 本機測試 ───

- 多次執行 streamlit run app.py 測試
- 曾使用測試埠：8511、8512、8513
- 最後穩定測試版本執行於 8513
- 目前確認：
  * 穴位模式正常
  * 症狀模式可開啟、可選預設症狀、可顯示結果
  * 對針模式可選預設對針、可顯示結果、可返回清單

─── 尚可後續優化 ───

- Header 雖已可覆蓋全寬，但實作仍偏 CSS hack；若下次再調整版面，可考慮改成更獨立的自訂 topbar 容器
- 對針目前不是嚴格筆畫排序，只是先以穩定為優先保留字串排序
- 症狀預設清單目前共 585 項，若後續覺得過長，可再加二級分類或搜尋過濾

【2026-05-09】UI 收斂 + 穴位圖功能 + 對針規則一致化

─── 背景與動機 ───

延續 4/29 的本機測試版。要把 UI 收斂到 8519 版的基準，加上穴位圖功能，並修正一個長期存在的資料不一致問題：對針模式左側搜尋會撈到《常見病》《痛症》的條目，但詳情頁的對針區只顯示《區位易象特效對針》，前後台規則不一。

─── 完成事項 ───

1. UI 視覺密度修正（不動 tab 名稱、順序）
   - 詳情頁三 tab 固定為：取穴定位 / 主治原理 / 臨床配伍
   - section-body 加 margin-bottom 14px，多段不再黏成一塊
   - section-label 拿掉 uppercase、margin 加大
   - needle-card、src-block padding/margin 加大
   - Tab 1「原理與發揮」加小標籤分四段：董楊思維／解說發揮／比較／引申
   - 主治關鍵字固定 4 欄按鈕
   - Tab 0 取穴定位左右分欄：左位置+針法、右穴位圖（width=320）

2. 自訂全寬 topbar
   - 蓋掉 Streamlit 預設 stHeader，硃砂底色 + 印章 logo（assets/logo-seal.png，rotate 90deg）
   - 中文大標 + 英文副標、右側「234 穴」徽章

3. 切換 toggle 自動清空搜尋
   - render_sidebar 偵測 _prev_mode_idx 變動，pop search_kw / pending 並 rerun

4. 對針規則一致化（修長期 bug）
   - 左側搜尋、左側預設清單、詳情頁對針區三處全部限定《區位易象特效對針》
   - dongshi.db 簡繁混雜：opencc s2twp 在顯示處統一轉繁
   - 搜尋雙向相容：使用者輸入繁體用 tw2sp 轉成簡體再 LIKE 雙查
   - 預設清單排序 key 用轉換後的繁體第一字筆畫

5. 穴位圖功能（重做 v2）
   - 棄用舊 PyMuPDF + 頁碼配對流程（誤把整頁當穴位圖、配錯穴位）
   - 改用 MinerU content_list.json：4 個 part 共 531 張預切 figure
   - bbox 過濾（寬高 < 60px、極端寬高比剔除），剩 275 張
   - 比對策略：caption「图N-X」→ DB.figure_ref 精確命中 188 張、caption 穴名命中 39 張、同頁回退 fallback 24 張、其餘 noref 24 張
   - admin sidebar 加「🖼 圖片審核」介面：過濾來源、6 張/頁、採用/跳過/重置三鈕
   - 顥軒人工審完 275 張，採用 203 張，2 張錯誤（1 張穴名錯：木鬥→木斗已修；1 張圖錯先跳過）
   - 圖片 base64 嵌入 dongzhen_new.db.acupoint_images.image_data

6. FOUC 緩解
   - show_detail 加 @st.fragment，內部互動只重跑詳情區
   - 「返回」按鈕改顯式 st.rerun() 觸發全頁 rerun
   - 合併連續 HTML 區塊為單次 st.markdown，減少 hydration race

─── 遇到的問題與解法 ───

問題 1：PDF 是整頁掃描，PyMuPDF get_images 每頁只吐一張且 >= 70% 頁面
- 解法：改用 MinerU 預切的 figure，已切好且帶 caption，bypass 整頁掃描問題

問題 2：木鬥穴 v.s. 木斗穴
- 原 DB（acupoints.name）是「木鬥穴」，但圖片來源與 dongshi.db 用「木斗穴」
- 解法：UPDATE 改回「木斗穴」（id=74）

問題 3：簡繁混雜
- dongshi.db 沒做過 s2twp，pair 出現「妇科穴 ✦ 還巢穴」（治療不孕症，來自《常見病》，不該在對針模式）
- 解法：顯示處 t() 統一轉繁；對針模式 source 限定區位易象

─── Git 歷史 ───

- 43fbce4 新增穴位圖功能 + UI 密度修正 + 對針規則一致化
- 2272a71 詳情頁右側放穴位圖 + FOUC 緩解

【2026-05-12】CSV/MD/JPG 後端正式取代 SQLite（依 4/27、4/28 兩份 spec 重構）

─── 背景與動機 ───

顥軒長期願望：後端用 CSV/Excel，前端只負責讀。理由是想修細部資料時可以直接打開 Numbers 改某一欄某一列，不必進 admin tab 也不必懂 SQL。
4/27、4/28 兩份 spec 把這個設計寫完整了，但之前沒實作。這次 session 從匯出→改寫→管理介面升級→退役 SQLite，四階段一氣呵成。

─── 完成事項 ───

Phase 1：匯出（migrate_to_csv.py）
- 從 dongzhen_new.db + dongshi.db 一次性產出：
  * data/穴位表.csv（234 列 × 13 欄）
  * data/對針表.csv（146 列，限《區位易象特效對針》）
  * data/症狀治療.csv（5210 列）
  * data/部位表.csv（13 列）
  * data/images/{穴號}_{穴名}.jpg（203 張，從 base64 解碼）
  * data/notes/{穴名}.md（233 份，董師原文+詮解發揮長文）
- 設計原則：短欄位（Excel 友善）走 CSV，長文走 MD

Phase 2：app.py 改吃 CSV
- 新增 data_loader.py：pandas + @st.cache_data 統一查詢層
- app.py 從 1240 行縮到 800 行，所有 SQL 換 DataFrame filter
- 詳情頁 Tab 0 加「📜 詳細筆記」expander 展示 md 全文
- Tab 1 原理區塊改從 md 抽 ### 段落（維傑新用/解說發揮/比較/引申/穴名闡釋）
- requirements.txt 加 pandas>=2.0
- 踩坑：Streamlit 1.30+ 不會自動把 script 目錄加進 sys.path，要手動 sys.path.insert（不然 import data_loader 會 ModuleNotFoundError）
- 踩坑：SynologyDrive 路徑下 Streamlit 檔案監看不可靠，改動後常需手動重啟才生效

Phase 3：admin 編輯升級
- sidebar 加「➕ 新增穴位」按鈕 → 表單頁 → 填必填欄位 → 直接跳到該穴詳情
- 詳情編輯 tab 底部加「危險區」段：勾選確認後才能刪除整列穴位（連帶刪 notes/ md）
- data_loader 新增 create_acupoint_row() / delete_acupoint_row() helper

Phase 4：SQLite 退役 + push 上 Cloud
- dongzhen_new.db、dongshi.db 用 git mv 搬到 archive/
- archive/README.md 說明來龍去脈
- migrate_to_csv.py 路徑指向 archive/ 為主、上層為 fallback
- 一次 commit 450 個檔案（CSV/MD/JPG + 程式碼異動）、推上 GitHub
- Streamlit Cloud 自動部署

─── 給下次接手者的提示 ───

正式編輯入口已變成「直接改 data/*.csv」：
1. 小欄位（取穴、針法、主治關鍵字、董楊思維、備註、頁碼、穴位圖路徑）→ Numbers 打開 data/穴位表.csv 改
2. 長文（董師原文、解說發揮、比較、引申）→ CotEditor 打開 data/notes/{穴名}.md 改
3. 新增/刪除穴位→ CSV 加列/刪列，或 admin sidebar/詳情頁按鈕
4. 改完上線→ git add data/ && commit && push

詳細架構見：docs/specs/TungsAcu-DB-current-spec.md

不要再回去動 archive/*.db，那是歷史快照。

─── Git 歷史 ───

- d40f729 Phase 4: SQLite 退役，CSV/MD/JPG 成為正式後端

====================================================
資料來源
====================================================

主資料庫（穴位詮釋解）：
- 楊維傑醫師《董氏奇穴穴位詮釋解》，人民衛生出版社 2018 年版

補充資料庫（其他著作）：
- 楊維傑-楊維傑區位易象特效對針
- 楊維傑-楊維傑常見病特效一針療法
- 楊維傑-楊維傑痛證特效一針療法
- 楊維傑-楊維傑針灸五輸穴應用發揮
- 楊維傑-董氏奇穴原理結構
- 楊維傑-董氏奇穴治療析要

====================================================
【2026-05-30】前端樣式穩定性待辦
====================================================

背景：
- 久未啟動後，8519 本地版與目前 Streamlit 顯示出現樣式差異。
- 主要問題不是資料或 app 啟動失敗，而是部分 Streamlit 元件樣式漂移：
  * 搜尋框在 8519 截圖中變灰底、黑框，疑似吃到深色/預設狀態。
  * 「瀏覽」按鈕在 8519 截圖中變黑底深字，對比不足。
  * streamlit 截圖中按鈕、輸入框、管理員區塊為較正確的淺色書卷風格。

後續待辦：
1. 鎖定 Streamlit 版本，避免新版 DOM 或預設樣式造成漂移。
2. 新增或檢查 .streamlit/config.toml，明確指定 light theme。
3. 補強 app.py 自訂 CSS，尤其是 stButton、stTextInput、stSelectbox、sidebar/admin 區塊的背景色、文字色、邊框、hover/focus 狀態。
4. 將自訂 CSS 集中整理，降低與 Streamlit 預設樣式互相覆蓋的風險。
5. 建立固定 viewport 截圖基準，例如 1920x1280，未來重開或改版後先做視覺比對。
6. 固定本地啟動指令：
   streamlit run app.py --server.port 8519 --server.address localhost

====================================================
【2026-05-30】本機工作區與雙機接力架構
====================================================

背景：
- SynologyDrive 同步資料夾內執行開發工作，曾出現 Stale NFS file handle。
- Streamlit watcher、git repo、venv、cache、CSV/MD/JPG 大量小檔混在同步資料夾中，會增加不穩定風險。
- 使用者主要以筆電操作，但桌機有更強運算能力，適合接力重任務。

決策摘要：
- 正式開發工作區改移到本機非同步資料夾，例如 ~/Projects/TungsAcu-DB。
- SynologyDrive 保留作原始資料、書籍、備份、歷史副本，不再作為執行中的 Streamlit/venv/git 大量讀寫工作區。
- 跨機接續以 git 為準，不靠 SynologyDrive 同步 .git。
- 筆電作為主要操作與審查機；桌機作為 MinerU、OCR、本地推論、批次轉檔等重任務接力者。
- token、Keychain、venv、cache、runtime 狀態不跨機同步。
- CSV/MD/JPG 仍是正式後端；使用者可直接改 CSV，後續應補「重新載入資料」按鈕與 CSV 健康檢查。

詳細規格：
- docs/specs/TungsAcu-DB-current-spec.md

====================================================
【2026-06-07】《治療析要》症狀標準詞表初版
====================================================

背景：
- 決定以《董氏奇穴治療析要》目錄/症狀詞作為全站標準症狀詞表。
- 症狀頁、穴位頁主治症狀、對針主治分類，後續都優先對齊標準症狀詞。
- 既有抽取出的主治關鍵字保留為相關關鍵字，用於搜尋、同義詞、病機詞、部位詞與補充提示，不作為主分類。

完成事項：
- 從 `data/症狀治療.csv` 中 `來源 = 董氏奇穴治療析要` 的 664 筆條目產生初版詞表。
- 新增 `data/症狀標準詞表.csv`：468 個唯一症狀詞。
- 新增 `data/症狀映射表.csv`：468 筆 identity mapping（標準症狀對應自身）。
- `data/症狀標準詞表.csv` 保留 `條目數` 與 `空推薦穴位數`，方便人工審核。

資料觀察：
- 《治療析要》來源共 664 筆。
- 唯一症狀詞 468 個。
- 推薦穴位空白列 144 筆。
- 有 48 個標準症狀目前所有對應條目都沒有推薦穴位，後續應優先審核。

決策：
- 初版詞表先保持來源順序，不人工合併近義詞。
- 近義詞、抽取詞、病機詞、部位詞後續進 `data/症狀映射表.csv`，不直接污染標準症狀詞表。

====================================================
【2026-06-07】《治療析要》目錄排序與詞表分層
====================================================

背景：
- 使用者指出初版詞表排序難以與《治療析要》原書目錄比對。
- 轉檔後 Markdown 已找到：`04-書籍資料庫/converted-md/楊維傑-董氏奇穴治療析要/楊維傑-董氏奇穴治療析要.md`。
- 由正文標題抽出 `data/治療析要目錄候選.csv`，作為目錄順序與人工校對依據。

完成事項：
- 新增 `data/治療析要目錄候選.csv`：158 筆候選標題。
- 其中 126 筆可直接匹配到 `data/症狀標準詞表.csv`。
- 更新 `data/症狀標準詞表.csv` 欄位：
  - `詞表層級`
  - `目錄排序`
  - `目錄症狀`
  - `目錄節`
  - `來源行`
- 將 126 筆可匹配者標為 `目錄標準詞`，依《治療析要》正文目錄排序。
- 將 342 筆未匹配目錄者標為 `抽取詞待映射`，排序移到 10000 之後，先保留搜尋價值。
- 更新 `data/症狀映射表.csv`：
  - 目錄標準詞：`類型 = 原始症狀`
  - 抽取詞：`類型 = 抽取詞`，備註「待人工映射到目錄標準詞；暫以自身保留搜尋命中」

決策：
- `症狀標準詞表.csv` 目前保留 468 筆，不立即刪除非目錄詞，避免丟失既有抽取價值。
- UI 預設清單後續應優先顯示 `詞表層級 = 目錄標準詞`。
- `抽取詞待映射` 只作搜尋命中與人工映射工作表，不作主分類。

====================================================
【2026-06-07】《治療析要》校對表同步正式詞表
====================================================

背景：
- 使用者用 Excel 校對 `data/治療析要目錄候選.csv`，補足原先缺漏的目錄症狀。
- 決定 `匹配標準症狀` 中括號內文字只作別名，頂層 `、` 才拆成多個正式詞。
- 英文專有名詞如 `Bell's palsy`、`TMJ`、`TMD` 不加雙引號；放在括號內作搜尋別名。

完成事項：
- 更新 `口歪眼斜`：
  - `匹配標準症狀 = 面神經麻痹、面癱（Bell's palsy）`
  - 同步後 `面神經麻痹`、`面癱` 皆為正式詞。
  - `Bell's palsy` 為映射別名，不作正式詞。
- 更新 `下頜骨痛(口不能張、顳頜關節紊亂症)`：
  - `匹配標準症狀 = 顳頜關節紊亂（TMJ、TMD、temporomandibular joint disorder、temporomandibular disorders）`
  - `TMJ`、`TMD` 與完整英文作映射別名，不作正式詞。
- 依校對表重建 `data/症狀標準詞表.csv`：
  - 201 個正式 `目錄標準詞`
  - 無重複 `標準症狀`
- 依同步規則重建 `data/症狀映射表.csv`：
  - 650 筆映射
  - 包含目錄原始標題、括號內別名、複合詞原字串、舊抽取詞搜尋保留
- `data/治療析要目錄候選.csv` 目前 196 列：
  - `matched` 193 列
  - `not_in_standard_terms` 3 列：`中指麻`、`腿麻`、`四肢其他`

決策：
- `data/症狀標準詞表.csv` 從此只保留正式目錄標準詞。
- 舊 468 詞中的非正式抽取詞不刪除價值，改由 `data/症狀映射表.csv` 保留搜尋命中。
- 前端症狀清單應讀正式詞表；搜尋可讀映射表擴充命中。

====================================================
【2026-06-07】症狀頁接正式詞表與映射表
====================================================

完成事項：
- `data_loader.py` 新增：
  - `load_symptom_standards_df()`
  - `load_symptom_mappings_df()`
  - `resolve_symptom_query()`
- 症狀預設清單改讀 `data/症狀標準詞表.csv`。
- 症狀預設清單依 `分類` 分組：
  - 痛症
  - 內科
  - 頭面頸
  - 五官科
  - 婦兒科
  - 皮膚外科
  - 其他疾病
- 症狀搜尋改用 `data/症狀映射表.csv` 擴充查詢詞。
- 搜尋 `面癱`、`Bell's palsy`、`TMJ`、`五十肩`、`小腿痛` 會先解析到正式詞或相關別名，再查穴位。
- 前端搜尋結果會顯示對應的標準詞/別名，方便確認映射是否符合預期。

驗證：
- 使用 Streamlit 實際啟動 `http://localhost:8519`，HTTP 回應 200。
- `app.py`、`data_loader.py` 語法檢查通過。
- 正式症狀預設清單目前共 201 項。

====================================================
【2026-06-07】穴位詳情頁主治症狀標準化
====================================================

完成事項：
- `data_loader.py` 新增 `standardize_keywords()`。
- 穴位詳情頁「主治原理」tab 改為：
  - 先顯示 `標準主治症狀`，來源為 `data/症狀映射表.csv` 對齊後的正式詞。
  - 未對齊正式詞的原始 `主治關鍵字` 改放 `相關關鍵字`。
  - 若某穴目前沒有任何標準症狀，`相關關鍵字` 直接顯示，不折疊，避免畫面空白。
- 點擊標準主治症狀或相關關鍵字，仍會跳到症狀模式搜尋。

資料觀察：
- 234 個穴位中，目前 130 個至少能對齊 1 個正式症狀。
- 104 個穴位目前尚無已對齊正式症狀，仍依原始主治關鍵字作補充顯示。

驗證：
- `app.py`、`data_loader.py` 語法檢查通過。
- Streamlit `http://localhost:8519` HTTP 回應 200。
- 嘗試使用 in-app Browser 做視覺驗證，但目前 `iab` browser 不可用。

補充修正：
- 相關關鍵字點擊後若尚未對齊標準症狀，症狀頁會明確提示「此詞目前尚未對齊標準症狀，先以原始關鍵字搜尋」。
- 新增 `data_loader.same_acupoint_refs()`，解析 `同XX穴` 類主治關鍵字。
- 穴位詳情頁「相關關鍵字」若遇到 `同XX穴`，按鈕會顯示 `同XX穴 → XX穴`，點擊後直接跳到目標穴位。
- 已驗證樣本：
  - `同火陵穴` → 火陵穴
  - `同水相穴及腎虧之背痛` → 水相穴
  - `同通腎穴，又治背痛` → 通腎穴
  - `同手五金穴` → 手五金穴
  - `同上唇穴` → 上唇穴

====================================================
【2026-06-07】對針頁接標準症狀搜尋
====================================================

完成事項：
- `search_pairs_df()` 改用 `resolve_symptom_query()` 擴充搜尋詞。
- 對針頁搜尋時可透過標準詞/映射詞查 `主治關鍵字`。
- 對針頁搜尋結果與單組對針詳情保留原始 `主治`，若能從長句中對齊正式詞，額外顯示 `標準症狀：...`。
- 穴位詳情頁「臨床配伍」中的對針區塊也同步顯示可對齊的標準症狀。
- 新增 `standardize_text_keywords()`，用於從長句主治文字抓正式症狀詞。
- 修正短詞誤命中：例如 `坐骨神經痛` 不再同時顯示 `經痛`。

資料觀察：
- `對針表.csv` 目前 146 筆，原始主治多為長句。
- 直接透過現有映射表能對齊的對針不多，後續若要更完整，需要補 `症狀映射表.csv`，例如 `肩關節周圍炎` 對到 `肩周炎/五十肩`。

驗證：
- `坐骨神經痛` 可搜尋到相關對針，標準症狀顯示為 `坐骨神經痛`。
- `面癱` 可透過 `口歪眼斜` 映射搜尋到相關對針。
- `靈骨` 等穴名搜尋仍正常。
- `app.py`、`data_loader.py` 語法檢查通過。

====================================================
【2026-06-09】重建對針資料與新版檢索 UI 推送
====================================================

完成事項：
- 依《區位易象特效對針》目錄與內容重建 `data/對針表.csv`：
  - 新欄位包含 `大類`、`次分類`、`目錄排序`、`穴組名稱`、`穴名`、`位置`、`針法`、`解析`、`圖片`、`理論與發揮`、`主治關鍵字`、`頁碼`。
  - 每組對針保留兩列穴位資料，前端再合併呈現兩穴與理論解析。
  - 圖片欄先保留空白，未來另做穴位示意圖。
- 建立對針重建與關鍵字標準化中介資料：
  - `data/pair_rebuild/對針表_重建草稿.csv`
  - `data/pair_rebuild/對針表_關鍵字標準化.csv`
  - `data/pair_rebuild/對針關鍵字_未映射.csv`
  - `data/pair_rebuild/對針關鍵字_標準化報告.json`
- 建立並使用症狀標準化資料：
  - `data/症狀標準詞表.csv`
  - `data/症狀映射表.csv`
  - `data/症狀標準詞表_待補穴位.csv`
- Streamlit UI 調整：
  - sidebar 只保留搜尋框、`穴位詮解`、`治療析要`、`區位對針`。
  - sidebar hover 改為右側浮出細項，治療與對針支援兩層分類。
  - topbar 改為較高的宣紙硃砂風格，右上角保留 `管理員`。
  - 穴位、症狀、對針首頁皆改為大分類 + 方格入口。
  - 症狀細項點入後以穴位小方格顯示結果。
  - 對針搜尋/分類結果改為一列兩格，點卡片直接進對針詳情。
  - 對針詳情分為第一穴、第二穴、兩穴解析與理論發揮；圖片區先以空白佔位。
- 專案規則補強：
  - 新增 `AGENTS.md` 與 `CLAUDE.md`，明定正式開發 repo 是 `/Users/samue11in/Projects/TungsAcu-DB`。
  - SynologyDrive 同名資料夾僅作歷史/來源參考，不寫入程式、CSV、spec、plan 或工作日誌。

驗證與版本：
- 本機 Streamlit `http://localhost:8501` 可回應 HTTP 200。
- `app.py`、`data_loader.py` 以 AST parse 做只讀語法檢查通過。
- 已 commit 並 push 到 GitHub `main`：
  - `39a0b65 重建對針資料並調整檢索 UI`
- GitHub push 時發現本機 `main` 與遠端分叉；已用臨時 worktree 將本次成果套到最新 `origin/main` 後推送，避免覆蓋遠端既有 CSV/圖片/筆記更新。
- 2026-06-09 已同步本機 `main` 到 `origin/main`。
  - 同步前備份分支：`local-main-before-sync-20260609-004027`
  - 同步前未提交雜項 stash：`stash@{0}`，訊息為 `pre-sync leftover docs backups 2026-06-09`

後續注意：
- 公開 Streamlit Cloud 需等待 GitHub main 部署完成後再做外部測試。
- 仍需人工校對 `data/症狀標準詞表_待補穴位.csv` 中目前無推薦穴位的正式症狀詞。
- 若要整理舊 docs 刪除、`.bak` 備份與 `docs/archive/`，應另開一次文件整理 commit，不混入 UI/資料功能 commit。

====================================================
【2026-06-10】高品質穴位圖製作方案暫存
====================================================

決策：
- 現有純向量手部原型的解剖比例與繪圖品質不足，不作為正式穴位圖母版。
- 未來優先測試「真人照片底圖 + Blender 3D 骨骼配準 + Affinity 標註」。
- 不直接將不同姿勢的 2D 人體圖與骨骼圖硬疊，也不讓 AI 生圖決定解剖或穴位位置。
- 先以指駟馬穴完成一張概念驗證，確認品質後才考慮批量製作。

詳細方案：
- `docs/specs/2026-06-10-真人照片與3D骨骼穴位圖方案.md`

狀態：
- 延後執行。
- 目前先處理本機 `http://localhost:8501` 的既有穴位圖顯示問題。

====================================================
【2026-06-10】網頁配色重設
====================================================

依使用者提供的配色參考圖調整：
- Topbar：`#505D38`
- Sidebar：`#E5E7E4`，固定寬度 `150px`，文字黑色，搜尋欄白色
- 主內容背景：`#EEEFEC`
- 主內容小格：`#CACBC1`

互動色、文字、邊框與 hover 同步改為中性深綠色階，移除原宣紙硃砂配色。

後續調整：
- Topbar 改為 `120px`，使用硃砂紅底、半透明 noise texture 與 radial gradient。
- Sidebar 改為 `200px`，使用極淺米色、半透明紙張纖維 noise texture 與 radial gradient。
- 主內容背景先改為純白色。

最終回調：
- 恢復原始宣紙硃砂色盤；Topbar 與 Sidebar 保留 noise texture + radial gradient。
- 主內容恢復純色宣紙底 `#F7EDD8`，不加紋理。
- Sidebar 文字放大並置中。
- Topbar 中文標題使用標楷體 fallback 字族，英文副標使用 Allura 書寫體。
- Sidebar 紋理改為半透明大理石：低頻雲霧、扭曲細脈與米色 radial gradient 疊加。
- Sidebar 大理石脈絡由 4 條增至 12 條，視覺密度約提高 3 倍。
- 暫時移除 Sidebar radial gradient，只保留米色底與半透明大理石紋理供比較。

====================================================
【2026-06-10】CSV 資料健康檢查腳本
====================================================

新增 `check_data_health.py`（只報告、不改資料；有 ERROR 時 exit 1）：
- 穴位表：必要欄位、穴名格式（圖X-X 開頭、標點開頭）、重複穴名（含標點變體）、
  疑似截斷重複（無穴號且穴名是另一穴名片段，先比同部位再比全表）、
  部位代碼對照部位表、穴位圖 / 詳細筆記路徑存在性
- 對針表：必要欄位、圖片路徑存在性（彙總報告）
- 症狀治療：症狀欄空白；推薦穴位空白彙總為 WARN（已知待補狀態）

首次掃描結果（待人工處理）：
- ERROR 8 項：4 筆「圖X-X 穴名」假條目、「。耳背穴」標點開頭、
  耳背穴 / 腑快穴各重複 2 次、對針表 39 張 pair_images/ 圖片不存在
  （pair_images 目錄從未產出，對針頁目前全顯示「暫無圖片」）
- WARN 23 項：21 筆疑似截斷重複列（五穴、千穴、主穴、硬穴等，皆無穴號）、
  43 筆穴號空白、症狀治療 323 筆推薦穴位待補

注意：穴號欄位放的是書中圖號（如「圖1-8」），兩穴共用一張圖屬正常，不檢查重複。

====================================================
【2026-06-10】穴號改 TEAS 編號 + 部位名稱修正 + 對針缺圖清除
====================================================

依《董氏奇穴英文對照 TEAS point index》全面修正（migrate_teas_codes.py 一次性執行）：
- 穴位表 穴號：原誤抓書中圖號（圖X-X），208 筆改為 TEAS 編號（11.01～CA.05）。
  26 筆比對不到留空白（即截斷碎片、圖說假條目、士耳、雙風等待校對列）。
- 異體字正規化比對：姊/姐、污/汙、崑/昆、崙/侖、裡/里、搏/博。
- 身體分區改名（部位表 + 穴位表 + 網頁同步）：四四 上臂、五五 腳趾、
  六六 腳掌、七七 小腿、八八 大腿、十十 頭面。
- 對針表 182 筆 pair_images/ 缺圖路徑清空（圖片從未產出，原本就顯示「暫無圖片」）。

健康檢查（check_data_health.py）配合更新：
- 穴號語意改為 TEAS 編號；新增「編號前綴對部位」檢查。
- 木穴（11.17）、解穴（88.28）、耳背穴（99.07）有正式編號，不再誤判為截斷碎片。

掃描後發現的部位錯置（待顥軒確認是否搬移）：
- 海豹（66.01）、木婦（66.02）目前在五五；花骨一～四（55.02-05）目前在六六。

TEAS 索引有、資料庫沒有的穴位（待確認是否補錄）：
- 77.18 天皇副、88.26 上九里、88.27 下九里、99.08 耳上/耳中/耳下、A.02-04 三叉一/二/三

====================================================
Active TODO
====================================================

P0：
- [x] 討論並定稿《董氏奇穴治療析要》在網頁中的資訊架構與編排方式。
- [x] 將《治療析要》編排決策更新到 `docs/specs/TungsAcu-DB-current-spec.md`。
- [x] 建立 `data/症狀標準詞表.csv`，以《治療析要》症狀詞作為全站標準症狀詞表初版。
- [x] 建立 `data/症狀映射表.csv`，先加入標準症狀 identity mapping。
- [x] 從《治療析要》Markdown 抽出 `data/治療析要目錄候選.csv`，並用於校正標準詞排序。
- [x] 將 `data/症狀標準詞表.csv` 分成 `目錄標準詞` 與 `抽取詞待映射`。
- [x] 依校對後 `data/治療析要目錄候選.csv` 重建正式 `data/症狀標準詞表.csv` 與 `data/症狀映射表.csv`。
- [ ] 人工審核 `data/症狀標準詞表.csv` 中 25 個已有條目但推薦穴位皆空白的正式詞。
- [ ] 補齊 `data/症狀標準詞表.csv` 中 61 個正式詞的條目數 metadata 或映射來源統計。
- [ ] 人工審核 `data/治療析要目錄候選.csv` 中 `not_in_standard_terms` 的候選標題，決定是否補入標準詞或排除。
- [ ] 將 `抽取詞待映射`、既有抽取詞、同義詞、病機詞、部位詞映射到目錄標準詞。
- [x] 調整症狀頁，預設清單優先顯示標準症狀詞，相關關鍵字降為搜尋輔助。
- [x] 調整穴位詳情頁主治症狀，主要顯示標準症狀詞，原 `主治關鍵字` 降為補充提示。
- [x] 調整對針頁搜尋與詳情，優先顯示可對齊的標準症狀詞，原始主治保留為說明。
- [ ] 以瀏覽器截圖確認目前 Streamlit UI 樣式修正：搜尋框、瀏覽按鈕、sidebar/admin、selectbox。

P1：
- [ ] 整理 `app.py` 自訂 CSS，降低 Streamlit 預設樣式覆蓋風險。
- [ ] 建立固定 viewport 截圖基準，例如 1920x1280。
- [ ] app 內新增「重新載入資料」按鈕，清除 Streamlit cache。
- [x] 新增 CSV 健康檢查：必要欄位、穴名/穴號重複、圖片路徑、notes 路徑、症狀詞表。（check_data_health.py）

Later：
- [ ] 依 `docs/specs/2026-06-10-真人照片與3D骨骼穴位圖方案.md` 製作指駟馬穴概念驗證圖。
- [ ] 建立桌機 heavy-worker 腳本或 runbook：MinerU、OCR、本地 LLM、批次轉檔。
- [ ] 視需要補 admin 內 notes/Markdown 編輯能力。

====================================================
【2026-06-10】公開站隱藏管理員入口
====================================================

安全修正：
- 新增 `_admin_enabled()`：只有 secrets.toml 設 `admin_enabled = true` 的環境才開放管理員功能。
- 公開 Streamlit Cloud 不設此 secret → topbar 管理員連結、`?admin=1`、登入面板全部隱藏。
- 移除 `admin123` 預設密碼；`admin_password` 未設定時一律拒絕登入。
- 本機 `.streamlit/secrets.toml`（已 gitignore）設 `admin_enabled = true` 與隨機密碼。

提醒：雲端容器的 CSV 編輯本就是暫存、重啟即消失；正式編輯流程一律在本機完成後 push。

====================================================
【2026-06-11】補錄 9 個 TEAS 索引穴位
====================================================

從《董氏奇穴穴位詮釋解》（04-書籍資料庫 converted-md，簡體轉繁 OpenCC s2tw）補錄：
- 天皇副穴（腎關）77.18、上九里穴（內九）88.26、下九里穴（外九）88.27
- 耳上穴（耳尖）99.08-1、耳中穴 99.08-2、耳下穴 99.08-3
- 三叉一穴（肺叉）A.02、三叉二穴（心叉）A.03、三叉三穴（脾叉）A.04

每穴含 CSV 列 + notes/<穴名>.md 詳細筆記。穴位表 207 → 216 列。
健康檢查 ERROR 0；殘留 WARN 為顥軒決定保留的已知事項
（海豹/木婦/花骨部位不搬、症狀治療 323 筆待補）。

====================================================
【2026-06-11】UI 三項優化：hover 修復 + 手機版 + 穴位互連
====================================================

1. hover 面板修復（桌機）：
   - 第一層 flyout 加 max-height + 捲動，JS 動態 fixed 定位夾在視窗內
   - 第二層 subflyout 初始改 fixed，避免被可捲動的第一層裁切
   - 視窗縮放即時重新定位。540px 矮視窗實測兩層皆完整可見。

2. 手機版（≤768px 媒體查詢）：
   - Topbar 縮 64px、隱藏英文副標；sidebar 變頂部導航列（搜尋 + 三導航橫排）
   - 觸控裝置停用 hover flyout，導航改點擊進頁（首頁部位區塊即完整清單）
   - catalog 2 欄、對針清單 1 欄。390x844 實測首頁與詳情頁皆正常。
   - 修正主容器 testid：stMainBlockContainer（舊 block-container 從未生效）。

3. 穴位互連：
   - 內文（位置/針法/備註/董楊思維/現代解剖/原理與發揮/推薦穴位）中出現的
     其他穴名自動變成該穴詳情頁連結（.ap-xref 樣式，金色點底線）
   - 穴名長度遞減匹配（天皇副穴優先於天皇穴），不自連當前穴
   - 火主穴頁實測 61 個連結，點擊正確跳轉火硬穴 66.03。

註：依顥軒決定不做「歸經/穴性/針感」欄位（各家思想不同）。

====================================================
【2026-06-11】手機版修正第二輪 + 主頁分類摺疊
====================================================

真機回饋修正：
- Sidebar 半寬根因：真機上 Streamlit 切到 aria-expanded="false"，桌面 200px
  鎖定規則特異性較高蓋過 100vw；媒體查詢內補上該狀態的覆蓋。
- 導航列下緣加 padding（大分類不再貼邊）。

主頁分類摺疊（穴位/症狀/對針三頁統一）：
- 各分類改為 <details class='catalog-acc'> 摺疊區塊，含項目數與箭頭。
- 桌面預設展開；手機（≤768px）由 positioner script 載入時收合一次，
  使用者展開後不再干涉。
- 症狀主頁從 st.button 改為連結卡片（?nav=symptom&sub=症狀，
  與 flyout 同路徑），手機一列兩個、字多縮小不換行。

驗證：390x844 首頁（13 摺疊列）、展開（兩欄卡片）、症狀頁（7 大分類）、
點擊後頭痛正確進結果頁；1440 桌面預設展開、版面正常。
