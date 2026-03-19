# 电商看板发布说明

这个项目现在的主用途是：
- 从本地 SQLite 数据库生成静态看板页面
- 发布到 GitHub Pages 给同事访问

仓库地址：
- `https://github.com/muguangxinlan-lgtm/wmix`

站点地址：
- `https://muguangxinlan-lgtm.github.io/wmix/`

## 当前主流程

1. 运行 `build_v2.py` 生成最新页面
2. 生成结果写入 `index.html`
3. 推送到 GitHub 仓库
4. GitHub Pages 自动发布

## 关键文件

- `build_v2.py`
  当前主生成脚本。读取 SQLite，输出 `index.html`。
- `index.html`
  GitHub Pages 实际发布的首页文件。
- `publish_github_pages.sh`
  一键重新生成并推送到 GitHub 的脚本。
- `HANDOFF.md`
  给后续 AI 或维护者看的项目状态和交接说明。

## 遗留/备用文件

- `build_dashboard.py`
  旧版生成脚本，保留参考。
- `dashboard.html`
  旧版输出文件，当前发布不依赖它。
- `serve_dashboard.py`
  本地静态服务脚本，用于把这台 Mac 当服务器。
- `launch_dashboard_server.sh`
  本地服务启动脚本。
- `com.wmix.dashboard-server.plist`
  macOS `launchd` 配置，用于本地常驻服务。

## 平时怎么更新

直接运行：

```bash
/Users/wmix/wmixclaude/publish_github_pages.sh
```

脚本会要求输入：
- GitHub 用户名
- GitHub token
- 提交说明

第一次输入后，凭据会保存到 macOS 钥匙串。后续再次运行时，脚本会自动复用，不需要每次重填。

## 手工更新方式

```bash
cd /Users/wmix/wmixclaude
python3 build_v2.py
git add .
git commit -m "update dashboard"
git push
```

## 注意事项

- 页面是静态站点，适合 GitHub Pages。
- 页面依赖 jsDelivr 上的 Chart.js，访问者需要能连外网 CDN。
- 不要把 GitHub token 写进脚本、仓库或聊天记录。
