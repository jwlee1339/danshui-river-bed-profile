# get_cross_section.py
# 2026-06-04
# 查詢河道斷面並繪圖
# 使用方法:
#   單年: python get_cross_section.py M12.4 --dbname Y2023 --output_dir ./寶橋 --water_level 12.0
#   多年: python get_cross_section.py M12.4 --start_year 2012 --end_year 2025 --output_dir ./寶橋

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.font_manager as fm
import argparse
import os
from dotenv import load_dotenv

from src.mssql_utils import MssqlUtils

river_ids = ['TE', 'H', 'KE', 'F', 'M', 'N', 'S']

# 查詢指定河段所有斷面名稱
def look_section_names(riverid: str):
    # 使用 :riverid 作為參數預留位置，防止 SQL 注入
    sql = f"""
    SELECT Section_ID, River_ID
    FROM MAP2.dbo.Cross_Section_administration
    WHERE River_ID = :riverid
    ORDER BY Section_ID;
    """
    return MssqlUtils.query_to_df(sql, dbname='MAP2', params={'riverid': riverid})

# 設定 Matplotlib 以支援中文顯示

def setup_matplotlib_chinese_font():
    """設定 Matplotlib 以支援中文顯示。"""
    # 嘗試尋找常見的繁體中文字體
    font_names = ['Microsoft JhengHei', '微軟正黑體', 'Heiti TC', 'PingFang TC']
    found_font = None
    for font_name in font_names:
        try:
            # findfont 會在系統中尋找字體並回傳路徑
            font_path = fm.findfont(fm.FontProperties(family=font_name))
            if font_path:
                plt.rcParams['font.family'] = font_name
                print(f"成功設定字體: {font_name}")
                found_font = font_name
                break
        except Exception:
            continue
    
    if not found_font:
        print("警告: 找不到指定的中文字體，圖表中的中文可能無法正常顯示。")

def gen_sql(dbname:str):
    """產生查詢斷面點位的 SQL 語法範本。"""
    # 使用 :param_name 作為參數預留位置
    sql = f"""
    SELECT Section_ID, Pt, Y, Z
    FROM {dbname}.dbo.Cross_Section_PT
    where Section_ID = :secid
    ORDER BY Y
    """
    return sql

def cal_top_width(y: np.ndarray, z: np.ndarray, water_level:float):
    """計算水面寬度。"""
    # 逐段計算線段寬度
    top_width = 0.0
    for i in range(len(y) - 1):
        y1, y2 = float(y[i]), float(y[i+1])
        z1, z2 = float(z[i]), float(z[i+1])
        if z1 < water_level and z2 < water_level:
            top_width += y2-y1
        # 待辦: 計算交叉點
    return top_width
    

