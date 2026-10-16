# Paywise 代码规范与 Git 协作

## 1. 分支策略

```text
main                 可发布版本
develop              集成分支
feature/frontend-*   前端阶段任务
feature/backend-*    后端阶段任务
```

每个会话只负责一个小任务、一个分支。分支名必须带任务编号，例如：

- `feature/frontend-001-calculator-form`
- `feature/backend-001-policy-model`

前后端可以并行开发。后端任务之间默认串行：后一个后端任务必须基于前一个后端任务已合并或明确的接口契约。

## 2. 会话任务边界

每个 AI 会话的提示词必须包含：

1. 任务编号和目标。
2. 允许修改的目录。
3. 依赖的接口或前置分支。
4. 验收标准。
5. 必须运行的测试或检查。
6. 完成后需要汇报的文件、测试和未决问题。

会话不得顺手修改其他任务范围内的文件。发现依赖缺失时记录问题，不自行扩大任务。

## 3. 提交规范

提交信息使用：

```text
feat(frontend): add salary input form
feat(backend): add policy version model
fix(backend): correct cumulative tax calculation
docs: update api contract
test(backend): add annual bonus cases
```

一个提交尽量只表达一个完整变化。提交前运行格式化、类型检查和相关测试。

## 4. TypeScript 规范

- 开启 strict 模式。
- 禁止 `any`，确有必要时写明原因。
- API 响应用 Zod 或生成的类型校验。
- 金额展示统一使用金额格式化函数。
- 组件只负责展示和交互，计算规则通过 API 获取。
- 不在 JSX 中写复杂计算。

## 5. Python 规范

- 使用 Ruff 格式化和检查。
- 使用类型注解。
- 使用 Decimal 处理金额。
- 领域计算函数优先写成纯函数。
- 路由层不实现税务规则。
- 异常返回统一错误结构，不返回堆栈。

## 6. API 规范

- 路径使用小写和复数名词。
- 使用 `/api/v1` 版本前缀。
- 请求和响应字段使用 `snake_case`，前端转换由 API client 统一处理。
- 错误包含 `code`、`message` 和可选 `field_errors`。
- 破坏性变更必须升级 API 版本或提供兼容期。

## 7. 集成流程

```text
创建任务分支 -> 完成小任务 -> 本地检查 -> 提交
-> 合并到 develop -> 集成测试 -> 合并 main -> 发布
```

前后端并行时，双方以 OpenAPI 和 mock 数据为共同契约。前端可以先用 mock 开发，不等待后端实现；后端先实现接口和契约测试，再接入真实数据库。

## 8. 合并冲突处理

- 同一文件尽量只由一个任务修改。
- 冲突优先由产生冲突的任务负责人解决。
- 不直接覆盖他人分支。
- 合并后重新运行受影响模块测试。
- 不使用 `git reset --hard` 丢弃他人工作。
