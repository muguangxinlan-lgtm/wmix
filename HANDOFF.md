# 项目交接与当前进度

## 项目是什么

这是一个离线电商数据看板项目。

主逻辑：
- 本地 Python 脚本读取 SQLite
- 生成静态 HTML
- 通过 GitHub Pages 发布

不是 Web 后端服务，也不是前后端分离项目。

## 现在的状态

截至 2026-03-19：

- Git 仓库已经初始化
- 远端仓库已经连接：`muguangxinlan-lgtm/wmix`
- 代码已经成功推送到 GitHub
- GitHub Pages 已经配置为从 `main` 分支的 `/ (root)` 发布
- 发布文件是 `index.html`

如果站点暂时打不开，优先检查 GitHub Pages 是否还在构建。

## 访问地址

- 仓库：`https://github.com/muguangxinlan-lgtm/wmix`
- 站点：`https://muguangxinlan-lgtm.github.io/wmix/`

## 主要文件说明

- `build_v2.py`
  主脚本。当前应该优先维护这个文件。
- `index.html`
  生成产物，也是 GitHub Pages 发布入口。
- `publish_github_pages.sh`
  发布脚本。会重新生成页面并推送；第一次输入 GitHub token 后会保存到 macOS 钥匙串。

## 历史背景

这个项目一开始是准备用一台一直开机的 Mac 做本地服务器，对应文件：
- `serve_dashboard.py`
- `launch_dashboard_server.sh`
- `com.wmix.dashboard-server.plist`

后来改成 GitHub Pages 方案，所以这些文件现在不是主路径，但可以保留备用。

## 已知问题

- 页面依赖外部 CDN：`https://cdn.jsdelivr.net/.../chart.umd.min.js`
- 如果访问者网络无法访问 jsDelivr，图表可能无法正常加载
- 仓库里同时保留了 `dashboard.html` 和 `index.html`，实际发布只用 `index.html`

## 建议的后续整理

1. 如果不再需要本地 Mac 服务器方案，可以移除：
   - `serve_dashboard.py`
   - `launch_dashboard_server.sh`
   - `com.wmix.dashboard-server.plist`
2. 如果不再需要旧版页面输出，可以移除 `dashboard.html`
3. 可以把 Chart.js 改成仓库内本地静态文件，避免依赖外部 CDN
4. 可以给 `build_v2.py` 增加命令行参数，避免数据库路径写死

## 下一个 AI/维护者先看什么

优先阅读：
1. `README.md`
2. `HANDOFF.md`
3. `build_v2.py`
4. `publish_github_pages.sh`