def plot_cross_section(df: pd.DataFrame, secid: str, save_path: str | None = None, water_level: float | None = None, fig: Figure | None = None, year: str | None = None):
    """根據 DataFrame 繪製並儲存斷面圖。"""
    if df.empty:
        print("沒有資料可供繪圖。")
        return None

    # 如果沒有傳入現有的 figure，則建立一個新的
    if fig is None:
        fig, ax = plt.subplots(figsize=(12, 6))
    else:
        fig.clear() # 清除現有 figure 的內容
        ax = fig.add_subplot(111)

    ax.plot(df['Y'], df['Z'], linestyle='-', color='black', label=f'斷面 {secid}')

    # --- 計算並標示水理特性 ---
    wetted_area = 0.0
    top_width = 0.0

    # 如果有指定水位，則繪製水位線並填充水域
    if water_level is not None and water_level > df['Z'].min():
        ax.axhline(y=water_level, color='green', linestyle='--', linewidth=2, label=f'指定水位: {water_level:.2f} m')
        ax.fill_between(df['Y'], df['Z'], water_level, where=(df['Z'] < water_level), color='lightblue', alpha=0.5, label='水域')

        # 準備計算所需的資料
        y = df['Y'].values
        z = df['Z'].values

        # 計算水面寬 (Top Width) 和交點
        # 找出所有在水面下的點，以及水位線與斷面線的交點
        wet_points_y = y[z < water_level].tolist()

        for i in range(len(y) - 1):
            # 檢查水位線是否與此線段相交
            if (z[i] < water_level and z[i+1] > water_level) or \
               (z[i] > water_level and z[i+1] < water_level):
                # 使用線性內插法計算交點的 Y 座標
                y_intersect = y[i] + (y[i+1] - y[i]) * (water_level - z[i]) / (z[i+1] - z[i])
                wet_points_y.append(y_intersect)
        
        if wet_points_y:
            # 計算水面寬度 - 應改為逐段累積
            top_width = cal_top_width(y, z, water_level)
            
            min_y = min(wet_points_y)
            max_y = max(wet_points_y)
            
            intersections = [min_y, max_y] # 更新交點為最左和最右點

            # 1. 計算通水面積 (Wetted Area) - 逐段累加法
            # 這種方法可以正確處理中間有島嶼或高地的複雜斷面
            wetted_area = 0.0
            for i in range(len(y) - 1):
                y1, y2 = float(y[i]), float(y[i+1])
                z1, z2 = float(z[i]), float(z[i+1])

                # 將線段兩端高程高於水位的部分，裁剪至水位高度
                h1 = water_level - min(z1, float(water_level))
                h2 = water_level - min(z2, float(water_level))
                
                # 計算這個小梯形的面積並累加
                wetted_area += (h1 + h2) * (y2 - y1) / 2

            # 如果有計算水理特性，則在圖表上顯示
            if top_width > 0 and wetted_area > 0:
                info_text = (f'水位: {water_level:.2f} m\n'
                             f'水面寬度: {top_width:.2f} m\n'
                             f'通水面積: {wetted_area:.2f} m²')
                # 將文字放在水位線上方，並水平置中於水面
                x_center = (min(intersections) + max(intersections)) / 2
                ax.text(x_center, water_level + 0.1, info_text, fontsize=10,
                        verticalalignment='bottom', horizontalalignment='center',
                        bbox=dict(boxstyle='round,pad=0.5', fc='wheat', alpha=0.8))



    year_str = f' ({year})' if year else ''
    title = f'河道斷面圖 - {secid}{year_str}'
    ax.set_title(title, fontsize=20, pad=20)
    ax.set_xlabel('橫向距離 (m)', fontsize=12)
    ax.set_ylabel('高程 (m)', fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax.legend()

    # --- 標註地形特徵點 ---
    if not df.empty:
        # 1. 找到並標註主深槽 (Thalweg)
        thalweg = df.loc[df['Z'].idxmin()]
        ax.plot(thalweg['Y'], thalweg['Z'], 'bv', markersize=8, label='主深槽 (Thalweg)')
        ax.annotate(f'主深槽高程: {thalweg["Z"]:.2f} m',
                    xy=(thalweg['Y'], thalweg['Z']),
                    xytext=(0, -40), textcoords='offset points',
                    ha='center',
                    arrowprops=dict(facecolor='black', arrowstyle='->'),
                    bbox=dict(boxstyle='round,pad=0.3', fc='cyan', alpha=0.7))

        # 2. 將資料分為左岸和右岸
        df_left = df[df['Y'] <= thalweg['Y']]
        df_right = df[df['Y'] > thalweg['Y']]

        # 3. 找出並標註左岸最高點 (高灘地)
        if not df_left.empty:
            left_high_point = df_left.loc[df_left['Z'].idxmax()]
            ax.plot(left_high_point['Y'], left_high_point['Z'], 'ro', markersize=6, label='岸頂點')
            ax.annotate(f'左岸最高點: {left_high_point["Z"]:.2f} m',
                        xy=(left_high_point['Y'], left_high_point['Z']),
                        xytext=(-60, 30), textcoords='offset points',
                        arrowprops=dict(facecolor='red', arrowstyle='->', shrinkA=5, shrinkB=5),
                        bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.7))

        # 4. 找出並標註右岸最高點 (高灘地)
        if not df_right.empty:
            right_high_point = df_right.loc[df_right['Z'].idxmax()]
            ax.plot(right_high_point['Y'], right_high_point['Z'], 'ro', markersize=6) # 使用相同標記，不重複加入圖例
            ax.annotate(f'右岸最高點: {right_high_point["Z"]:.2f} m',
                        xy=(right_high_point['Y'], right_high_point['Z']),
                        xytext=(10, 30), textcoords='offset points',
                        arrowprops=dict(facecolor='red', arrowstyle='->', shrinkA=5, shrinkB=5),
                        bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.7))

    # 根據公式計算 Y 軸最大值
    min_z = df['Z'].min()
    max_z = df['Z'].max()
    y_max_limit = min_z + (max_z - min_z) * 1.66
    ax.set_ylim(top=y_max_limit)

    # 調整 Y 軸顯示，'auto' 會自動調整比例以填滿畫布，達到放大效果
    ax.set_aspect('auto')
    # ax.invert_yaxis() # 根據要求，不再反轉 Y 軸

    if save_path:
        fig.tight_layout()
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"已儲存斷面圖至 '{save_path}'")
    
    return fig

