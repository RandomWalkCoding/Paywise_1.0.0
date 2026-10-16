# Paywise 技术方案

## 1. 技术目标

Paywise 采用前后端分离架构。前端负责表单、交互、结果可视化和方案管理；后端负责薪酬计算、政策版本、数据校验和结果解释。

首版优先保证三件事：计算结果可重复、政策版本可追溯、前后端可以独立开发和部署。

## 2. 推荐技术栈

### 前端

- React + TypeScript
- Vite
- React Router
- TanStack Query：服务端数据请求和缓存
- Zod：表单和 API 响应校验
- Tailwind CSS 或项目统一 CSS 方案
- Vitest + Testing Library

### 后端

- Python 3.12+
- FastAPI
- Pydantic：请求、响应和领域模型
- SQLAlchemy 2.x
- Alembic：数据库迁移
- pytest

### 基础设施

- PostgreSQL：政策、方案、计算记录和版本数据
- Redis：可选，用于短期缓存政策查询和限流
- Docker Compose：本地开发
- OpenAPI：前后端接口契约
- GitHub Actions：测试、类型检查和构建

如果团队已经确定其他技术栈，应保持前后端接口和领域规则不变，再替换实现层。

## 3. 模块划分

### 前端模块

```text
frontend/
  src/
    app/                 应用入口、路由、全局配置
    pages/               首页、计算器、结果、方案对比、政策说明
    components/          通用 UI 组件
    features/
      calculator/        收入输入、扣款输入、结果展示
      comparison/        Offer 和薪酬方案对比
      policy/             政策版本和来源展示
      scenarios/          方案保存、复制、导出
    api/                 API client 和接口类型
    schemas/             表单校验
    state/               客户端状态
    styles/              主题和全局样式
```

### 后端模块

```text
backend/
  app/
    api/                 路由、请求响应模型
    domain/
      calculator/        个税、社保、公积金、奖金领域规则
      scenarios/         薪酬方案领域模型
      policy/             政策版本领域模型
    services/            编排计算流程和结果解释
    repositories/        数据访问接口和实现
    models/              ORM 模型
    schemas/             Pydantic DTO
    policy_data/         政策种子数据和导入工具
    core/                 配置、日志、异常、鉴权预留
  tests/
```

### 边界原则

- 个税、社保、公积金规则只存在于后端领域层，前端不得复制计算逻辑。
- 前端只负责展示后端返回的计算结果和解释。
- API 使用版本化路径，例如 `/api/v1/calculations`。
- 金额统一使用 `Decimal` 或最小货币单位，禁止使用浮点数处理金额。
- 每次计算绑定 `policy_version` 和 `calculation_month`。

## 4. API 初步契约

### 创建计算

`POST /api/v1/calculations`

请求至少包含：计算月份、工作地、社保地、公积金地、收入项目、扣除项目和奖金配置。

响应至少包含：到手现金、个人资产增加、税前总包、社保明细、公积金明细、个税明细、政策版本、结果可信度标签和解释列表。

### 获取政策

`GET /api/v1/policies?region=shanghai&month=2026-10`

响应包含适用规则、版本、生效日期、来源、审核状态和缺失字段。

### 方案管理

- `POST /api/v1/scenarios`
- `GET /api/v1/scenarios`
- `GET /api/v1/scenarios/{id}`
- `POST /api/v1/comparisons`

OpenAPI 文件是前后端共同依据。接口变更必须先更新 OpenAPI 和示例，再修改实现。

## 5. 计算领域设计

计算流程固定为：

```text
输入标准化 -> 政策匹配 -> 基数校验 -> 社保公积金计算
-> 累计预扣个税计算 -> 年终奖方案计算 -> 汇总结果 -> 生成解释和可信度标签
```

规则函数应当尽量纯函数化，输入明确、输出确定，不直接访问数据库。政策读取和计算编排由 service 层完成。

## 6. 数据安全和隐私

- 默认不要求登录。
- 不保存身份证号和真实姓名。
- 工资条原图默认不落库。
- 保存方案时只保存计算所需字段。
- 日志不得输出完整工资输入和个人敏感数据。
- 分享结果默认脱敏。
