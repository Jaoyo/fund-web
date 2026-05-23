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
bash run.sh
```

服务监听 `http://localhost:8000`，OpenAPI 文档在 `http://localhost:8000/docs`。

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
- 无鉴权（个人本地使用）

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
