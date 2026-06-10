# 河道斷面底床最低點高程沿程圖 — HTML/JS 前端實作計畫

## 一、目標

建立一支 HTML/CSS/JavaScript 網頁，使用 **local Flot v0.8.3** 繪製指定河道在多個年份中的「斷面底床最低點高程」沿程變化折線圖。

## 二、資料來源

直接讀取已產出的 CSV 資料檔案，無後端資料庫連線。

| 河道 | River_ID | CSV 路徑 |
|------|----------|---------|
| 景美溪 | M | data/景美溪/M_2012-2025_bed_min_profile.csv |
| 新店溪 | H | data/新店溪/H_2012-2025_bed_min_profile.csv |
| 基隆河 | KE | data/基隆河/KE_2012-2025_bed_min_profile.csv |
| 三峽河 | S | data/三峽河/S_2012-2025_bed_min_profile.csv |
| 淡水河 | TE | data/淡水河/TE_2012-2025_bed_min_profile.csv |

CSV 欄位：`year`, `River_ID`, `Section_ID`, `Cum_Distance`, `min_Z`

## 三、檔案結構

```
C:\home\02_MIT\2026\09_淡水河沖淤\
├── plot_river_bed_profile_flot.html     # [新增] 單一 HTML，自含 CSS + JS
├── plot_river_bed_profile.html          # [現有, 不動] echarts 版本
├── flot\                                # [現有, 不動] local flot v0.8.3
│   ├── jquery.flot.js
│   ├── jquery.flot.axislabels.js
│   └── jquery.flot.resize.js
├── data\
│   ├── 景美溪\  M_2012-2025_bed_min_profile.csv
│   ├── 新店溪\  H_2012-2025_bed_min_profile.csv
│   ├── 基隆河\  KE_2012-2025_bed_min_profile.csv
│   ├── 三峽河\  S_2012-2025_bed_min_profile.csv
│   └── 淡水河\  TE_2012-2025_bed_min_profile.csv
└── doc\
    └── 2026-06-06-bed-profile-flot-design.md  [本計畫]
```

## 四、外部依賴

| 套件 | 來源 | 原因 |
|------|------|------|
| jQuery 3.x | CDN (jsDelivr) | local flot/ 無 jQuery |
| flot core | local `flot/jquery.flot.js` v0.8.3 | 使用者指定 |
| flot axislabels | local `flot/jquery.flot.axislabels.js` | 提供軸標題 |
| flot resize | local `flot/jquery.flot.resize.js` | 視窗縮放自動重繪 |

不需打包工具、無後端、無 framework。

## 五、使用方式

```bash
python -m http.server 8000
# 開啟 http://localhost:8000/plot_river_bed_profile_flot.html
```

直接以 `file://` 雙擊也能跑（fetch 相對路徑 CSV），但本機 server 較穩。

## 六、使用者操作介面

```
┌──────────────────────────────────────────────────────────┐
│  河道: [景美溪 ▼]  起始年: [2012 ▼]  結束年: [2025 ▼]     │
│  斷面標註間隔: [1]  [繪製] [重設縮放]                     │
│  提示：在圖表上水平拖曳可局部放大                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│             Flot 折線圖區域 (含雙 X 軸)                   │
│                                                          │
│       ┌────────────────────────────┐                     │
│       │ Legend 容器 (右上角)        │                    │
│       │  ● 2012  ● 2013  ...       │                    │
│       └────────────────────────────┘                     │
│                                                          │
│   下軸: 斷面至河道出口累積距離 (m)                        │
│   上軸: 斷面編號 (依 labelStep 過濾)                       │
│   [滑鼠懸停資料點] → 跳出視窗列出該斷面所有年份高程        │
│   [滑鼠拖曳] → 水平框選局部放大                            │
├──────────────────────────────────────────────────────────┤
│  [狀態列] 錯誤 / 資訊訊息                                │
└──────────────────────────────────────────────────────────┘
```

### 控制項說明

| 控制項 | 類型 | 預設 | 說明 |
|--------|------|------|------|
| 河道 | select | 景美溪 (M) | 切換 5 條河，自動重繪並重設縮放 |
| 起始年 | select | 2012 | 2012 ~ 2025 |
| 結束年 | select | 2025 | 2012 ~ 2025 |
| 斷面標註間隔 | number | 1 | 控制上軸斷面編號 tick 密度 |
| 繪製 | button | — | 手動重繪（切換河道/年也會自動重繪，會重設縮放） |
| 重設縮放 | button | 禁用 | 縮放啟用時變可按，回到全範圍 |

