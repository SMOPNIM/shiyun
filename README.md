# 诗云 (Shiyun) — 究极吟诗程序

> *"诗云" 灵感来源于刘慈欣科幻小说《诗云》—— 一个试图枚举所有可能诗歌的终极程序。*

枚举 UTF-8 可打印字符（汉字、符号、表情符号）的所有排列组合，支持 **枚举模式**（全部组合）和 **吟诗模式**（每首诗 = line_length × lines_per_poem 个字符的组合）。Web 界面交互，支持暂停/继续、状态保存/恢复、Gzip 压缩保存。

## 功能

- 两种模式：**枚举模式**（全部组合）和 **吟诗模式**（每首诗 = `line_length` × `lines_per_poem` 字符的组合）
- 预设字符集：ASCII、数字、字母、**千字文**（1000 个不重复汉字）、表情符号、全部可打印 Unicode（~155k 字符）
- 支持自定义字符集
- SSE 实时流式输出到浏览器，带速率/进度/用时统计
- **暂停/继续**：可随时暂停并在后续恢复生成
- **状态保存/加载**：保存生成进度到磁盘，后续加载继续
- **页面刷新恢复**：自动保存会话，刷新后恢复
- **星图展示**：暂停/停止后将吟诗以多星云绕日动画展示，每首诗一个光点，每 1 万首一个独立星云
- **TUI 模式**：终端交互界面（curses，无需额外依赖）
- Gzip 压缩保存到文件（含 JSON 元数据头）
- **实时统计**（生成数、速率、进度、用时）
- 大数保护（超过 10^18 显示"过大"）

## 快速开始

```bash
# 安装依赖
pip install flask waitress

# 启动 Web 服务
python3 app.py

# 或启动 TUI 模式
python3 app.py --tui

# 访问 http://127.0.0.1:5000
```

## TUI 模式

| 按键 | 功能 |
|------|------|
| `C` | 切换字符集 |
| `M` | 切换模式（枚举/吟诗） |
| `+` `-` | 调整长度 |
| `Enter` | 开始生成 |
| `P` | 暂停 |
| `R` | 继续 |
| `T` | 停止 |
| `S` | 保存状态 |
| `Q` | 退出 |

## 保存格式

保存文件首行为 JSON 元数据注释（`//` 开头），后续每行一个组合：

```
// {"chars": "01", "chars_len": 2, "max_length": 2, "timestamp": "2026-06-19T18:00:52", "program": "诗云 - 究极吟诗程序"}
0
1
00
01
10
11
```

## API

| 路径 | 方法 | 说明 |
|------|------|------|
| `/` | GET | WebUI |
| `/api/presets` | GET | 获取预设字符集列表 |
| `/api/presets/<key>/chars` | GET | 获取指定预设的字符 |
| `/api/estimate` | POST | 估算组合/诗总数 |
| `/api/start` | POST | 创建生成会话 |
| `/stream` | GET | SSE 实时流（支持 `?resume=1`） |
| `/api/pause` | POST | 暂停生成 |
| `/api/resume` | POST | 继续生成（可选 `state`） |
| `/api/stop` | POST | 停止生成 |
| `/api/stats` | GET | 获取统计（生成数、总数、速率、用时） |
| `/api/save` | POST | 保存到文件（可选 Gzip） |
| `/api/save_status` | GET | 保存进度查询 |
| `/api/save_state` | POST | 保存会话状态到磁盘 |
| `/api/list_states` | GET | 列出已保存的状态文件 |
| `/api/load_state/<file>` | GET | 加载指定状态文件 |
| `/api/auto_save` | POST | 自动保存（用于页面刷新恢复） |
| `/api/latest_session` | GET | 获取最新自动保存的会话 |
| `/api/clear_latest` | POST | 清除自动保存的会话 |

## 许可

MIT

