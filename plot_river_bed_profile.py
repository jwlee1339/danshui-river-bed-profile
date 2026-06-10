# plot_river_bed_profile.py
# 2026-06-05
# Plot river bed thalweg elevation profile by cumulative distance from outlet.
# 使用說明:
# 1. 確保已安裝必要套件: pip install matplotlib pandas python-dotenv pyodbc
# 2. 執行腳本，提供河道編號、起始年、結束年、輸出目錄，及斷面基本資料 CSV (可選):
#    python plot_river_bed_profile.py M 2012 2025 output --cs_csv cs_property/2026_cs.csv
#   其中 M 是河道編號，2012 是起始年，2025 是結束年，output 是輸出目錄。
# 3. 圖表將顯示河道斷面底床最低點高程沿程變化，並儲存為 "{River_ID}_{start_year}-{end_year}_bed_min_profile.png"。
# 注意:
# - 斷面基本資料 CSV 預設為 cs_property/2026_cs.csv，應包含 "Section_ID", "River_ID", "Cum_Distance" 欄位。
# - 輸出 CSV 包含每年每個斷面的最低點高程資料，缺資料的斷面會在 warnings CSV 中列出。
# 使用例:
# python plot_river_bed_profile.py M 2012 2025 output --cs_csv cs_property/2026_cs.csv --show

import argparse
import os
from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dotenv import load_dotenv

from src.mssql_utils import MssqlUtils


REQUIRED_CS_COLUMNS = ["Section_ID", "River_ID", "Cum_Distance"]


def setup_matplotlib_chinese_font() -> None:
    """Set a Traditional Chinese font when available."""
    font_names = [
        "Microsoft JhengHei",
        "Noto Sans CJK TC",
        "Noto Sans TC",
        "PingFang TC",
        "Heiti TC",
    ]

    for font_name in font_names:
        try:
            font_path = fm.findfont(
                fm.FontProperties(family=font_name),
                fallback_to_default=False,
            )
        except Exception:
            continue

        if font_path:
            plt.rcParams["font.sans-serif"] = [font_name]
            plt.rcParams["font.family"] = "sans-serif"
            break

    plt.rcParams["axes.unicode_minus"] = False


