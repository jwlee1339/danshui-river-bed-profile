# 河道斷面底床最低點高程沿程變化圖 (Flot 版)

以 HTML + JavaScript + [Flot v0.8.3](http://www.flotcharts.org/) 繪製指定河道在多個年份中的「斷面底床最低點高程」沿程變化折線圖。支援滑鼠 hover 查詢任一斷面歷年數據，以及水平拖曳框選局部放大。

---

## 目錄

- [功能](#功能)
- [系統需求](#系統需求)
- [輸入資料](#輸入資料)
- [輸出內容](#輸出內容)
- [程式結構](#程式結構)
- [使用方法](#使用方法)
- [檔案清單](#檔案清單)
- [已知限制](#已知限制)
- [相關資源](#相關資源)

---

## 功能

### 主要繪圖

- 折線圖：X 軸 = 斷面至河道出口累積距離，Y 軸 = 斷面底床最低點高程
- 每個年份繪製一條線，使用 viridis 14 階色盤區分
- 圓點標記每個斷面測點（radius 3）
- 雙 X 軸：
  - 下軸 = 累積距離（數值軸，自動刻度）
  - 上軸 = 斷面編號（手動刻度，依「斷面標註間隔」過濾）
- Y 軸 = 最低點高程（含軸標題）
- 圖例置於圖表右上方，分欄排版
- 淺灰格線

### 使用者介面

| 控制項 | 類型 | 預設值 | 說明 |
|--------|------|--------|------|
| 河道 | 下拉選單 | 景美溪 (M) | 切換 5 條河，自動載入並重繪 |
| 起始年 | 下拉選單 | 2012 | 2012 ~ 2025 |
| 結束年 | 下拉選單 | 2025 | 2012 ~ 2025 |
| 斷面標註間隔 | 數字輸入 | 1 | 控制上軸斷面編號的刻度密度（1 = 全部）|
| 繪製 | 按鈕 | — | 手動重繪（會重設縮放） |
| 重設縮放 | 按鈕 | 預設停用 | 縮放啟用時可按 |

### 互動功能

- **Hover 查詢**：滑鼠移到任一資料點，跳出小視窗列出該斷面在目前年份範圍內所有年份的高程值
- **局部放大**：在圖表區水平拖曳框選 X 軸範圍，放大顯示
  - X 軸限在選取範圍
  - Y 軸依選取範圍內資料自動重算 min/max
  - 上軸斷面編號跟著只顯示選取範圍內的斷面
- **重設縮放**：按「重設縮放」按鈕回到全範圍
- **自動重設時機**：切換河道、起始年、結束年、點「繪製」按鈕時，會自動重設縮放

### 錯誤處理

| 情境 | 顯示 |
|------|------|
| CSV 載入失敗（404、網路錯誤）| 紅字「無法載入資料檔案，請確認 HTTP server 已啟動」|
| 起始年 > 結束年 | 紅字「錯誤: 起始年不可大於結束年」|
| 年份範圍內無資料 | 紅字「所選年份範圍內無資料」|
| CSV 欄位不符 | 紅字「資料格式錯誤：缺少 year/Section_ID/Cum_Distance/min_Z」|
| 微小拖曳 (<0.5% 全範圍) | 不觸發縮放（避免誤觸）|

---

## 系統需求

### 執行環境

- **瀏覽器**：任何支援 ES5 與 Canvas 2D 的現代瀏覽器
  - Chrome / Edge / Firefox / Safari 最近 2 年版皆可
  - Internet Explorer 9 以上（flot 0.8.3 最低需求）
- **HTTP 伺服器**：因 `fetch()` 無法讀 `file://` 協定下的本地檔案，必須透過 HTTP 伺服器存取

### 軟體相依

- jQuery 3.x（從 CDN 載入）
- Flot v0.8.3（從 local `flot/` 目錄載入）
- Flot 軸標題 plugin（`jquery.flot.axislabels.js`）
- Flot 視窗縮放 plugin（`jquery.flot.resize.js`）

### 開發環境

- 任何文字編輯器（VS Code、Notepad++、Sublime Text 等）
- 不需打包工具（無 webpack/vite/rollup）
- 不需後端（純前端）
- 不需資料庫連線（CSV 已預先產出）

### 網路需求

- 首次載入需連網取得 jQuery CDN
- 之後切換不同河道時，只 fetch 本機 CSV，無需連網

---

## 輸入資料

### CSV 檔案格式

每行一筆資料，欄位順序固定：

| 欄位 | 型別 | 範例 | 說明 |
|------|------|------|------|
| `year` | 整數 | 2012 | 西元年 |
| `River_ID` | 字串 | M | 河道編號 |
| `Section_ID` | 字串 | M00.2 | 斷面編號 |
| `Cum_Distance` | 浮點數 | 0.0 | 斷面至河道出口累積距離（m）|
| `min_Z` | 浮點數 | -0.26 | 該斷面該年份測點 Z 的最小值（m）|

範例：

```csv
year,River_ID,Section_ID,Cum_Distance,min_Z
2012,M,M00.2,0.0,-0.26
2012,M,M00.4,280.0,0.63
2012,M,M01,400.0,0.42
...
```

### 檔案路徑對照

程式內建 5 條河的 CSV 路徑對照表：

| 河道顯示名 | River_ID | CSV 路徑（相對於 HTML 檔）|
|------------|----------|--------------------------|
| 景美溪 (M) | M | `data/景美溪/M_2012-2025_bed_min_profile.csv` |
| 新店溪 (H) | H | `data/新店溪/H_2012-2025_bed_min_profile.csv` |
| 基隆河 (KE) | KE | `data/基隆河/KE_2012-2025_bed_min_profile.csv` |
| 三峽河 (S) | S | `data/三峽河/S_2012-2025_bed_min_profile.csv` |
| 淡水河 (TE) | TE | `data/淡水河/TE_2012-2025_bed_min_profile.csv` |

每個 CSV 涵蓋 **2012 ~ 2025 共 14 個年份** × 各河道的所有斷面。

### 新增/修改河道

如需新增其他河道的 CSV，請：

1. 將 CSV 放到 `data/<河道名稱>/<River_ID>_2012-2025_bed_min_profile.csv`
2. 編輯 `index.html` 的 `RIVERS` 陣列，加入新項目：

```js
var RIVERS = [
    { label: '景美溪(M)',  id: 'M',  path: 'data/\u666f\u7f8e\u6eaa/M_2012-2025_bed_min_profile.csv' },
    // ... 加入新河道
    { label: '新河道(XX)', id: 'XX', path: 'data/\u65b0\u6cb3\u9053/XX_2012-2025_bed_min_profile.csv' },
];
```

注意 `path` 中的中文字元需用 `\u` 跳脫序列，避免 CSV 載入失敗。

---

## 輸出內容

程式本身不輸出檔案，僅在瀏覽器中繪製互動式圖表。圖表內容包括：

- 圖表標題（H2 元素）：「河道斷面底床最低點高程沿程變化圖」
- 14 條 viridis 顏色折線（每個年份一條）
- 雙 X 軸刻度與軸標題
- Y 軸刻度與軸標題
- 圖例（含 14 個年份標籤）
- Hover 跳出的斷面資訊小視窗

### 衍生資料（供其他用途）

如需從原始資料庫（SQL Server）重新產生 CSV，可參考同目錄的 `plot_river_bed_profile.py`（matplotlib 版，輸出格式與本前端相同）。

---

## 程式結構

### 檔案組織

```
C:\home\02_MIT\2026\09_淡水河沖淤\
├── index.html   # 本檔重點：Flot 前端（單檔 ~513 行）
├── plot_river_bed_profile.html        # [現有] 原 echarts 版（未動）
├── plot_river_bed_profile.py          # [現有] matplotlib 版（產出 CSV）
├── get_cross_section.py               # [現有] 斷面查詢+繪圖（風格參考）
├── flot\                              # [現有] local flot v0.8.3
│   ├── jquery.flot.js
│   ├── jquery.flot.axislabels.js
│   └── jquery.flot.resize.js
├── data\                              # [現有] 5 條河 CSV
│   ├── 景美溪\M_2012-2025_bed_min_profile.csv
│   ├── 新店溪\H_2012-2025_bed_min_profile.csv
│   ├── 基隆河\KE_2012-2025_bed_min_profile.csv
│   ├── 三峽河\S_2012-2025_bed_min_profile.csv
│   └── 淡水河\TE_2012-2025_bed_min_profile.csv
└── doc\                               # [現有] 文件
    ├── 對話.txt                                # 原始需求
    ├── 河道斷面底床最低點高程沿程圖計畫.txt     # Python 版計畫
    ├── 2026-06-06-bed-profile-flot-design.md    # Flot 版設計文件
    └── 2026-06-06-conversation-log.md           # 今日對話紀錄
```

### `index.html` 內部結構

單一 HTML 檔，自含 CSS 與 JS，依功能分為以下段落：

| 段落 | 行數範圍 | 內容 |
|------|----------|------|
| `<head>` | 1-62 | meta、CDN、local flot 引用、CSS |
| 控制項列 | 64-90 | select × 3、number × 1、button × 2、提示文字 |
| `#chart-container` | 92-96 | 圖表容器含 legend、選取框、canvas |
| 常數與全域變數 | 100-117 | RIVERS、YEARS、VIRIDIS、cachedData、sectionYearZ、distanceToSection、zoomState |
| 工具函式 | 119-170 | getColor、parseCSV、showStatus、hideStatus |
| `plot()` 主函式 | 172-330 | 資料處理、軸計算、flot 呼叫、事件綁定 |
| Hover tooltip | 332-360 | showTooltip、hideTooltip、bindHover |
| Zoom 功能 | 362-410 | alignZoomSelectionDiv、setupZoom |
| 初始化 | 412-490 | populateSelect、loadData、按鈕事件、resize 監聽 |

### 模組級變數

```js
var RIVERS              // 河道清單（5 條）
var YEARS               // 2012 ~ 2025
var VIRIDIS             // 14 色 RGB 陣列
var cachedData          // 各河道已載入的 CSV 資料（cache 避免重複 fetch）
var sectionYearZ        // 反查表：sectionId -> { year: min_Z }
var distanceToSection   // 反查表：distance -> sectionId
var zoomState           // 縮放狀態：{ active, xMin, xMax }
var currentLabelStep    // 當前斷面標註間隔
```

### 主要函式

| 函式 | 用途 |
|------|------|
| `parseCSV(text)` | 解析 CSV 字串為物件陣列（去 BOM、行分割、欄位對應）|
| `plot()` | 主要繪圖流程：UI 值讀取 → 篩選 → 計算軸範圍 → 呼叫 $.plot() → 綁定事件 |
| `showTooltip()` | 顯示 hover 跳出視窗（自動貼齊游標）|
| `bindHover()` | 綁定 `plothover` 事件，呼叫 showTooltip |
| `setupZoom()` | 綁定 mousedown/move/up，處理拖曳框選 |
| `alignZoomSelectionDiv()` | 每次 plot 後對齊選取框位置 |
| `loadData(riverId, cb)` | fetch CSV，解析後存入 cachedData，呼叫 cb |

### flot v0.8.3 設定重點

```js
$.plot($('#chart'), series, {
    legend: { show: true, container: $('#legend'), noColumns: 7 },
    xaxis:  { min, max, axisLabel: '斷面至河道出口累積距離 (m)' },
    x2axis: { show: true, min, max, ticks: [[dist, sectionId], ...],
              axisLabel: '斷面編號' },
    yaxis:  { min, max, axisLabel: '斷面底床最低點高程 (m)' },
    grid:   { hoverable: true, mouseActiveRadius: 25, autoHighlight: true }
});
```

每個 series 必須顯式提供 `bars: { show: false }` 與 `dashes: { show: false }`，否則 flot 0.8.3 內部會在 legend 渲染時拋 `Cannot read properties of undefined (reading 'show')`。

---

## 使用方法

### 第一次啟動

1. 開啟終端機，切換到專案根目錄：

   ```bash
   cd C:\home\02_MIT\2026\09_淡水河沖淤
   ```

2. 啟動本機 HTTP 伺服器（任選一）：

   ```bash
   # 方法 A：Python 內建（最簡單）
   python -m http.server 8000

   # 方法 B：Node.js
   npx serve .

   # 方法 C：PHP
   php -S localhost:8000
   ```

3. 用瀏覽器開啟：

   ```
   http://localhost:8000/
   ```

### 日常操作

| 操作 | 結果 |
|------|------|
| 切換河道下拉 | 自動載入新 CSV 並重繪 |
| 切換起始年/結束年 | 自動篩選並重繪 |
| 修改斷面標註間隔 | 需點「繪製」按鈕才生效 |
| 點「繪製」 | 重新計算並繪製（會重設縮放）|
| 滑鼠移到資料點 | 跳出小視窗顯示該斷面歷年數據 |
| 在圖表區水平拖曳 | 框選 X 範圍局部放大 |
| 點「重設縮放」 | 回到全範圍 |

### 部署到正式環境

將以下檔案上傳到任何靜態網頁伺服器（nginx、Apache、IIS 等）：

- `index.html`
- `flot/`（整個資料夾）
- `data/`（整個資料夾）

注意：HTML 內引用 jQuery 走 CDN（`https://cdn.jsdelivr.net/npm/jquery@3/dist/jquery.min.js`）。如正式環境無外網，可改為下載 jQuery 到 local 並修改 HTML 內的 `<script src="...">`。

### 中文字型

CSS 已設定字型 fallback 鏈：

```css
font-family: 'Microsoft JhengHei', 'Noto Sans TC', 'PingFang TC', 'Heiti TC', sans-serif;
```

- Windows：使用 Microsoft JhengHei（微軟正黑體）
- macOS：使用 PingFang TC 或 Heiti TC
- Linux：使用 Noto Sans TC

如使用 Linux 伺服器但無中文字型，請安裝 `fonts-noto-cjk`：

```bash
sudo apt install fonts-noto-cjk
```

---

## 已知限制

1. **flot 0.8.3 較舊**：v4+ 的 ES module 語法不適用；如未來升級，需重寫 `$.plot()` 與 legend 處理
2. **無打包工具**：無法用 npm 套件；如需加強功能（如匯出 PNG、動畫）需自寫或引用 CDN
3. **jQuery 仍走 CDN**：離線環境需先下載 jQuery 到 local
4. **HTTP 必需**：`file://` 協定下 `fetch()` 會被瀏覽器擋下（CORS 限制）
5. **IE 相容性**：flot 0.8.3 仍支援 IE9+，但 `setLineDash` 等 Canvas API 在舊 IE 無效
6. **無自動資料更新**：CSV 是預先產出的靜態檔；如需從資料庫動態查詢，需後端 API

---

## 相關資源

- **flot 官方網站**：http://www.flotcharts.org/
- **flot GitHub**：https://github.com/flot/flot
- **jQuery 官方網站**：https://jquery.com/
- **專案內相關檔案**：
  - `doc/2026-06-06-bed-profile-flot-design.md`：本檔的設計文件
  - `doc/2026-06-06-conversation-log.md`：今日開發對話紀錄
  - `doc/對話.txt`：原始需求
  - `doc/河道斷面底床最低點高程沿程圖計畫.txt`：Python 版（matplotlib）對應計畫
  - `get_cross_section.py`：斷面圖繪製風格參考
  - `plot_river_bed_profile.py`：matplotlib 版（產出 CSV 資料）
  - `plot_river_bed_profile.html`：echarts 版（對照組）
