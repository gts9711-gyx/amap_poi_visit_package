# 北京商圈地图复用工作流

## 目标

用最低资源消耗复用当前地图能力。后续输入新的北京行政区、物理商圈和指标数据时，不重新搭建页面、不重新找北京边界、不重复查询已缓存商圈坐标，只更新 `processed.js`。

## 固定资产

- 地图边界：`data/beijing_districts.geojson` 和 `data/beijing_districts.js`
- 商圈定位缓存：`data/geocode_cache.json`
- 页面模板：`index.html`
- 生成脚本：`scripts/build_processed_data.py`

## 标准命令

```bash
cd /Users/bytedance/codexx/Work/beijing_poi_gmv_map
/Users/bytedance/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  scripts/build_processed_data.py \
  --input "/path/to/input.xlsx" \
  --district-col "物理商圈所在行政区" \
  --area-col "物理商圈名称" \
  --heat-col "底图颜色指标列名" \
  --bubble-col "气泡大小指标列名" \
  --title "北京市XXX与YYY分布" \
  --eyebrow "北京行政区XXX热力 + 商圈YYY气泡" \
  --heat-label "XXX" \
  --bubble-label "YYY" \
  --heat-legend-high "XXX 高" \
  --heat-legend-low "XXX 低" \
  --bubble-metric-format raw \
  --offline-geocode
```

## 什么时候去掉 `--offline-geocode`

默认保留它，最省时间和网络资源。只有当新数据里出现大量全新商圈、且散点位置需要更接近真实物理位置时，去掉 `--offline-geocode` 让脚本尝试补充公共地理编码缓存。

## 输出

- `data/processed.json`：结构化结果，便于检查。
- `data/processed.js`：网页直接加载的数据。
- `index.html`：刷新即可看到新图。

## 发布

当前公网发布使用 GitHub Pages 仓库：

`/Users/bytedance/codexx/Work/amap_poi_visit_package/beijing_poi_gmv_map/`

更新发布时复制以下文件过去并提交：

- `index.html`
- `data/beijing_districts.js`
- `data/processed.js`
- `outputs/beijing_poi_gmv_map.png`（如已重新导出图片）

线上地址：

`https://gts9711-gyx.github.io/amap_poi_visit_package/beijing_poi_gmv_map/`
