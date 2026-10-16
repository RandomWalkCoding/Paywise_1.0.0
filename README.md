# Paywise 薪算清｜GitHub 上传说明

## 1. 项目简介

Paywise（薪算清）是一个面向在职员工和求职者的个人薪酬决策工具。用户输入工资、津贴、绩效、年终奖、工作地及社保/公积金缴纳地后，系统匹配对应月份的政策参数，计算社保、公积金、累计预扣个税和奖金税额，并解释每个结果的计算口径。

项目重点解决“税前总包看起来很高，但实际到手是多少、公司成本是多少、不同 Offer 怎么比较”的问题。

## 2. 当前已实现能力

- 薪酬计算：支持固定工资、津贴、绩效、年终奖、其他应税收入和税后扣款。
- 地区政策：工作城市、社保缴纳地、公积金缴纳地可以分别设置，并按计算月份匹配政策版本。
- 扣款计算：支持社保和公积金基数上下限、个人缴费、公司缴费及基数解释。
- 个税计算：支持居民个人工资薪金累计预扣，展示累计应纳税所得额、税率、速算扣除数和本月预扣税。
- 年终奖分析：在匹配政策允许时，比较单独计税和并入综合所得两种方案。
- 结果解释：同时展示到手现金、个人资产增加和税前总包，并列出假设、政策来源、可信度和待确认事项。
- 方案管理：支持保存、读取、复制、重命名、删除、恢复方案，并保存输入和结果快照。
- Offer 对比：最多选择 4 个方案，对比月到手、年收入、本月个税、个人公积金和年度总包。
- 结果分享：支持导出结果和复制脱敏摘要，分享内容不包含原始输入。
- 政策审核接口：支持政策导入、待审核、通过或驳回的流程，正式匹配只使用已审核政策。

## 3. 技术栈

- 前端：React、TypeScript、Vite、React Router
- 后端：Python、FastAPI、Pydantic
- 测试：pytest、Playwright 浏览器集成验收
- 接口：REST API，统一使用 /api/v1 前缀

## 4. 目录结构

```text
.
├─ backend/                 FastAPI 服务、计算引擎、政策和方案接口
│  ├─ app/
│  └─ tests/
├─ frontend/                React 页面和交互
│  └─ src/
├─ PRD.md                   产品需求文档
├─ TECHNICAL_DESIGN.md      技术方案
├─ RELEASE_CHECKLIST.md     本地验收记录和发布限制
└─ GITHUB_UPLOAD_GUIDE.md   GitHub 上传与运行说明
```

## 5. 本地运行

### 后端

要求 Python 3.12 或更高版本。

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

启动后可访问：

- API：http://127.0.0.1:8000
- Swagger：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/v1/health

### 前端

要求 Node.js 20.19+ 或 22.12+。

```powershell
cd frontend
npm install
npm run dev
```

默认页面：http://127.0.0.1:5173。

如需修改 API 地址，可复制 frontend/.env.example 为 frontend/.env.local，设置：

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## 6. 验证命令

```powershell
cd backend
python -m pytest -q

cd ..\frontend
npm run build
```

前后端同时启动后，可以运行浏览器集成验收：

```powershell
python frontend/integration_check.py
```

## 7. 上传到 GitHub

在项目根目录执行：

```powershell
git init
git add .
git commit -m "feat: add Paywise salary calculator MVP"
git branch -M main
git remote add origin https://github.com/<your-account>/<your-repository>.git
git push -u origin main
```

如果本地已经存在 Git 仓库，只需要确认远程地址后执行：

```powershell
git status
git add .
git commit -m "docs: refine project documentation"
git push
```

上传前请检查以下内容：

- 不要提交 backend/.venv/、frontend/node_modules/、.env.local 和真实个人薪酬数据。
- 政策示例数据当前带有“待官方审核”标识，不应描述为正式税务政策。
- README、PRD 和验收记录中的项目状态应与实际代码一致。
- 如果仓库公开，建议在 GitHub 的 About 区域补充 React、TypeScript、FastAPI、salary-calculator 等主题。

## 8. 当前版本边界

这是一个可本地演示和验收的 MVP。方案和政策导入目前使用进程内存，服务重启后不会保留记录；当前仅内置上海、北京示例政策，其他地区可能进入估算状态；项目尚未提供登录、权限隔离和生产部署配置。因此，当前版本适合用于产品演示、作品集展示和后续工程化迭代，不应直接作为正式税务申报或公网生产服务。
