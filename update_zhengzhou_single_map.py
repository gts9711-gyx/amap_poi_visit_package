import csv
import html
import json
import math
import re
import urllib.parse
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
XLSX = Path("/Users/bytedance/Downloads/【郑州】面饮情况 - 团队x品类x门店明细-2026-04-29.xlsx")


def clean(value):
    if value is None:
        return "-"
    if isinstance(value, float) and math.isnan(value):
        return "-"
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return "-"
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1].strip()
    return text or "-"


def clean_number(value):
    text = clean(value)
    if text == "-":
        return "0"
    try:
        num = float(text)
    except ValueError:
        return text
    if num.is_integer():
        return str(int(num))
    return f"{num:.2f}"


def valid_coord(lng, lat):
    return 70 <= lng <= 140 and 10 <= lat <= 60


def poi_key(point):
    poi_id = clean(point.get("POI ID"))
    if poi_id != "-":
        return f"poi:{poi_id}"
    return "coord:{:.6f},{:.6f}:{}".format(
        float(point["经度"]),
        float(point["纬度"]),
        clean(point.get("POI名称")),
    )


def normalize_existing(point):
    city = clean(point.get("城市"))
    position = clean(point.get("位置"))
    color = "#2563eb" if city == "北京" else "#16a34a"
    return {
        "城市": city,
        "位置": position,
        "来源": "原位置点位",
        "POI名称": clean(point.get("POI名称")),
        "地址": clean(point.get("地址")),
        "经度": float(point.get("经度")),
        "纬度": float(point.get("纬度")),
        "小组": clean(point.get("小组")),
        "BDM": clean(point.get("BDM")),
        "BD": clean(point.get("BD")),
        "商家ID": clean(point.get("商家ID")),
        "门店ID": clean(point.get("门店ID")),
        "品牌ID": clean(point.get("品牌ID")),
        "POI ID": clean(point.get("POI ID")),
        "商圈类型": clean(point.get("商圈类型")),
        "经营大类": clean(point.get("经营大类")),
        "营业状态": clean(point.get("营业状态")),
        "是否认领": clean(point.get("是否认领")),
        "是否在售": clean(point.get("是否在售")),
        "是否动销": clean(point.get("是否动销")),
        "本月GMV": clean_number(point.get("本月GMV")),
        "线下GMV": clean_number(point.get("线下GMV")),
        "商品数": clean_number(point.get("商品数")),
        "搜索次数": clean_number(point.get("搜索次数")),
        "围栏名称": clean(point.get("围栏名称")),
        "颜色值": color,
        "浅色值": "#dbeafe" if city == "北京" else "#dcfce7",
    }


def point_from_row(row):
    lng = float(row["经度[最新]"])
    lat = float(row["纬度[最新]"])
    name = clean(row.get("poi名称[最新]"))
    encoded = urllib.parse.quote(name)
    return {
        "城市": "郑州",
        "位置": "郑州单计全量",
        "来源": "郑州单计全量",
        "POI名称": name,
        "地址": clean(row.get("poi所在地址[最新]")),
        "经度": lng,
        "纬度": lat,
        "小组": clean(row.get("围栏责任小组[当日]")),
        "BDM": clean(row.get("围栏责任bdm[当日]")),
        "BD": clean(row.get("围栏责任bd[当日]")),
        "商家ID": clean(row.get("总户商家ID[最新]")),
        "门店ID": clean(row.get("门店户ID[最新]")),
        "品牌ID": clean(row.get("总户品牌ID[最新]")),
        "POI ID": clean(row.get("poi_id[最新]")),
        "商圈类型": clean(row.get("物理商圈类型_映射")),
        "经营大类": clean(row.get("商圈经营大类_映射")),
        "营业状态": clean(row.get("营业状态_映射")),
        "是否认领": clean(row.get("是否认领")),
        "是否在售": clean(row.get("是否在售")),
        "是否动销": clean(row.get("是否当月动销")),
        "本月GMV": clean_number(row.get("本月核销GMV")),
        "线下GMV": clean_number(row.get("当月线下扫码核销GMV")),
        "商品数": clean_number(row.get("当日在售商品数(T外卖+T直播)")),
        "搜索次数": clean_number(row.get("近30日通过搜索进入poi详情页的次数")),
        "围栏名称": clean(row.get("围栏名称[最新]")),
        "颜色值": "#16a34a",
        "浅色值": "#dcfce7",
        "高德标记链接": f"https://uri.amap.com/marker?position={lng:.6f}%2C{lat:.6f}&name={encoded}&src=codex.poi.visit",
        "高德搜索链接": f"https://www.amap.com/search?query={encoded}",
    }