def read_cross_section_property(
    csv_path: Path,
    river_id: str,
    distance_start: float | None = None,
    distance_end: float | None = None,
) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"找不到斷面基本資料檔案: {csv_path}")

    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    missing_columns = [col for col in REQUIRED_CS_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(
            "斷面基本資料缺少必要欄位: " + ", ".join(missing_columns)
        )

    df = df[REQUIRED_CS_COLUMNS].copy()
    df["River_ID"] = df["River_ID"].astype(str).str.strip()
    df["Section_ID"] = df["Section_ID"].astype(str).str.strip()
    df["Cum_Distance"] = pd.to_numeric(df["Cum_Distance"], errors="coerce")

    df_river = df[df["River_ID"] == river_id].copy()
    df_river = df_river.dropna(subset=["Section_ID", "Cum_Distance"])

    if distance_start is not None:
        df_river = df_river[df_river["Cum_Distance"] >= distance_start]
    if distance_end is not None:
        df_river = df_river[df_river["Cum_Distance"] <= distance_end]

    df_river = df_river.sort_values("Cum_Distance").reset_index(drop=True)

    if df_river.empty:
        distance_text = ""
        if distance_start is not None or distance_end is not None:
            start_text = "-inf" if distance_start is None else str(distance_start)
            end_text = "inf" if distance_end is None else str(distance_end)
            distance_text = f"，距離範圍 {start_text} 到 {end_text}"
        raise ValueError(f"找不到 River_ID = {river_id}{distance_text} 的斷面資料")

    return df_river


def gen_section_point_sql(dbname: str) -> str:
    return f"""
    SELECT Section_ID, Pt, Y, Z
    FROM {dbname}.dbo.Cross_Section_PT
    WHERE Section_ID = :secid
    ORDER BY Section_ID, Y
    """


def query_section_min_z(dbname: str, section_id: str) -> tuple[float | None, str | None]:
    sql = gen_section_point_sql(dbname)
    df = MssqlUtils.query_to_df(sql, dbname=dbname, params={"secid": section_id})

    if df is None:
        return None, "query_failed"
    if df.empty:
        return None, "no_points"
    if "Z" not in df.columns:
        return None, "missing_z_column"

    z_values = pd.to_numeric(df["Z"], errors="coerce").dropna()
    if z_values.empty:
        return None, "no_valid_z"

    return float(z_values.min()), None


def collect_profile_data(
    df_sections: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    records = []
    warnings = []

    for year in range(start_year, end_year + 1):
        dbname = f"Y{year}"
        print(f"處理年份 {year} ({dbname})...")

        for row in df_sections.itertuples(index=False):
            section_id = str(row.Section_ID)
            min_z, warning = query_section_min_z(dbname, section_id)

            if warning:
                warnings.append(
                    {
                        "year": year,
                        "River_ID": row.River_ID,
                        "Section_ID": section_id,
                        "Cum_Distance": row.Cum_Distance,
                        "warning": warning,
                    }
                )
                print(f"  警告: {year} {section_id} {warning}")
                continue

            records.append(
                {
                    "year": year,
                    "River_ID": row.River_ID,
                    "Section_ID": section_id,
                    "Cum_Distance": float(row.Cum_Distance),
                    "min_Z": min_z,
                }
            )

    df_profile = pd.DataFrame(
        records,
        columns=["year", "River_ID", "Section_ID", "Cum_Distance", "min_Z"],
    )
    df_warnings = pd.DataFrame(
        warnings,
        columns=["year", "River_ID", "Section_ID", "Cum_Distance", "warning"],
    )

    if not df_profile.empty:
        df_profile = df_profile.sort_values(
            ["year", "Cum_Distance", "Section_ID"]
        ).reset_index(drop=True)

    return df_profile, df_warnings


def plot_profile(
    df_profile: pd.DataFrame,
    df_sections: pd.DataFrame,
    river_id: str,
    start_year: int,
    end_year: int,
    save_path: Path,
    section_label_step: int = 1,
) -> None:
    if df_profile.empty:
        raise ValueError("沒有可繪製的斷面最低點高程資料")

    setup_matplotlib_chinese_font()

    fig, ax = plt.subplots(figsize=(13, 7))
    years = sorted(df_profile["year"].unique())
    colors = plt.cm.viridis(np.linspace(0, 1, len(years)))

    for color, year in zip(colors, years):
        df_year = df_profile[df_profile["year"] == year].sort_values("Cum_Distance")
        ax.plot(
            df_year["Cum_Distance"],
            df_year["min_Z"],
            marker="o",
            linestyle="-",
            linewidth=1.8,
            markersize=4,
            color=color,
            label=str(year),
        )

    ax.set_title(
        f"{river_id} 河道斷面底床最低點高程沿程變化 {start_year}-{end_year}",
        fontsize=16,
        pad=16,
    )
    ax.set_xlabel("斷面至河道出口累積距離 Cum_Distance (m)", fontsize=12)
    ax.set_ylabel("斷面底床最低點高程 min Z (m)", fontsize=12)
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.7)
    ax.legend(title="年份", bbox_to_anchor=(1.02, 1), loc="upper left")

    label_step = max(1, int(section_label_step))
    df_label = df_sections.iloc[::label_step].copy()
    ax_top = ax.twiny()
    ax_top.set_xlim(ax.get_xlim())
    ax_top.set_xticks(df_label["Cum_Distance"])
    ax_top.set_xticklabels(
        df_label["Section_ID"],
        rotation=90,
        fontsize=8,
        va="bottom",
    )
    ax_top.set_xlabel("斷面編號 Section_ID", fontsize=12, labelpad=10)
    ax_top.tick_params(axis="x", pad=2)

    fig.tight_layout()
    fig.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="繪製河道斷面底床最低點高程與斷面至河道出口累積距離沿程圖"
    )
    parser.add_argument("river_id", help="河道編號，例如 M、F、H、KE")
    parser.add_argument("start_year", type=int, help="起始西元年，例如 2012")
    parser.add_argument("end_year", type=int, help="結束西元年，例如 2025")
    parser.add_argument("output_dir", help="輸出目錄")
    parser.add_argument(
        "--cs_csv",
        default="cs_property/2026_cs.csv",
        help="斷面基本資料 CSV，預設為 cs_property/2026_cs.csv",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="輸出後顯示 matplotlib 視窗",
    )
    parser.add_argument(
        "--section_label_step",
        type=int,
        default=1,
        help="上方 X 軸斷面編號標註間隔，預設 1 表示全部標註",
    )
    parser.add_argument(
        "--distance_start",
        type=float,
        help="斷面至河道出口累積距離篩選起點，包含此距離",
    )
    parser.add_argument(
        "--distance_end",
        type=float,
        help="斷面至河道出口累積距離篩選終點，包含此距離",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()

    if args.start_year > args.end_year:
        print("錯誤: 起始西元年不可大於結束西元年")
        return 1
    if (
        args.distance_start is not None
        and args.distance_end is not None
        and args.distance_start > args.distance_end
    ):
        print("錯誤: 距離篩選起點不可大於終點")
        return 1

    river_id = args.river_id.strip()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        df_sections = read_cross_section_property(
            Path(args.cs_csv),
            river_id,
            args.distance_start,
            args.distance_end,
        )
    except Exception as exc:
        print(f"錯誤: {exc}")
        return 1

    if args.distance_start is not None or args.distance_end is not None:
        start_text = "-inf" if args.distance_start is None else args.distance_start
        end_text = "inf" if args.distance_end is None else args.distance_end
        print(
            f"找到 {len(df_sections)} 個 {river_id} 河道斷面，"
            f"距離範圍 {start_text} 到 {end_text} m"
        )
    else:
        print(f"找到 {len(df_sections)} 個 {river_id} 河道斷面")

    df_profile, df_warnings = collect_profile_data(
        df_sections,
        args.start_year,
        args.end_year,
    )

    file_prefix = f"{river_id}_{args.start_year}-{args.end_year}_bed_min_profile"
    csv_path = output_dir / f"{file_prefix}.csv"
    warning_path = output_dir / f"{file_prefix}_warnings.csv"
    png_path = output_dir / f"{file_prefix}.png"

    df_profile.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"已輸出資料 CSV: {csv_path}")

    if not df_warnings.empty:
        df_warnings.to_csv(warning_path, index=False, encoding="utf-8-sig")
        print(f"已輸出缺資料警告 CSV: {warning_path}")

    try:
        plot_profile(
            df_profile,
            df_sections,
            river_id,
            args.start_year,
            args.end_year,
            png_path,
            args.section_label_step,
        )
    except Exception as exc:
        print(f"錯誤: {exc}")
        return 1

    print(f"已輸出圖檔: {png_path}")

    if args.show:
        setup_matplotlib_chinese_font()
        image = plt.imread(png_path)
        plt.figure(figsize=(12, 6))
        plt.imshow(image)
        plt.axis("off")
        plt.show()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
