# 北京 POI 数 + 核销 GMV 地图

基于 Excel 生成北京市行政区 POI 热力图，并叠加物理商圈核销 GMV 气泡散点。

## 生成数据

```bash
cd /Users/bytedance/codexx/Work/beijing_poi_gmv_map
/Users/bytedance/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  scripts/build_processed_data.py
```

输出：

- `data/beijing_districts.geojson`
- `data/processed.json`

## 本地预览

```bash
cd /Users/bytedance/codexx/Work/beijing_poi_gmv_map
python3 -m http.server 8790
```

打开 `http://localhost:8790`。

## 说明

- 行政区底色：按区级全量有效 POI 数聚合。
- 气泡大小：按物理商圈核销 GMV 映射。
- 商圈气泡位置：优先使用公共地理编码并校验所属行政区；识别不到时回退到行政区 AOI 内分散铺点。
