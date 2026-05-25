#!/usr/bin/env python3
"""Build multi-period Beijing map data from Feishu sheet raw values."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from build_processed_data import build, fetch_geojson


def rows_to_records(values: list[list], period: str) -> list[dict]:
    header = values[0]
    idx = {str(name).strip(): i for i, name in enumerate(header) if name}
    required = ["物理商圈所在行政区", "物理商圈名称", "全量有效POI数", "已开发有效POI_近1d核销GMV"]
    missing = [name for name in required if name not in idx]
    if missing:
        raise SystemExit(f"{period} missing columns: {', '.join(missing)}")
    records = []
    for row_no, row in enumerate(values[1:], start=2):
        district = str(row[idx["物理商圈所在行政区"]] or "").strip() if idx["物理商圈所在行政区"] < len(row) else ""
        area = str(row[idx["物理商圈名称"]] or "").strip() if idx["物理商圈名称"] < len(row) else ""
        if not district or not area:
            continue
        records.append({
            "row": row_no,
            "period": period,
            "industry": "全部行业",
            "district": district,
            "tradeArea": area,
            "heat": float(row[idx["全量有效POI数"]] or 0),
            "bubble": float(row[idx["已开发有效POI_近1d核销GMV"]] or 0),
        })
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-input", default="data/feishu_periods_raw.json")
    parser.add_argument("--geojson-output", default="data/beijing_districts.geojson")
    parser.add_argument("--geocode-cache", default="data/geocode_cache.json")
    parser.add_argument("--processed-output", default="data/processed.json")
    parser.add_argument("--geojson-js-output", default="data/beijing_districts.js")
    parser.add_argument("--processed-js-output", default="data/processed.js")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw = json.loads(Path(args.raw_input).read_text(encoding="utf-8"))
    geojson = fetch_geojson(Path(args.geojson_output))
    periods = list(raw.keys())
    industries = ["全部行业"]
    datasets = {}
    period_summaries = []

    for period in periods:
        records = rows_to_records(raw[period], period)
        build_args = SimpleNamespace(
            input=args.raw_input,
            district_col="物理商圈所在行政区",
            area_col="物理商圈名称",
            heat_col="全量有效POI数",
            bubble_col="已开发有效POI_近1d核销GMV",
            title="北京市分时段商圈交易情况",
            eyebrow="北京行政区 POI 热力 + 商圈核销 GMV 气泡",
            heat_label="门店 / POI 数",
            bubble_label="核销 GMV",
            heat_legend_high="门店多",
            heat_legend_low="门店少",
            bubble_metric_format="yi",
            note="商圈散点优先使用公共地理编码，并校验落在所属行政区边界内；未识别商圈回退到行政区 AOI 内确定性错位。",
        )
        processed = build(records, geojson, Path(args.geocode_cache), 0, True, build_args)
        datasets.setdefault(period, {})["全部行业"] = {
            "districts": processed["districts"],
            "scatter": processed["scatter"],
            "meta": processed["meta"],
        }
        period_summaries.append({
            "period": period,
            "tradeAreaRows": processed["meta"]["tradeAreaRows"],
            "heatTotal": processed["meta"]["heatTotal"],
            "bubbleTotal": processed["meta"]["bubbleTotal"],
        })

    first = datasets[periods[0]]["全部行业"]
    output = {
        "meta": {
            "title": "北京市分时段商圈交易情况",
            "eyebrow": "北京行政区 POI 热力 + 商圈核销 GMV 气泡",
            "heatLabel": "门店 / POI 数",
            "bubbleLabel": "核销 GMV",
            "heatLegendHigh": "门店多",
            "heatLegendLow": "门店少",
            "bubbleMetricFormat": "yi",
            "periods": periods,
            "industries": industries,
            "defaultPeriod": periods[0],
            "defaultIndustry": "全部行业",
            "periodSummaries": period_summaries,
            "note": "四个时段来自飞书表四个 sheet；当前表未提供行业列，行业筛选默认全部行业。",
        },
        "periods": periods,
        "industries": industries,
        "datasets": datasets,
        "districts": first["districts"],
        "scatter": first["scatter"],
    }

    Path(args.processed_output).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.geojson_js_output).write_text(
        "window.BEIJING_GEOJSON = " + json.dumps(geojson, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    Path(args.processed_js_output).write_text(
        "window.BEIJING_PROCESSED = " + json.dumps(output, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print(json.dumps(output["meta"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
