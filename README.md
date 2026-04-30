# 北京重点点位 + 郑州单计全量 POI 地图

## 推荐使用方式

- 稳定公开地图链接建议使用 GitHub Pages：仓库推送到 GitHub 后，Pages 会自动发布 `index.html`。
- 若仓库名为 `amap_poi_visit_package`，发布地址通常是 `https://<github-user>.github.io/amap_poi_visit_package/`。
- 打开 `index.html` 可以在一张地图中查看全部 1282 个点位。
- 页面左侧可按城市、原 8 个核心位置和“郑州单计全量新增点位”筛选；点击任一位置会自动聚焦到对应区域。
- 本版不再标记调研标签，郑州点位来自面饮明细中的全部单计商家，并按 POI ID 去重。
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
- `beijing_zhengzhou_map_validation_report.md`：历史点位数量、标签数量、重复和经纬度校验报告。
- `beijing_poi_visit_points.*`：北京原始单城点位文件，保留作为备份。
- `amap_open_links.md`：每个点位的高德单点打开链接，作为导航备用。
- `beijing_zhengzhou_poi_visit_package.zip`：北京 + 郑州完整文件包。

## 点位数量

- 总点位：1282
- 北京原重点点位：72；郑州位置 1-4 保留点位 + 郑州单计全量新增点位
- 郑州 Excel 单计商家：1210；其中新增到地图：1090；与原位置点位重复未重复标注：120
- 已删除郑州二七万达补充文件来源点位；保留郑州位置一至位置四原有点位。

## 注意

- 北京原始经纬度来自抖音后台 Excel；郑州全量单计点位来自用户提供的 `/Users/bytedance/Downloads/【郑州】面饮情况 - 团队x品类x门店明细-2026-04-29.xlsx`。
- 已移除二七万达补充文件来源点位；如果同一 POI 已存在于郑州位置一至位置四，不再重复标注。
- 没有源文件经纬度的点位不标注到地图，不使用地址反查或猜测坐标。
- 高德 App 原生批量导入 KML/GeoJSON 支持不稳定，因此本包主方案是“一张网页地图展示全部点位”，高德 App 用于单点打开和导航。
- 若没有公开静态托管权限，可以先用电脑本地打开 `index.html` 验证地图效果，再将整个目录上传到可访问的静态空间。