def main():
    """主執行函式。"""
    # 從 .env 檔案載入環境變數
    load_dotenv()

    parser = argparse.ArgumentParser(description="從資料庫查詢指定河道斷面並繪製圖形。")
    parser.add_argument("secid", help="要查詢的斷面 ID (例如: 12-1)。")
    parser.add_argument("--dbname", help="要查詢的資料庫名稱。若未提供，則使用 .env 檔案中的 DB_NAME。")
    parser.add_argument("--output_dir", default='.', help="儲存圖檔的目錄 (預設: 當前目錄)。")
    parser.add_argument("--water_level", type=float, help="在圖上標示指定的水位線 (例如: 15.5)。")
    parser.add_argument("--start_year", type=int, help="起始年份 (啟用多年模式，查詢該年至 end_year 的資料並合併)。")
    parser.add_argument("--end_year", type=int, default=2025, help="結束年份 (預設: 2025，需搭配 start_year 使用)。")
    args = parser.parse_args()

    setup_matplotlib_chinese_font()
    os.makedirs(args.output_dir, exist_ok=True)
    safe_secid = args.secid.replace(os.path.sep, '_').replace('/', '_').replace('\\', '_')

    # --- 多年模式：查詢 start_year ~ end_year 的資料並合併 ---
    if args.start_year is not None:
        all_dfs = []
        years_with_data = []
        for year in range(args.start_year, args.end_year + 1):
            dbname = f"Y{year}"
            sql_query = gen_sql(dbname)
            sql_params = {"secid": args.secid}
            print(f"正在從資料庫 '{dbname}' 查詢斷面 '{args.secid}'...")
            df = MssqlUtils.query_to_df(sql_query, dbname=dbname, params=sql_params)
            if df is not None and not df.empty:
                df['year'] = str(year)
                all_dfs.append(df)
                years_with_data.append(str(year))
                print(f"  ✔ 取得 {len(df)} 筆資料")
            else:
                print(f"  ✗ 無資料")

        if all_dfs:
            df_combined = pd.concat(all_dfs, ignore_index=True)
            csv_path = os.path.join(args.output_dir, f'{safe_secid.replace("-", "_")}_{args.start_year}-{args.end_year}.csv')
            df_combined.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"\n已儲存合併斷面數據至 '{csv_path}' ({len(years_with_data)} 年, 共 {len(df_combined)} 筆)")

            fig, ax = plt.subplots(figsize=(12, 6))
            colors = plt.cm.viridis(np.linspace(0, 1, len(all_dfs)))
            for i, year_df in enumerate(all_dfs):
                ax.plot(year_df['Y'], year_df['Z'], linestyle='-', color=colors[i], label=year_df['year'].iloc[0])
            ax.set_title(f'河道斷面疊圖 - {args.secid} ({args.start_year}~{args.end_year})', fontsize=20, pad=20)
            ax.set_xlabel('橫向距離 (m)', fontsize=12)
            ax.set_ylabel('高程 (m)', fontsize=12)
            ax.grid(True, linestyle='--', linewidth=0.5)
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title='年份')
            save_path = os.path.join(args.output_dir, f'{safe_secid.replace("-", "_")}_{args.start_year}-{args.end_year}.png')
            fig.tight_layout()
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"已儲存斷面疊圖至 '{save_path}'")
            plt.show()
        else:
            print("所有年份皆無資料。")
        return

    # --- 單年模式 (原行為) ---
    if not args.dbname and not os.getenv('DB_NAME'):
        print("錯誤: 缺少資料庫名稱。請透過 --dbname 參數或在 .env 檔案中設定 DB_NAME。")
        return

    target_db = args.dbname or os.getenv('DB_NAME')
    year = target_db.lstrip('Y') if target_db else ''

    save_path = os.path.join(args.output_dir, f'{year}_{safe_secid.replace("-", "_")}.png')

    sql_query = gen_sql(target_db)
    sql_params = {"secid": args.secid}

    print(f"正在從資料庫 '{target_db}' 查詢斷面 '{args.secid}'...")
    df_section = MssqlUtils.query_to_df(sql_query, dbname=args.dbname, params=sql_params)

    if df_section is not None and not df_section.empty:
        print(f"成功查詢到 {len(df_section)} 筆資料。")
        fig = plot_cross_section(df_section, args.secid, save_path, water_level=args.water_level, year=year)
        if fig:
            plt.show()

        csv_path = os.path.join(args.output_dir, f'{year}_{safe_secid.replace("-", "_")}.csv')
        df_export = pd.DataFrame({'year': year, 'id': args.secid, 'Y': df_section['Y'], 'Z': df_section['Z']})
        df_export.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"已儲存斷面數據至 '{csv_path}'")
    elif df_section is not None:
        print("查詢成功，但未找到符合條件的資料。")

if __name__ == '__main__':
    main()