## 七、技術細節

### 7.1 HTML 結構

```html
<script src="https://cdn.jsdelivr.net/npm/jquery@3/dist/jquery.min.js"></script>
<script src="flot/jquery.flot.js"></script>
<script src="flot/jquery.flot.axislabels.js"></script>
<script src="flot/jquery.flot.resize.js"></script>

<div class="controls"> ... 3 select + 1 number + 2 button + 提示 ... </div>
<div id="chart-container">
    <div id="zoom-selection"></div>          <!-- 拖曳時的選取框 -->
    <div id="legend-container"><div id="legend"></div></div>
    <div id="chart" style="height:550px;"></div>
</div>
<div id="status"></div>
<div id="tooltip"></div>                      <!-- hover 跳出視窗 -->
```

### 7.2 CSV 載入與解析

- `fetch()` 載入
- 自寫解析器：去 BOM (`\uFEFF`)、行分割、`split(',')`、取 5 欄
- 解析後存入 `cachedData[riverId]`，後續切換年份不 reload

### 7.3 繪圖邏輯

```javascript
function doPlot() {
  // 1. 讀 UI 值
  var riverId    = $('#river').val();
  var startYear  = +$('#startYear').val();
  var endYear    = +$('#endYear').val();
  var labelStep  = +$('#labelStep').val() || 1;

  // 2. 篩選 + 分組
  var filtered = cachedData[riverId].filter(d =>
    d.year >= startYear && d.year <= endYear);
  var groups = {};  // year -> [[Cum_Distance, min_Z], ...]
  filtered.forEach(d => {
    (groups[d.year] = groups[d.year] || []).push([d.distance, d.minZ]);
  });

  // 3. 計算 x2axis (斷面編號) 的 ticks
  var sectionMap = {};  // sectionId -> Cum_Distance (取第一筆)
  cachedData[riverId].forEach(d => {
    if (sectionMap[d.section] === undefined)
      sectionMap[d.section] = d.distance;
  });
  var sections = Object.keys(sectionMap).sort(
    (a, b) => sectionMap[a] - sectionMap[b]);
  var x2Ticks = sections
    .map(s => [sectionMap[s], s])
    .filter((_, i) => i % labelStep === 0);

  // 4. viridis 色盤 (14 色)
  var years  = Object.keys(groups).map(Number).sort((a, b) => a - b);
  var series = years.map((y, i) => ({
    label: String(y),
    data:  groups[y].sort((a, b) => a[0] - b[0]),
    color: getViridisColor(i, years.length),
    lines:  { show: true, lineWidth: 1.8 },
    points: { show: true, radius: 3, symbol: 'circle' }
  }));

  // 5. $.plot() 設定
  $.plot($('#chart'), series, {
    legend: {
      show: true,
      container: $('#legend'),
      labelBoxBorderColor: '#ccc',
      noColumns: 4
    },
    xaxis:  { axisLabel: '斷面至河道出口累積距離 (m)' },
    x2axis: {
      ticks: x2Ticks,
      axisLabel: '斷面編號'
    },
    yaxis:  { axisLabel: '斷面底床最低點高程 (m)' },
    grid:   { borderWidth: 1, hoverable: false, clickable: false }
  });
}
```

### 7.4 flot v0.8.3 重點（與 v4 差異）

- 必須用 `$.plot(placeholder, data, options)`，非新版 ES module
- `legend` 用 `container: $('selector')` 指定外部 `<div>`，由 flot 將表格 HTML 注入
- `x2axis` 為內建軸，`ticks: [[x, "label"], ...]` 手動指定即可
- 軸標題透過 `axislabels` plugin 提供（`axisLabel: "..."`）
- 視窗縮放用 `resize` plugin；呼叫 `$.plot.plot(placeholder, data, options).setupGrid()` 重繪

### 7.5 格線樣式

flot 0.8.3 的 `grid.markings` 只支援固定範圍的實線區段，繪製真虛線需逐段拼接。
**簡化方案：** 使用預設淺灰格線（`#f0f0f0`，linewidth 1），與 matplotlib 的 `--` 視覺差異極小。

### 7.6 viridis 色盤

