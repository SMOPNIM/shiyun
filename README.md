# 诗云 (Shiyun) — 究极吟诗程序

> *"诗云" 灵感来源于刘慈欣科幻小说《诗云》—— 一个试图枚举所有可能诗歌的终极程序。*

枚举 UTF-8 可打印字符（字符、符号、表情符号）的所有排列组合，通过 Web 界面交互，支持 Gzip 压缩保存。

## 功能

- 枚举指定字符集的全部排列组合（长度 ≤ N）
- 预设字符集：ASCII、数字、字母、**千字文**（1000 个不重复汉字）、表情符号
- 支持自定义字符集
- SSE 实时流式输出到浏览器
- Gzip 压缩保存到文件（含元数据）
- 实时统计（生成数、速率、进度）

## 快速开始

```bash
# 安装依赖
pip install flask waitress

# 启动服务
python3 app.py

# 访问 http://127.0.0.1:5000
```

## 保存格式

保存文件首行为 JSON 元数据注释，后续每行一个组合：

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
| `/api/presets` | GET | 获取预设字符集 |
| `/api/estimate` | POST | 估算组合总数 |
| `/api/start` | POST | 创建生成会话 |
| `/stream` | GET | SSE 实时流 |
| `/api/stop` | POST | 停止生成 |
| `/api/stats` | GET | 获取统计 |
| `/api/save` | POST | 保存到文件（可选 Gzip） |
| `/api/save_status` | GET | 保存进度查询 |

## 许可

MIT