def load_existing_points():
    text = INDEX.read_text(encoding="utf-8")
    match = re.search(r"const points = (\[.*?\]);\nconst cityOrder", text, re.S)
    if not match:
        raise RuntimeError("Cannot find existing points array")
    return json.loads(match.group(1))


def load_zhengzhou_single_points():
    df = pd.read_excel(XLSX, sheet_name="Sheet1", dtype=str)
    df = df[df["单双计_门店归属"].astype(str).str.strip().eq("单计")].copy()
    df["经度[最新]"] = pd.to_numeric(df["经度[最新]"], errors="coerce")
    df["纬度[最新]"] = pd.to_numeric(df["纬度[最新]"], errors="coerce")
    df = df[df.apply(lambda r: valid_coord(r["经度[最新]"], r["纬度[最新]"]), axis=1)]
    df = df.drop_duplicates(subset=["poi_id[最新]"], keep="first")
    return [point_from_row(row) for _, row in df.iterrows()]


def build_points():
    existing = [
        normalize_existing(p)
        for p in load_existing_points()
        if not (clean(p.get("城市")) == "郑州" and clean(p.get("位置")) == "二七万达补充点位")
    ]
    points = []
    seen = set()
    for point in existing:
        key = poi_key(point)
        if key not in seen:
            points.append(point)
            seen.add(key)
    added_from_excel = 0
    duplicate_from_excel = 0
    for point in load_zhengzhou_single_points():
        key = poi_key(point)
        if key in seen:
            duplicate_from_excel += 1
            continue
        points.append(point)
        seen.add(key)
        added_from_excel += 1
    return points, added_from_excel, duplicate_from_excel


def unique_positions(points):
    preferred = [
        ("北京", "南锣鼓巷-雍和宫-隆福寺", "北京｜南锣鼓巷-雍和宫-隆福寺"),
        ("北京", "王府井-前门-西单", "北京｜王府井-前门-西单"),
        ("北京", "三里屯-朝阳公园-蓝色港湾", "北京｜三里屯-朝阳公园-蓝色港湾"),
        ("北京", "通州万达-北运河-玉桥", "北京｜通州万达-北运河-玉桥"),
        ("郑州", "二七广场-德化街-郑州站", "郑州｜位置一：二七广场-德化街-郑州站"),
        ("郑州", "金水正弘城-花园路-新田360", "郑州｜位置二：金水正弘城-花园路-新田360"),
        ("郑州", "二七万达-大学路-航海路", "郑州｜位置三：二七万达-大学路-航海路"),
        ("郑州", "中牟县城-老县城南北-中县城", "郑州｜位置四：中牟县城-老县城南北-中县城"),
        ("郑州", "郑州单计全量", "郑州｜单计全量新增点位"),
    ]
    counts = {(p["城市"], p["位置"]): 0 for p in points}
    for point in points:
        counts[(point["城市"], point["位置"])] += 1
    out = []
    for city, position, label in preferred:
        if counts.get((city, position), 0):
            out.append({"key": f"{city}｜{position}", "城市": city, "位置": position, "label": label})
    return out


