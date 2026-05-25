# 北京行政区 + 商圈指标地图复用模板

基于 Excel 生成北京市行政区热力图，并叠加物理商圈气泡散点。后续只要输入“北京行政区 + 北京物理商圈 + 两个指标列”，即可复用同一套地图能力。

## 最省资源复用方式

复用内容：

- `data/beijing_districts.geojson` / `data/beijing_districts.js`：北京 16 区边界，后续不用重复下载。
- `data/geocode_cache.json`：已识别过的商圈公共地理编码缓存，后续不用重复查询。
- `index.html`：通用 ECharts 模板，可直接 `file://` 打开。
- `scripts/build_processed_data.py`：通用 Excel 转地图数据脚本。

后续只需要跑一次脚本：

```bash
cd /Users/bytedance/codexx/Work/beijing_poi_gmv_map
/Users/bytedance/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  scripts/build_processed_data.py \
  --input /path/to/new_beijing_metric.xlsx \
  --district-col "物理商圈所在行政区" \
  --area-col "物理商圈名称" \
  --heat-col "全量有效POI数" \
  --bubble-col "已开发有效POI_近1d核销GMV" \
  --title "北京市全量有效 POI 与核销 GMV 分布" \
  --eyebrow "北京行政区 POI 热力 + 商圈核销 GMV 气泡" \
  --heat-label "全量有效 POI" \
  --bubble-label "核销 GMV" \
  --heat-legend-high "POI 多" \
  --heat-legend-low "POI 少" \
  --bubble-metric-format yi \
  --offline-geocode
```

输出：

- `data/beijing_districts.geojson`
- `data/processed.json`
- `data/beijing_districts.js`
- `data/processed.js`

`--offline-geocode` 会只使用已有商圈地理编码缓存，速度最快、最省网络资源。若新商圈很多且希望尽量贴近真实位置，可以去掉 `--offline-geocode`，脚本会尝试补充公共地理编码缓存。

## 本地预览

```bash
cd /Users/bytedance/codexx/Work/beijing_poi_gmv_map
python3 -m http.server 8790
```

打开 `http://localhost:8790`。

## 说明

- 行政区底色：按 `--heat-col` 指标在行政区内聚合。
- 气泡大小和紫色深浅：按 `--bubble-col` 指标映射。
- 商圈气泡位置：优先使用公共地理编码并校验所属行政区；识别不到时回退到行政区 AOI 内分散铺点。

## 输入数据要求

Excel 至少需要 4 列：

- 行政区列：例如 `物理商圈所在行政区`，值需匹配北京 16 区名称。
- 商圈列：例如 `物理商圈名称`。
- 底图热力指标列：例如 `全量有效POI数`。
- 气泡指标列：例如 `已开发有效POI_近1d核销GMV`。

同一行政区下可有多个商圈；脚本会自动聚合行政区底色，并保留每一行商圈作为一个气泡。
