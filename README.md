# Paywise 薪算清

> 一个面向中国职场人的薪酬计算与 Offer 决策工具。

Paywise 把税前薪资、奖金、社保、公积金和个税放进同一套可解释的计算流程，帮助你看清每月到手、年度收入和不同 Offer 的真实差异。项目还接入 OpenAI 兼容格式的 GLM 模型，为方案比较提供结构化的 AI 薪酬分析。

## ✨ 核心能力

- **到手收入计算**：工资、津贴、绩效、年终奖、专项扣除与其他应税收入
- **社保与公积金**：支持城市、缴费基数和个人/雇主缴纳明细
- **个税与奖金测算**：累计预扣过程、年终奖单独/合并计税对比
- **Offer 方案管理**：保存、重命名、软删除、恢复和历史快照
- **多方案对比**：最多同时比较 4 个方案的现金流、税费和年度总包
- **AI 智能分析**：按现金流、年度总包、税费公积金、政策确定性四个维度给出建议
- **可解释结果**：展示计算假设、政策来源、可信度和需要人工核验的事项

## 🧱 技术栈

| 层  | 技术                                                   |
| -- | ---------------------------------------------------- |
| 前端 | React、TypeScript、Vite、React Router                   |
| 后端 | FastAPI、Pydantic、Python                              |
| AI | OpenAI-compatible Chat Completions API、GLM-5.3-Flash |
| 测试 | pytest、TypeScript、Vite production build              |

## 🚀 本地运行

### 1. 启动后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PAYWISE_AI_API_KEY="你的 API Key"
$env:PAYWISE_AI_MODEL="glm-5.3-flash"
uvicorn app.main:app --reload
```

后端地址：`http://127.0.0.1:8000`；接口文档：`http://127.0.0.1:8000/docs`

### 2. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

前端地址：`http://127.0.0.1:5173`

如需修改 API 地址，可复制 `.env.example` 为 `.env.local`：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## 🧪 验证

```powershell
cd backend
pytest -q
cd ..\frontend
npm run build
```

## 🔌 主要接口

- `GET /api/v1/health`：服务健康检查
- `POST /api/v1/calculations`：执行薪酬计算
- `GET/POST /api/v1/scenarios`：读取和保存薪酬方案
- `GET /api/v1/scenarios/{id}`：读取方案快照
- `POST /api/v1/scenarios/ai-analysis`：生成 AI Offer 分析

## ⚠️ 数据与隐私说明

- 当前方案存储为进程内存，服务重启后需要重新保存。
- 仓库中的政策数据用于演示和开发，不构成税务、法律或薪酬承诺。
- AI 分析仅使用当前选择的方案计算结果；生产部署时请自行配置密钥管理、日志脱敏和访问控制。
- 不要将真实 API Key 提交到 Git 仓库，建议通过环境变量或部署平台 Secret 注入。

## 📄 License

本项目当前用于学习、演示和产品原型开发。正式开源前请补充合适的许可证。