硬編碼 14 色 RGB 陣列（與 `plot_river_bed_profile.html` echarts 版相同）。

### 7.7 局部放大 (Zoom)

flot 0.8.3 沒有 `selection` plugin，採自製實作：

1. 觸發：在 `#chart` 上 `mousedown` 左鍵時，記錄起始像素 x
2. 拖曳：`document.mousemove` 更新選取框（`#zoom-selection`）的 left/width
3. 結束：`document.mouseup` 將像素 x 透過 `xaxis.c2p()` 轉成資料範圍
4. 若選取範圍 < 整體範圍 0.5% 則忽略（避免誤觸）
5. 設定 `zoomState.active = true; xMin, xMax`，呼叫 `plot()` 重繪
6. `plot()` 內：以 zoomState 覆蓋 xaxis/x2axis 範圍，並**重新計算 y 軸範圍**（只看選取 x 範圍內的資料）

**重設縮放按鈕：**
- 預設 disabled；zoomState.active = true 時啟用
- 點擊後清空 zoomState，呼叫 `plot()` 重繪

**自動重設時機：**
- 切換河道、起始年、結束年、點「繪製」按鈕
- 改 labelStep 不重設（需自行按「繪製」或「重設縮放」）

**軸刻度跟著更新：**
- x2axis (斷面編號) 只保留 `[xMin, xMax]` 範圍內的斷面，依 labelStep 過濾
- yaxis 範圍從選取範圍內資料的 min/max 自動推算

### 7.8 Hover 跳出視窗 (Tooltip)

- `grid.hoverable: true; mouseActiveRadius: 25` (預設 10 太近)
- 綁定 `plothover` 事件；`item.datapoint[0]` 為選中斷面距離
- 反查 `distanceToSection[dist]` 得斷面 ID，再從 `sectionYearZ[section]` 取得各年份高程
- 顯示為 `position: fixed` 小視窗，含斷面名稱、距離、與年份×高程表格
- 自動貼齊游標 14px，靠近右/下邊界時翻向左/上
- 拖曳開始時 `hideTooltip()` 避免干擾

## 八、錯誤處理

| 情境 | 處理方式 |
|------|---------|
| CSV 載入失敗 (404 / 網路) | 狀態列紅字「無法載入資料檔案，請確認 HTTP server 已啟動」 |
| 選擇的年份範圍內無資料 | 狀態列「所選年份範圍內無資料」 |
| CSV 欄位不符 | 狀態列「資料格式錯誤：缺少 year/Section_ID/Cum_Distance/min_Z」 |
| start_year > end_year | 按鈕按下時 inline 紅字提示，不繪圖 |
| 中文字型支援 | CSS `font-family: 'Microsoft JhengHei', 'Noto Sans TC', sans-serif;` |

## 九、風格參考

參考 `get_cross_section.py` 與 `plot_river_bed_profile.py` 的 matplotlib 繪圖風格：

- viridis 色盤
- marker 圓點 (radius 3)
- 圖例靠右上，標題「年份」 (由 4 欄排版)
- 圖表標題：`{River_ID} 河道斷面底床最低點高程沿程變化 {start_year}-{end_year}` (在 controls 上方 H2)

## 十、產出檔案

| 檔案 | 動作 |
|------|------|
| `plot_river_bed_profile_flot.html` | 新增（專案根目錄） |
| `doc/2026-06-06-bed-profile-flot-design.md` | 更新為本版本 |

## 十一、測試方式

啟動 `python -m http.server 8000` 後依序測試：

1. 各河道（景美溪、新店溪、基隆河、三峽河、淡水河）載入是否正常
2. 不同年份範圍（如 2012-2015、2020-2025）是否正確篩選
3. 斷面標註間隔（1、2、5）是否正確顯示在上軸
4. 錯誤情境：不存在的河道、start > end、無資料年份
5. 圖表外觀：色盤、圖例、標題、格線、雙 X 軸對齊
6. 視窗縮放後圖表自動重繪（resize plugin）
7. 滑鼠懸停資料點 → 跳出視窗列出該斷面所有年份高程
8. 滑鼠拖曳 → 水平框選局部放大（X 軸與 Y 軸皆跟著重算）
9. 「重設縮放」按鈕 → 回到全範圍
10. 切換河道 / 年份 → 自動重設縮放
11. 微小拖曳 (<0.5%) → 不放大
