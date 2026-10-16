# Paywise 薪算清

当前工作区已完成阶段 0–4 的本地演示版功能和集成验收（2026-10-14）。正式上线仍需完成下述数据和持久化限制，不能将本地验收等同于生产发布。

已完成 FastAPI 健康检查、配置/CORS、政策示例数据、计算接口契约、薪酬计算器表单，以及社保、公积金、累计预扣个税、年终奖方案计算和端到端结果解释。方案管理、Offer 对比、政策导入审核、结果导出和脱敏分享已实现。

## 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

健康检查：`GET http://127.0.0.1:8000/api/v1/health`，接口文档：`http://127.0.0.1:8000/docs`。

可用环境变量：`PAYWISE_APP_NAME`、`PAYWISE_APP_VERSION`、`PAYWISE_API_PREFIX`、`PAYWISE_CORS_ORIGINS`（逗号分隔）。

测试：`pytest`

提供 `GET /api/v1/policies?region_code=SH&month=2026-10`、`POST /api/v1/calculations` 和方案保存接口 `POST/GET /api/v1/scenarios`、`GET /api/v1/scenarios/{id}`。方案保存原始输入、政策版本、计算引擎版本和完整结果快照，读取历史方案时不会按新政策重算。计算结果包含政策版本和来源、可信度标签、假设、待确认项、社保/公积金基数解释、累计预扣过程及年终奖双方案。政策数据明确标记为示例数据，不能作为正式税务依据；年终奖单独计税是否可用由匹配政策字段控制。

方案支持保存、列表、读取、重命名、软删除和恢复；当前存储使用进程内存，服务重启后需重新保存，接入数据库前不应作为长期历史归档。

## 阶段状态

- 阶段 0：完成（项目骨架）
- 阶段 1：完成（政策、契约和计算表单）
- 阶段 2：完成（社保、公积金、个税、奖金和结果解释）
- 阶段 3：完成（方案管理和最多 4 个 Offer 对比）
- 阶段 4：本地验收完成（真实前后端、浏览器流程、政策审核、导出和生产构建）

当前本地演示版阶段已收尾。验收命令、结果和正式上线前限制见 [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)。

## 前端

需要 Node.js 20.19+ 或 22.12+（与当前 Vite 版本要求一致）。

```powershell
cd frontend
npm install
npm run dev
```

生产构建检查：`npm run build`

复制 `frontend/.env.example` 为 `frontend/.env.local`，按需设置 `VITE_API_BASE_URL`。计算器页的“计算到手收入”按钮会调用后端计算接口，展示结果汇总、扣款明细、累计预扣过程和年终奖方案。
