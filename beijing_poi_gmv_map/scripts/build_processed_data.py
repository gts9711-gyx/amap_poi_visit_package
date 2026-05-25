#!/usr/bin/env python3
"""Build processed data for reusable Beijing district heatmap + trade-area bubble map."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import time
import urllib.request
import urllib.parse
from collections import defaultdict
from pathlib import Path

import openpyxl


INPUT_DEFAULT = "/Users/bytedance/Downloads/未保存的查询-2026-05-25 23-52-34.xlsx"
DATAV_URL = "https://geo.datav.aliyun.com/areas_v3/bound/110000_full.json"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
GOLDEN_ANGLE = math.pi * (3 - math.sqrt(5))


def fetch_geojson(output_path: Path) -> dict:
    if output_path.exists():
        return json.loads(output_path.read_text(encoding="utf-8"))
    request = urllib.request.Request(
        DATAV_URL,
        headers={"User-Agent": "Mozilla/5.0 (Codex map renderer)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read().decode("utf-8")
    output_path.write_text(payload, encoding="utf-8")
    return json.loads(payload)


def clean_district(name: str) -> str:
    return str(name).strip()


def read_excel(path: Path, district_col: str, area_col: str, heat_col: str, bubble_col: str) -> list[dict]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise SystemExit("Excel is empty")
    header = [str(v).strip() for v in rows[0]]
    required = [district_col, area_col, heat_col, bubble_col]
    missing = [name for name in required if name not in header]
    if missing:
        raise SystemExit(f"Missing columns: {', '.join(missing)}")
    idx = {name: header.index(name) for name in required}
    records = []
    for i, row in enumerate(rows[1:], start=2):
        district = clean_district(row[idx[district_col]])
        area = str(row[idx[area_col]] or "").strip()
        heat = float(row[idx[heat_col]] or 0)
        bubble = float(row[idx[bubble_col]] or 0)
        if not district or not area:
            continue
        records.append({
            "row": i,
            "district": district,
            "tradeArea": area,
            "heat": heat,
            "bubble": bubble,
        })
    return records


def feature_name(feature: dict) -> str:
    props = feature.get("properties") or {}
    return clean_district(props.get("name") or props.get("NAME") or "")


def flatten_rings(geometry: dict) -> list[list[list[float]]]:
    if not geometry:
        return []
    if geometry.get("type") == "Polygon":
        return geometry.get("coordinates") or []
    if geometry.get("type") == "MultiPolygon":
        rings = []
        for polygon in geometry.get("coordinates") or []:
            rings.extend(polygon)
        return rings
    return []


def bbox_for_feature(feature: dict) -> tuple[float, float, float, float]:
    xs, ys = [], []
    for ring in flatten_rings(feature.get("geometry") or {}):
        for lng, lat, *_ in ring:
            xs.append(float(lng))
            ys.append(float(lat))
    return min(xs), min(ys), max(xs), max(ys)


def center_for_feature(feature: dict) -> tuple[float, float]:
    props = feature.get("properties") or {}
    for key in ["centroid", "center"]:
        value = props.get(key)
        if isinstance(value, list) and len(value) >= 2:
            return float(value[0]), float(value[1])
    min_lng, min_lat, max_lng, max_lat = bbox_for_feature(feature)
    return (min_lng + max_lng) / 2, (min_lat + max_lat) / 2


def point_in_ring(point: tuple[float, float], ring: list[list[float]]) -> bool:
    x, y = point
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = float(ring[i][0]), float(ring[i][1])
        xj, yj = float(ring[j][0]), float(ring[j][1])
        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def point_in_feature(point: tuple[float, float], feature: dict) -> bool:
    geometry = feature.get("geometry") or {}
    if geometry.get("type") == "Polygon":
        return point_in_polygon(point, geometry.get("coordinates") or [])
    if geometry.get("type") == "MultiPolygon":
        return any(point_in_polygon(point, polygon) for polygon in geometry.get("coordinates") or [])
    return False


def point_in_polygon(point: tuple[float, float], polygon: list[list[list[float]]]) -> bool:
    if not polygon or not point_in_ring(point, polygon[0]):
        return False
    return not any(point_in_ring(point, hole) for hole in polygon[1:])


def safe_offset_point(center: tuple[float, float], feature: dict, rank: int, count: int) -> tuple[float, float]:
    if count <= 1:
        return center
    min_lng, min_lat, max_lng, max_lat = bbox_for_feature(feature)
    max_radius = min(max_lng - min_lng, max_lat - min_lat) * 0.38
    radius = max_radius * math.sqrt((rank + 0.5) / count)
    angle = rank * GOLDEN_ANGLE
    candidate = (center[0] + math.cos(angle) * radius, center[1] + math.sin(angle) * radius)
    if point_in_feature(candidate, feature):
        return candidate
    for factor in [0.75, 0.55, 0.35, 0.18, 0.08]:
        shrunk = (
            center[0] + (candidate[0] - center[0]) * factor,
            center[1] + (candidate[1] - center[1]) * factor,
        )
        if point_in_feature(shrunk, feature):
            return shrunk
    return (
        center[0] + math.cos(angle) * max_radius * 0.025,
        center[1] + math.sin(angle) * max_radius * 0.025,
    )


def query_candidates(record: dict) -> list[str]:
    area = record["tradeArea"]
    district = record["district"]
    parts = [part.strip() for part in area.replace("／", "/").split("/") if part.strip()]
    candidates = []
    primary = parts[0] if parts else area
    candidates.append(f"北京市 {district} {primary}")
    if primary != area:
        candidates.append(f"北京 {primary}")
    else:
        candidates.append(f"北京 {area}")
    unique = []
    for item in candidates:
        if item not in unique:
            unique.append(item)
    return unique


def geocode_one(query: str) -> tuple[float, float] | None:
    params = urllib.parse.urlencode({
        "format": "json",
        "limit": "1",
        "q": query,
    })
    request = urllib.request.Request(
        f"{NOMINATIM_URL}?{params}",
        headers={"User-Agent": "Codex beijing poi gmv map geocoder"},
    )
    try:
        with urllib.request.urlopen(request, timeout=6) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None
    if not payload:
        return None
    item = payload[0]
    return float(item["lon"]), float(item["lat"])


def load_cache(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(path: Path, cache: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_trade_area_point(record: dict, feature: dict, cache: dict, sleep_seconds: float, offline: bool = False) -> tuple[tuple[float, float] | None, str]:
    cache_key = f"{record['district']}|{record['tradeArea']}"
    cached = cache.get(cache_key)
    if cached:
        if cached.get("lng") is not None and cached.get("lat") is not None:
            point = (float(cached["lng"]), float(cached["lat"]))
            if point_in_feature(point, feature):
                return point, cached.get("query", "cache")
        return None, "cache-miss"

    if offline:
        return None, "offline-fallback"

    for query in query_candidates(record):
        point = geocode_one(query)
        time.sleep(sleep_seconds)
        if point and point_in_feature(point, feature):
            cache[cache_key] = {"lng": round(point[0], 6), "lat": round(point[1], 6), "query": query}
            return point, query
    cache[cache_key] = {"lng": None, "lat": None, "query": None}
    return None, "fallback"


def offset_duplicate_point(point: tuple[float, float], duplicate_rank: int, feature: dict) -> tuple[float, float]:
    if duplicate_rank <= 0:
        return point
    min_lng, min_lat, max_lng, max_lat = bbox_for_feature(feature)
    radius = min(max_lng - min_lng, max_lat - min_lat) * 0.012 * math.sqrt(duplicate_rank)
    angle = duplicate_rank * GOLDEN_ANGLE
    candidate = (point[0] + math.cos(angle) * radius, point[1] + math.sin(angle) * radius)
    if point_in_feature(candidate, feature):
        return candidate
    return point


def scale_symbol(value: float, min_value: float, max_value: float) -> float:
    if max_value <= min_value:
        return 14
    if value <= 0:
        return 5
    t = (math.sqrt(value) - math.sqrt(max(min_value, 0))) / (math.sqrt(max_value) - math.sqrt(max(min_value, 0)) or 1)
    return round(5 + max(0, min(1, t)) * 29, 2)


def build(records: list[dict], geojson: dict, cache_path: Path, sleep_seconds: float, offline_geocode: bool, args: argparse.Namespace) -> dict:
    feature_by_name = {feature_name(feature): feature for feature in geojson.get("features", [])}
    district_names = sorted({record["district"] for record in records})
    missing = [name for name in district_names if name not in feature_by_name]
    if missing:
        raise SystemExit(f"Districts not found in GeoJSON: {', '.join(missing)}")

    district_agg = defaultdict(lambda: {"heat": 0.0, "bubble": 0.0, "tradeAreaCount": 0})
    by_district = defaultdict(list)
    for record in records:
        district_agg[record["district"]]["heat"] += record["heat"]
        district_agg[record["district"]]["bubble"] += record["bubble"]
        district_agg[record["district"]]["tradeAreaCount"] += 1
        by_district[record["district"]].append(record)

    bubble_values = [record["bubble"] for record in records]
    positive_bubbles = [value for value in bubble_values if value > 0]
    min_positive_bubble = min(positive_bubbles) if positive_bubbles else 0
    max_bubble = max(bubble_values) if bubble_values else 0

    districts = []
    scatter = []
    cache = load_cache(cache_path)
    geocoded_count = 0
    fallback_count = 0
    query_sources = defaultdict(int)
    used_points = defaultdict(int)
    resolved_count = 0

    for district in sorted(district_agg):
        feature = feature_by_name[district]
        center = center_for_feature(feature)
        agg = district_agg[district]
        districts.append({
            "name": district,
            "value": round(agg["heat"], 2),
            "heat": round(agg["heat"], 2),
            "bubble": round(agg["bubble"], 2),
            "tradeAreaCount": agg["tradeAreaCount"],
            "center": [round(center[0], 6), round(center[1], 6)],
        })
        areas = sorted(by_district[district], key=lambda item: item["bubble"], reverse=True)
        for rank, record in enumerate(areas):
            point, source = resolve_trade_area_point(record, feature, cache, sleep_seconds, offline_geocode)
            resolved_count += 1
            if resolved_count % 20 == 0:
                save_cache(cache_path, cache)
            if point:
                point_key = f"{point[0]:.4f},{point[1]:.4f}"
                duplicate_rank = used_points[point_key]
                used_points[point_key] += 1
                lng, lat = offset_duplicate_point(point, duplicate_rank, feature)
                geocoded_count += 1
                query_sources[source] += 1
                position_source = "公共地理编码"
            else:
                lng, lat = safe_offset_point(center, feature, rank, len(areas))
                fallback_count += 1
                position_source = "行政区AOI错位"
            scatter.append({
                "name": record["tradeArea"],
                "district": district,
                "value": [round(lng, 6), round(lat, 6), round(record["bubble"], 2)],
                "heat": round(record["heat"], 2),
                "bubble": round(record["bubble"], 2),
                "symbolSize": scale_symbol(record["bubble"], min_positive_bubble, max_bubble),
                "positionSource": position_source,
            })

    save_cache(cache_path, cache)

    district_heats = [item["heat"] for item in districts]
    return {
        "meta": {
            "source": str(Path(args.input)),
            "geojsonSource": DATAV_URL,
            "districtColumn": args.district_col,
            "tradeAreaColumn": args.area_col,
            "heatColumn": args.heat_col,
            "bubbleColumn": args.bubble_col,
            "title": args.title,
            "eyebrow": args.eyebrow,
            "heatLabel": args.heat_label,
            "bubbleLabel": args.bubble_label,
            "heatLegendHigh": args.heat_legend_high,
            "heatLegendLow": args.heat_legend_low,
            "bubbleMetricFormat": args.bubble_metric_format,
            "tradeAreaRows": len(records),
            "districtCount": len(districts),
            "heatTotal": round(sum(record["heat"] for record in records), 2),
            "bubbleTotal": round(sum(record["bubble"] for record in records), 2),
            "maxBubble": round(max_bubble, 2),
            "minDistrictHeat": round(min(district_heats), 2),
            "maxDistrictHeat": round(max(district_heats), 2),
            "medianDistrictHeat": round(statistics.median(district_heats), 2),
            "geocodedTradeAreas": geocoded_count,
            "fallbackTradeAreas": fallback_count,
            "note": args.note,
        },
        "districts": districts,
        "scatter": scatter,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=INPUT_DEFAULT)
    parser.add_argument("--district-col", default="物理商圈所在行政区")
    parser.add_argument("--area-col", default="物理商圈名称")
    parser.add_argument("--heat-col", default="全量有效POI数")
    parser.add_argument("--bubble-col", default="已开发有效POI_近1d核销GMV")
    parser.add_argument("--title", default="北京市全量有效 POI 与核销 GMV 分布")
    parser.add_argument("--eyebrow", default="北京行政区 POI 热力 + 商圈核销 GMV 气泡")
    parser.add_argument("--heat-label", default="全量有效 POI")
    parser.add_argument("--bubble-label", default="核销 GMV")
    parser.add_argument("--heat-legend-high", default="POI 多")
    parser.add_argument("--heat-legend-low", default="POI 少")
    parser.add_argument("--bubble-metric-format", choices=["raw", "yi", "wan"], default="yi")
    parser.add_argument("--note", default="商圈散点优先使用公共地理编码，并校验落在所属行政区边界内；未识别商圈回退到行政区 AOI 内确定性错位。")
    parser.add_argument("--geojson-output", default="data/beijing_districts.geojson")
    parser.add_argument("--processed-output", default="data/processed.json")
    parser.add_argument("--geojson-js-output", default="data/beijing_districts.js")
    parser.add_argument("--processed-js-output", default="data/processed.js")
    parser.add_argument("--geocode-cache", default="data/geocode_cache.json")
    parser.add_argument("--geocode-sleep", type=float, default=0.2)
    parser.add_argument("--offline-geocode", action="store_true", help="Use existing cache only; do not call external geocoding")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    geojson_output = Path(args.geojson_output)
    processed_output = Path(args.processed_output)
    geojson_output.parent.mkdir(parents=True, exist_ok=True)
    processed_output.parent.mkdir(parents=True, exist_ok=True)

    records = read_excel(input_path, args.district_col, args.area_col, args.heat_col, args.bubble_col)
    geojson = fetch_geojson(geojson_output)
    processed = build(records, geojson, Path(args.geocode_cache), args.geocode_sleep, args.offline_geocode, args)
    processed_output.write_text(json.dumps(processed, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.geojson_js_output).write_text(
        "window.BEIJING_GEOJSON = " + json.dumps(geojson, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    Path(args.processed_js_output).write_text(
        "window.BEIJING_PROCESSED = " + json.dumps(processed, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print(json.dumps(processed["meta"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
