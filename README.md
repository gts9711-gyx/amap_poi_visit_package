# 北京 + 郑州单计 POI 拜访地图

## 推荐使用方式

- 稳定公开地图链接建议使用 GitHub Pages：仓库推送到 GitHub 后，Pages 会自动发布 `index.html`。
- 若仓库名为 `amap_poi_visit_package`，发布地址通常是 `https://<github-user>.github.io/amap_poi_visit_package/`。
- 打开 `index.html` 可以在一张地图中查看全部 310 个点位。
- 页面左侧可按城市、9 个核心/补充位置筛选；点击任一位置会自动聚焦到对应区域。
- 页面也可按 3 类调研标签筛选：扫码/营销调研、新开问题调研、动销问题调研。
- 点击任一点位可查看地址、BDM、BD、商圈类型、经营大类、GMV、商品数和搜索次数，并可跳转到高德 App 打开该单点。

## 公开发布状态

- 已生成可直接发布的静态网页地图包。
- 已加入 GitHub Pages 自动部署工作流：`.github/workflows/pages.yml`。
- 推送到 GitHub 的 `main` 分支后，会通过 GitHub Actions 自动发布静态站点。
- 如果 GitHub Pages 首次未自动打开，请在仓库 Settings -> Pages 中选择 GitHub Actions 作为发布来源后重新运行工作流。

## 文件说明

- `index.html`：主地图页，一张地图展示全部点位，适合发布成公开链接。
- `beijing_zhengzhou_poi_visit_points.csv`：北京 + 郑州完整点位表，可用 Excel/飞书表格打开。
- `beijing_zhengzhou_poi_visit_points.kml`：北京 + 郑州通用地图点位文件，适合支持 KML 的地图工具。
- `beijing_zhengzhou_poi_visit_points.geojson`：北京 + 郑州标准地理数据文件，适合 GIS/地图工具二次处理。
- `beijing_zhengzhou_map_validation_report.md`：点位数量、标签数量、重复和经纬度校验报告。
- `beijing_poi_visit_points.*`：北京原始单城点位文件，保留作为备份。
- `amap_open_links.md`：每个点位的高德单点打开链接，作为导航备用。
- `beijing_zhengzhou_poi_visit_package.zip`：北京 + 郑州完整文件包。

## 点位数量

- 总点位：310
- 北京点位：72；郑州点位：238
- 扫码/营销调研：166；新开问题调研：72；动销问题调研：72
- 北京 4 个核心位置、郑州 4 个核心位置、郑州二七万达 1 个补充位置。

## 注意

- 北京原始经纬度来自抖音后台 Excel；郑州核心位置经纬度来自用户提供的 `/Users/bytedance/Downloads/【郑州】面饮情况 - 团队x品类x门店明细-2026-04-29.xlsx`。
- 二七万达补充点位经纬度来自用户提供的 `/Users/bytedance/Downloads/二七万达-面饮情况 - 团队x品类x门店明细-2026-04-29.xlsx` 的 `二七万达` sheet。
- 没有源文件经纬度的点位不标注到地图，不使用地址反查或猜测坐标。
- 高德 App 原生批量导入 KML/GeoJSON 支持不稳定，因此本包主方案是“一张网页地图展示全部点位”，高德 App 用于单点打开和导航。
- 若没有公开静态托管权限，可以先用电脑本地打开 `index.html` 验证地图效果，再将整个目录上传到可访问的静态空间。
