# 對話紀錄 — 2026-06-06

## 對話背景
延續 `doc/對話.txt` 的需求（河道斷面底床最低點高程沿程變化圖），本檔記錄 2026-06-06 整天的完整對話與決策歷程。

---

## 回合 1：使用者提出原始需求

> 我想做一個專案 可以繪製河道斷面底床最低點高程(Y軸) 與 斷面至河道出口的距離(X軸)
> 1. 使用html/css/javascript + flot chart 繪圖元件
> 2. 資料檔案如data\景美溪\M_2012-2025_bed_min_profile.csv
> 3. 繪製斷面最低點高程 vs 斷面到河道出口距離 折線圖
> 4. Y軸為斷面最低點高程，下部X軸為斷面到河道出口距離，上部X軸為斷面編號
> 5. 使用者選項包括: 河道編號、起始西元年、結束西元年
> 6. 繪圖樣式參考 get_cross_section.py
> 7. 先做計畫

---

## 回合 2：brainstorming 釐清

助理載入 `brainstorming` skill，確認計畫模式，並進行以下澄清：

**Q1：flot 函式庫來源？**
→ 使用者選擇：**Local flot/ v0.8.3**（推薦；離線可用、版本固定）

**Q2：河道範圍？**
→ 使用者選擇：**5 條現有 CSV**（景美溪 M、新店溪 H、基隆河 KE、三峽河 S、淡水河 TE；對應 get_cross_section.py 中已有資料的子集）

**Q3：產出檔案名稱？**
→ 使用者選擇：**新檔 plot_river_bed_profile_flot.html**（保留原 echarts 版 plot_river_bed_profile.html 不動）

---

## 回合 3：助理提出設計摘要

> **技術架構**：單一 HTML 檔，自含 CSS + JS；jQuery 走 CDN，flot 用 local v0.8.3
> **UI 控制**：河道 select、起始年 select、結束年 select、斷面標註間隔 number、繪製 button
> **繪圖**：Y 軸 = 最低點高程；下 X 軸 = 累積距離；上 X 軸 = 斷面編號（手動 ticks）；每個年份一條 viridis 色線
> **flot v0.8.3 重點**：用 `$.plot()`；legend 需 `container` + `labelFormatter`；x2axis 用 `ticks: [[x, "label"]]`
> **錯誤處理**：CSV 404、年份無資料、欄位不符、start > end、中文字型

---

## 回合 4：使用者批准並要求實作

> 好 請實作

助理：
1. 更新 `doc/2026-06-06-bed-profile-flot-design.md`（反映 v0.8.3 + 5 河）
2. 撰寫 `plot_river_bed_profile_flot.html`
3. 啟動 HTTP server 驗證

### 4a. 修正 4 個 flot 0.8.3 陷阱

| # | 問題 | 修正 |
|---|------|------|
| 1 | `populateSelect` 把 `item` 物件塞進 `option.value`，瀏覽器轉成 `"[object Object]"`，導致 `select.value` 為空 | 加入 `item.id` 判斷 |
| 2 | flot line 1126 直接讀 `s.bars.show` 沒防呆 | series 顯式加 `bars: { show: false }` |
| 3 | flot line 2777 直接讀 `series[i].dashes.show` | series 加 `dashes: { show: false }` |
| 4 | x2axis 預設 `axis.used` 為 false（無 series 綁定），導致 show=false 不渲染 | x2axis 顯式 `show: true` |

### 4b. 修正 1 個資料 typo

`data/淡水河/` 路徑寫成 `data/\u6de8\u6c34\u6cb3`（淨水河），應為 `data/\u6de1\u6c34\u6cb3`（淡水河）

### 4c. 修正 1 個 UX 設定

`grid.hoverable: false` 改成 `mouseActiveRadius: 25`（預設 10px 在 ~20px 點距下太近）

### 4d. 修正 1 個 resize 誤刪

原本寫 `window.addEventListener('resize', ...)` 手動重繪，是多餘且有 bug 的。local flot 的 `jquery.flot.resize.js` 已內建自動監聽 placeholder resize，直接刪除手動 handler。

### 4e. 驗證結果（headless browser）

| 測試 | 結果 |
|------|------|
| 景美溪 (M) | 938 筆 |
| 新店溪 (H) | 1121 筆 |
| 基隆河 (KE) | 2058 筆 |
| 三峽河 (S) | 518 筆 |
| 淡水河 (TE) | 1526 筆 |
| 年份篩選 2020-2023 | 4 條線 |
| start > end | 紅字錯誤 |
| labelStep=10 | top 軸顯示 M00.2, M09, M18… |
| 上軸「斷面編號」 | 標題置中 |
| 下軸「累積距離」 | 0-18000 |
| Y 軸「最低點高程」 | -5~40 |
| viridis 14 色 | 套用 |