def render_index(points, positions):
    city_counts = {city: sum(1 for p in points if p["城市"] == city) for city in ["北京", "郑州"]}
    title = "北京重点点位 + 郑州单计全量 POI 地图"
    subtitle = f"{len(points)} 个点位｜郑州单计全量 1210 个｜无重复 POI 标记"
    points_json = json.dumps(points, ensure_ascii=False, separators=(",", ":"))
    positions_json = json.dumps(positions, ensure_ascii=False, separators=(",", ":"))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<title>{title}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<style>
  :root {{ --panel: rgba(255,255,255,.95); --text:#111827; --muted:#64748b; --line:#d8dee9; --shadow:0 14px 34px rgba(15,23,42,.18); }}
  html, body, #map {{ height:100%; margin:0; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif; color:var(--text); }}
  #map {{ background:#e5edf3; }}
  .panel {{ position:absolute; z-index:1000; left:14px; top:14px; width:390px; max-width:calc(100vw - 28px); background:var(--panel); backdrop-filter:blur(14px); border:1px solid rgba(209,213,219,.9); border-radius:10px; box-shadow:var(--shadow); overflow:hidden; }}
  .panel-head {{ display:flex; align-items:center; justify-content:space-between; gap:10px; padding:12px 14px; border-bottom:1px solid var(--line); }}
  .title {{ font-size:16px; font-weight:750; line-height:1.25; }}
  .subtitle {{ margin-top:3px; color:var(--muted); font-size:12px; }}
  .toggle {{ display:none; appearance:none; border:1px solid var(--line); background:white; border-radius:8px; padding:7px 9px; font-size:13px; color:#1f2937; }}
  .panel-body {{ padding:12px 14px 14px; max-height:calc(100vh - 120px); overflow:auto; }}
  .section {{ margin-bottom:14px; }}
  .section-title {{ font-size:12px; color:var(--muted); margin-bottom:8px; }}
  .buttons {{ display:grid; gap:8px; }}
  .city-row {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; }}
  .position-btn, .city-btn, .utility-btn {{ appearance:none; border:1px solid var(--line); background:white; border-radius:8px; color:var(--text); cursor:pointer; }}
  .position-btn {{ padding:9px 10px; font-size:13px; line-height:1.25; text-align:left; }}
  .city-btn {{ padding:9px 8px; text-align:center; font-size:12px; }}
  .position-btn.active, .city-btn.active {{ border-color:#16a34a; box-shadow:inset 0 0 0 1px #16a34a; background:#f0fdf4; }}
  .dot {{ display:inline-block; width:9px; height:9px; border-radius:999px; margin-right:5px; vertical-align:0; }}
  .stats {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; }}
  .stat {{ border:1px solid var(--line); border-radius:8px; background:white; padding:8px; }}
  .stat b {{ display:block; font-size:18px; line-height:1.1; }}
  .stat span {{ display:block; margin-top:3px; color:var(--muted); font-size:11px; }}
  .utility-row {{ display:flex; gap:8px; }}
  .utility-btn {{ flex:1; text-align:center; padding:9px 8px; font-size:13px; }}
  .legend {{ display:grid; gap:6px; color:#334155; font-size:12px; }}
  .leaflet-popup-content {{ min-width:270px; max-width:340px; margin:12px; font-size:13px; line-height:1.55; }}
  .popup-title {{ font-weight:760; font-size:14px; line-height:1.35; margin-bottom:6px; }}
  .popup-tag {{ display:inline-block; padding:2px 7px; border-radius:999px; font-size:12px; margin-bottom:6px; }}
  .popup-grid {{ display:grid; grid-template-columns:74px 1fr; gap:4px 8px; }}
  .popup-grid span:nth-child(odd) {{ color:#64748b; }}
  .amap-link {{ display:block; margin-top:10px; text-align:center; text-decoration:none; background:#0f172a; color:white; border-radius:8px; padding:8px 10px; font-weight:650; }}
  .count-badge {{ float:right; color:#64748b; font-size:12px; }}
  @media (max-width:760px) {{
    .panel {{ left:8px; right:8px; top:8px; width:auto; max-width:none; border-radius:9px; }}
    .toggle {{ display:inline-block; }}
    .panel-body {{ max-height:48vh; padding:10px 12px 12px; }}
    .panel.collapsed .panel-body {{ display:none; }}
    .title {{ font-size:15px; }} .subtitle {{ font-size:11px; }}
    .city-row, .stats {{ grid-template-columns:1fr; }}
    .position-btn {{ padding:8px 9px; }}
    .leaflet-control-zoom {{ margin-top:96px !important; }}
  }}
</style>
</head>
<body>
<div id="map"></div>
<aside class="panel" id="panel">
  <div class="panel-head">
    <div>
      <div class="title">{title}</div>
      <div class="subtitle">{subtitle}</div>
    </div>
    <button class="toggle" id="togglePanel">筛选</button>
  </div>
  <div class="panel-body">
    <div class="section"><div class="section-title">城市</div><div class="city-row" id="cityButtons"></div></div>
    <div class="section"><div class="section-title">位置 / 来源</div><div class="buttons" id="positionButtons"></div></div>
    <div class="section"><div class="section-title">当前展示</div><div class="stats">
      <div class="stat"><b id="shownCount">{len(points)}</b><span>展示点位</span></div>
      <div class="stat"><b id="positionCount">{len(positions)}</b><span>位置/来源</span></div>
      <div class="stat"><b id="cityCount">2</b><span>城市数</span></div>
    </div></div>
    <div class="section utility-row"><button class="utility-btn" id="showAll">看全部</button><button class="utility-btn" id="fitCurrent">适配视野</button></div>
    <div class="legend">
      <div><span class="dot" style="background:#2563eb"></span>北京：原重点拜访点位</div>
      <div><span class="dot" style="background:#16a34a"></span>郑州：面饮明细中全部单计商家，按 POI 去重</div>
    </div>
  </div>
</aside>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const points = {points_json};
const cityOrder = ['全部','北京','郑州'];
const cityCounts = {{'全部': points.length, '北京': {city_counts.get('北京', 0)}, '郑州': {city_counts.get('郑州', 0)}}};
const positionOrder = {positions_json};
let activeCity = '全部';
let activePosition = '全部';
const map = L.map('map', {{ zoomControl:true, preferCanvas:true }}).setView([34.75, 113.65], 8);
L.tileLayer('https://webrd0{{s}}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={{x}}&y={{y}}&z={{z}}', {{ subdomains:['1','2','3','4'], attribution:'高德地图' }}).addTo(map);
const layer = L.layerGroup().addTo(map);
const markers = [];
function esc(value) {{ return String(value ?? '').replace(/[&<>'"]/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}}[ch])); }}
function keyFor(p) {{ return `${{p['城市']}}｜${{p['位置']}}`; }}
function inSelection(p) {{ return (activeCity === '全部' || p['城市'] === activeCity) && (activePosition === '全部' || keyFor(p) === activePosition); }}
function amapMarkerLink(p) {{ return `https://uri.amap.com/marker?position=${{Number(p['经度']).toFixed(6)}}%2C${{Number(p['纬度']).toFixed(6)}}&name=${{encodeURIComponent(p['POI名称'])}}&src=codex.poi.visit`; }}
function popupHtml(p) {{
  const tag = p['来源'] === '郑州单计全量' ? '郑州单计商家' : `${{p['城市']}}重点点位`;
  return `<div class="popup-title">${{esc(p['城市'])}}｜${{esc(p['POI名称'])}}</div>
    <div class="popup-tag" style="background:${{p['浅色值']}};color:${{p['颜色值']}}">${{esc(tag)}}</div>
    <div class="popup-grid">
      <span>位置/来源</span><b>${{esc(p['位置'])}}</b>
      <span>地址</span><b>${{esc(p['地址'])}}</b>
      <span>小组</span><b>${{esc(p['小组'])}}</b>
      <span>BDM/BD</span><b>${{esc(p['BDM'])}} / ${{esc(p['BD'])}}</b>
      <span>商圈</span><b>${{esc(p['商圈类型'])}}</b>
      <span>经营大类</span><b>${{esc(p['经营大类'])}}</b>
      <span>营业状态</span><b>${{esc(p['营业状态'])}}</b>
      <span>认领/在售</span><b>${{esc(p['是否认领'])}} / ${{esc(p['是否在售'])}}</b>
      <span>本月GMV</span><b>${{esc(p['本月GMV'])}}</b>
      <span>线下GMV</span><b>${{esc(p['线下GMV'])}}</b>
      <span>商品/搜索</span><b>${{esc(p['商品数'])}} / ${{esc(p['搜索次数'])}}</b>
      <span>POI ID</span><b>${{esc(p['POI ID'])}}</b>
    </div>
    <a class="amap-link" target="_blank" rel="noopener" href="${{esc(amapMarkerLink(p))}}">在高德 App 打开此点</a>`;
}}
points.forEach(p => {{
  const marker = L.circleMarker([p['纬度'], p['经度']], {{
    radius: p['来源'] === '郑州单计全量' ? 4 : 6,
    color: '#ffffff',
    weight: 1,
    fillColor: p['颜色值'],
    fillOpacity: .86,
    title: `${{p['城市']}}｜${{p['POI名称']}}`
  }}).bindPopup(popupHtml(p));
  marker._pointData = p; markers.push(marker);
}});
function selectedPoints() {{ return points.filter(inSelection); }}
function renderMarkers(fit=true) {{
  layer.clearLayers();
  const selected = selectedPoints();
  markers.forEach(m => {{ if (inSelection(m._pointData)) layer.addLayer(m); }});
  document.getElementById('shownCount').textContent = selected.length;
  document.getElementById('positionCount').textContent = new Set(selected.map(keyFor)).size;
  document.getElementById('cityCount').textContent = new Set(selected.map(p => p['城市'])).size;
  updateButtons();
  if (fit && selected.length) {{
    const bounds = L.latLngBounds(selected.map(p => [p['纬度'], p['经度']]));
    map.fitBounds(bounds.pad(activePosition === '全部' ? .08 : .18), {{ animate:true, maxZoom: activePosition === '全部' ? 11 : 15 }});
  }}
}}
function updateButtons() {{
  document.querySelectorAll('[data-city]').forEach(btn => btn.classList.toggle('active', btn.dataset.city === activeCity));
  document.querySelectorAll('[data-position]').forEach(btn => btn.classList.toggle('active', btn.dataset.position === activePosition));
}}
function makeCityButtons() {{
  const wrap = document.getElementById('cityButtons');
  cityOrder.forEach(city => {{
    const btn = document.createElement('button'); btn.className = 'city-btn'; btn.dataset.city = city;
    btn.innerHTML = `${{esc(city)}} <span class="count-badge">${{cityCounts[city]}}</span>`;
    btn.onclick = () => {{ activeCity = city; activePosition = '全部'; renderMarkers(true); }};
    wrap.appendChild(btn);
  }});
}}
function makePositionButtons() {{
  const wrap = document.getElementById('positionButtons');
  const all = document.createElement('button'); all.className = 'position-btn active'; all.dataset.position = '全部'; all.textContent = '全部位置 / 来源';
  all.onclick = () => {{ activePosition = '全部'; renderMarkers(true); }}; wrap.appendChild(all);
  positionOrder.forEach(pos => {{
    const btn = document.createElement('button'); btn.className = 'position-btn'; btn.dataset.position = pos.key;
    const count = points.filter(p => keyFor(p) === pos.key).length;
    btn.innerHTML = `${{esc(pos.label)}} <span class="count-badge">${{count}}</span>`;
    btn.onclick = () => {{ activePosition = pos.key; activeCity = pos['城市']; renderMarkers(true); if (window.innerWidth < 760) document.getElementById('panel').classList.add('collapsed'); }};
    wrap.appendChild(btn);
  }});
}}
document.getElementById('showAll').onclick = () => {{ activeCity='全部'; activePosition='全部'; renderMarkers(true); }};
document.getElementById('fitCurrent').onclick = () => renderMarkers(true);
document.getElementById('togglePanel').onclick = () => document.getElementById('panel').classList.toggle('collapsed');
makeCityButtons(); makePositionButtons(); renderMarkers(true);
</script>
</body>
</html>
"""


def write_csv(points):
    fieldnames = [
        "城市", "位置", "来源", "POI名称", "地址", "经度", "纬度", "小组", "BDM", "BD",
        "商家ID", "门店ID", "品牌ID", "POI ID", "商圈类型", "经营大类", "营业状态",
        "是否认领", "是否在售", "是否动销", "本月GMV", "线下GMV", "商品数", "搜索次数", "围栏名称",
    ]
    with (ROOT / "beijing_zhengzhou_poi_visit_points.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for point in points:
            writer.writerow({k: point.get(k, "-") for k in fieldnames})


def write_geojson(points):
    features = []
    for point in points:
        props = {k: v for k, v in point.items() if k not in {"经度", "纬度"}}
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [point["经度"], point["纬度"]]},
            "properties": props,
        })
    (ROOT / "beijing_zhengzhou_poi_visit_points.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_kml(points):
    placemarks = []
    for point in points:
        name = html.escape(f"{point['城市']}｜{point['POI名称']}")
        description = html.escape(
            f"位置/来源：{point['位置']}\n地址：{point['地址']}\nBDM/BD：{point['BDM']} / {point['BD']}\n"
            f"本月GMV：{point['本月GMV']}\n商品/搜索：{point['商品数']} / {point['搜索次数']}\nPOI ID：{point['POI ID']}"
        )
        placemarks.append(
            f"    <Placemark><name>{name}</name><description>{description}</description>"
            f"<Point><coordinates>{point['经度']},{point['纬度']},0</coordinates></Point></Placemark>"
        )
    kml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<kml xmlns=\"http://www.opengis.net/kml/2.2\">\n<Document>\n"
    kml += "\n".join(placemarks)
    kml += "\n</Document>\n</kml>\n"
    (ROOT / "beijing_zhengzhou_poi_visit_points.kml").write_text(kml, encoding="utf-8")


def write_zip():
    files = [
        "index.html",
        "README.md",
        "beijing_zhengzhou_poi_visit_points.csv",
        "beijing_zhengzhou_poi_visit_points.geojson",
        "beijing_zhengzhou_poi_visit_points.kml",
    ]
    with zipfile.ZipFile(ROOT / "beijing_zhengzhou_poi_visit_package.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        for name in files:
            path = ROOT / name
            if path.exists():
                zf.write(path, arcname=name)


def update_readme(total, zhengzhou_total, added, duplicates):
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = re.sub(r"北京 \+ 郑州单计 POI 拜访地图", "北京重点点位 + 郑州单计全量 POI 地图", text)
    text = re.sub(r"全部 310 个点位", f"全部 {total} 个点位", text)
    text = re.sub(r"310 个点位｜9 个位置｜3 类调研动作", f"{total} 个点位｜郑州单计全量 {zhengzhou_total} 个｜按 POI 去重", text)
    text = re.sub(r"- 总点位：.*", f"- 总点位：{total}", text)
    text = re.sub(r"- 北京点位：.*", f"- 北京原重点点位：72；郑州位置 1-4 保留点位 + 郑州单计全量新增点位", text)
    text = re.sub(r"- 扫码/营销调研：.*", f"- 郑州 Excel 单计商家：{zhengzhou_total}；其中新增到地图：{added}；与原位置点位重复未重复标注：{duplicates}", text)
    text = re.sub(r"- 北京 4 个核心位置、郑州 4 个核心位置、郑州二七万达 1 个补充位置。", "- 已删除郑州二七万达补充文件来源点位；保留郑州位置一至位置四原有点位。", text)
    readme.write_text(text, encoding="utf-8")


def main():
    points, added, duplicates = build_points()
    positions = unique_positions(points)
    INDEX.write_text(render_index(points, positions), encoding="utf-8")
    write_csv(points)
    write_geojson(points)
    write_kml(points)
    zhengzhou_total = len(load_zhengzhou_single_points())
    update_readme(len(points), zhengzhou_total, added, duplicates)
    write_zip()
    summary = {
        "total_points": len(points),
        "zhengzhou_single_excel": zhengzhou_total,
        "added_from_excel": added,
        "duplicates_from_excel": duplicates,
        "positions": {p["key"]: sum(1 for x in points if f"{x['城市']}｜{x['位置']}" == p["key"]) for p in positions},
    }
    (ROOT / "map_update_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
