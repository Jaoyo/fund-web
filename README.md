# fund-web

个人自用基金跟踪与建议工具。前后端分离，后端可独立被其他本地项目/Agent 调用。

## 技术栈

- **后端**：FastAPI + sqlite3 原生（WAL 模式） + pip
- **前端**：Vue 3 + TS + Vite + Element Plus + Pinia + ECharts
- **数据源**：天天基金（东方财富）公开接口

## 启动

### 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # 编辑 .env，填入 FUND_AUTH_TOKEN
bash run.sh
```

生成 token：`openssl rand -hex 32`

服务监听 `http://localhost:8000`，OpenAPI 文档在 `http://localhost:8000/docs`。

> token 来源支持两种，优先级：环境变量 > `backend/.env` 文件。未设置时所有业务接口会返回 `code: 5001`。

### 前端

```bash
cd frontend
npm install
npm run dev
```

打开 `http://localhost:5173`。

## API 约定

- 路由前缀 `/api/v1`
- 统一响应格式：`{ "code": 0, "message": "ok", "data": ... }`，`code == 0` 表示成功
- `POST /api/v1/transactions` 支持 `client_id` 幂等
- CORS 默认放开 `localhost` / `127.0.0.1` 所有端口
- 鉴权：所有 `/api/v1/*` 业务接口需要 `Authorization: Bearer <FUND_AUTH_TOKEN>` 头；`/` 和 `/api/v1/health` 公开
  - 鉴权失败业务码 `4011`，服务器未配置 token 业务码 `5001`
  - 前端首次访问会跳到 `/login`，粘贴 token 后存进 `localStorage`，同一浏览器只需输入一次

## 部署到公网

- **必须** 配合 HTTPS 反代（Caddy / Nginx + Let's Encrypt），否则 token 明文传输等于裸奔
- **进程数量限制**：强烈建议在单进程模式下运行后端（如 `uvicorn --workers 1` 或确保 gunicorn 的 worker 数量为 1）。系统内部使用本地字典（dict）作为净值查询的防并发节流和内存缓存，多 worker 模式下由于内存不共享，不仅会导致缓存失效/命中率随机，长线运行更会导致多进程中存在重复的冗余缓存数据，引起一定程度的内存积压和数据不一致问题。
- token 用 `openssl rand -hex 32` 生成；放进 `backend/.env`（已 gitignore）或 systemd unit 的 `Environment=`
- 多设备访问：每个设备首次访问时粘贴同一个 token 即可
- token 泄露后：改 `.env` 里的值重启服务，所有设备自动失效，重新粘贴新值即可

## 目录

```
backend/        FastAPI 后端
  app/
    main.py     入口
    config.py
    db.py       sqlite3 + WAL
    models/     Pydantic 模型
    routers/    路由层
    services/   业务逻辑（东财接口、收益计算、建议指标）
    tasks/      APScheduler 定时任务
  data/         SQLite 文件（gitignore）
  tests/

frontend/       Vue 3 前端
  src/
    api/        axios 封装
    stores/     Pinia
    views/      Dashboard / FundDetail / Transactions / Advice
    components/
    router/
    utils/
```