---

## 回合 5：使用者要求新增 hover tooltip

> 新增 滑鼠移動到數據點後 請將歷年數據以跳出視窗列表顯示

助理實作：
- CSS：白底圓角陰影小視窗，固定定位
- HTML：`<div id="tooltip">`
- 模組級查表：`sectionYearZ[section][year] = min_Z` 與 `distanceToSection[dist] = section`
- `grid.hoverable: true; mouseActiveRadius: 25`
- 綁定 `plothover`，從 `item.datapoint[0]` 取距離 → 反查斷面 → 組出表格
- tooltip 自動貼齊游標 14px，靠近邊界時翻向
- 缺資料年份以灰色斜體 `—` 標示

### 驗證

| 測試 | 結果 |
|------|------|
| 滑鼠移到 M05 (距出口 1599m) | tooltip 顯示 14 年 (2012-2025) ✓ |
| 年份篩選 2020-2023 | tooltip 只顯示 4 年 ✓ |
| 滑鼠移出圖表 | tooltip 隱藏 ✓ |

---

## 回合 6：使用者詢問局部放大可行性

> 我需要 局部放大功能 是否可行

助理回應：可行。flot 0.8.3 內建 selection 機制 → 助理先回答「可行」並提出方案：
- 拖曳 X 軸範圍放大
- X 與 Y 軸都自動重算
- 「重設縮放」按鈕
- 仍保留年份篩選、labelStep、hover tooltip

---

## 回合 7：使用者批准

> 好

助理實作：
- HTML：新增 `<button id="resetZoomBtn">` 與提示文字
- HTML：新增 `<div id="zoom-selection">` 絕對定位選取框
- 模組級：`var zoomState = { active, xMin, xMax }`
- 自製拖曳（因 flot 0.8.3 無 selection plugin）：mousedown/move/up + `xaxis.c2p()` 轉資料範圍
- `plot()` 重構：以 zoomState 覆蓋 xaxis/x2axis 範圍，重新計算 y 軸範圍從選取範圍內資料
- x2axis 刻度只保留 `[xMin, xMax]` 內斷面
- 微小拖曳（< 0.5% 全範圍）忽略
- 「重設縮放」按鈕啟用條件：`zoomState.active`
- 自動重設時機：切換河道、起始年、結束年、點「繪製」按鈕
- 修變數命名衝突：`var plot = getPlot()` 撞 `function plot()` → 改用 `var p`

### 驗證

| 測試 | 結果 |
|------|------|
| 拖曳 data x 2000→6000 | xMin=2612, xMax=6620, y 自動縮到 2.8-9.3 ✓ |
| 點「重設縮放」 | 回到全範圍 ✓ |
| 微小拖曳 (10 單位) | 不放大 ✓ |
| 切換河道 (M→H) | 縮放重設 ✓ |
| 切換年份 | 縮放重設 ✓ |
| 縮放後 hover 資料點 | tooltip 仍正常顯示 ✓ |

---

## 最終產出檔案

### 新增
- `plot_river_bed_profile_flot.html` — 單檔自含，~420 行，含 flot 0.8.3 折線圖、hover tooltip、局部放大

### 更新
- `doc/2026-06-06-bed-profile-flot-design.md` — 反映 v0.8.3 + 5 河 + tooltip + zoom 設計
- `doc/對話.txt` — 原始需求（未動）
- `doc/2026-06-06-conversation-log.md` — 本檔

### 現有（未動）
- `plot_river_bed_profile.html` — 原 echarts 版
- `flot/` — local flot v0.8.3 + plugins
- `data/{5 個河道資料夾}` — CSV 資料

---

## 關鍵決策紀錄

1. **單一 HTML 檔**：無打包工具、無後端、易部署
2. **local flot v0.8.3**：離線可用、版本固定（避開 v4 ESM 語法差異）
3. **5 河範圍**：與既有 CSV 與 get_cross_section.py 交集一致
4. **hoverable radius 25**：預設 10 在 ~20px 點距下命中率過低
5. **手動 resize handler 移除**：flot resize plugin 已內建自動處理
6. **selection 機制自製**：flot 0.8.3 缺 selection plugin，避免引外部依賴
7. **變數 p 避免撞函數 plot**：plot() 函數與 flot 實例變數名稱隔離
8. **變數 sectionYearZ/distanceToSection 提到模組級**：bindHover 從 plot 閉包外呼叫，需模組級作用域
9. **滑鼠游標 crosshair**：暗示「可拖曳」操作
10. **微拖曳 <0.5% 忽略**：避免使用者誤觸
