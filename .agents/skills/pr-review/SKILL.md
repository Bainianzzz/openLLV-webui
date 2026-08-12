---
name: pr-review
description: Use when reviewing openLLV-webui (Gradio webui) PRs. Checks ui components, inference service methods, SQLAlchemy models, utils helpers, SwanLab monitoring, docs, tests, dependency changes, and merge gates.
---

# PR 审核 (openLLV-webui)

## 概述

按照本项目的 webui 约定审核 PR，并在用户明确授权后用 `gh` CLI 提交结构化结论。目标不是追求唯一写法，而是确认变更符合项目分层、错误语义、文档和测试要求，不引入功能回归、性能劣化或安全问题。

技术栈：**Python 3.10+**、**Gradio**、**openLLV**、**SQLAlchemy 2.x**、**SwanLab**、**pytest**、**uv**（依赖与 Python 环境统一由 uv 管理）。项目结构：`inference`（webui 服务方法：`model` SQLAlchemy 模型定义、`enhance`/`train` 业务编排、`utils` 工具函数与后台任务 `utils/task`）、`ui`（webui 界面，每个包的 `__init__.py` 负责组装页面组件，`ui/<domain>` 为各业务邻域的子组件模块）、`test`（webui 测试用例，mock data，共享 fixture 在 `test/mock`）、`.agents/skills/openllv/reference`（openLLV 文档）。

适用：PR 合并前审核、`gh pr diff` / `gh pr review`、检查 ui 组件、inference 服务方法、模型、utils、文档、测试、依赖变更与合并门禁。
不适用：无 PR 上下文的本地单文件解释；openLLV 上游仓库的 PR（本仓库与上游仅通过依赖锁定（`uv.lock`）对接）。

> 参考技能：核对 Gradio API 用法用 `gradio` 技能，核对 openLLV 用法用 `openllv` 技能（不直接阅读 openLLV 源码），核对数据库写法用 `sqlalchemy` 技能，核对 SwanLab 用法用 `swanlab-skill` 技能。

## 审核流程

1. 复杂 PR 可并行分派两个视角（如果当前工具和用户授权允许）：代码库约定映射（分层、命名、测试辅助工具、既有模式，带文件行号）和深度审核（正确性、性能、安全、验证）。小 PR、纯文档或单文件小改可跳过。
2. 先确认 PR 意图、base 分支和 diff，再读实现。PR 可能基于功能分支而非 `main`，范围完整性按相对 base 的增量判断。

```bash
gh pr view <PR>
gh pr diff <PR>
gh pr view <PR> --json files,additions,deletions,baseRefName,headRefName
```

3. 核对文件列表与 patch，确认无遗漏或无法读取的文件；对二进制、rename 等特殊文件单独确认。逐项判断适用范围：通用执行面、ui 组件与页面组装、inference 服务方法、SQLAlchemy 模型与数据库、utils 工具函数、docs 文档、测试覆盖、依赖与配置。
4. 读取完整文件和调用上下文，不只看 patch；对关键发现抽样验证实际文件状态，例如 `git show origin/<head-branch>:<file-path>`。
5. 对行为变更追踪入口、全部调用方、数据/状态写入和输出消费方，不要只审查被修改的函数。
6. 标严重性前可对照既有模式，但既有实现只证明一致性，不能证明正确或安全；破坏主链路、数据或行为回归、明显性能或安全风险仍按影响定级。

## 范围维度

每个 PR 先判断以下维度是否适用，再确认覆盖完整性。检查项为通用规则，按业务正确性、性能、安全三类组织；同类规则只保留在最贴近的维度，不限于当前实现。

### 0. 通用执行面与仓库配置

适用条件：所有 PR。

- 检查所有新增、修改、删除和重命名；新增顶层路径或无法识别的文件必须说明用途与执行方式。
- 执行入口（`.husky/pre-commit`、`app.py`、`pyproject.toml` 与测试配置）不能仅因不在业务目录中而跳过。
- 检查 import-time side effect 和配置驱动入口，避免小型配置变更激活未修改代码中的危险路径。

### 1. ui 组件与页面组装

适用条件：`ui/**` 有变更。

业务：

- 组件正确注册到页面结构（Blocks/Tabs/布局上下文），由包级组装入口装配；组件返回的引用与调用方解构一致。
- 事件监听器（click/submit/change 等）的 `inputs`/`outputs` 顺序与回调函数签名严格一致。
- 回调对框架可能传入的空值（未上传、未填写）有明确处理；错误以可读异常抛出交由框架展示，不吞异常、不返回误导结果。
- 用户文本输入解析（JSON、数值、枚举）失败时抛出带原因的明确错误，不把部分解析结果传入下游。
- 动态选项来源（外部 API、配置、数据查询）可能为空，默认值选取需判空，避免渲染或启动崩溃。

性能：

- 渲染与事件回调避免重复执行重计算或对同一数据源重复查询。
- 大数据量展示（表格、列表、图）要有行数、分页或高度限制，避免前端卡顿。
- 长时间任务评估队列/异步配置，避免阻塞其他事件交互。

安全：

- 按具体渲染上下文检查动态内容（用户输入、数据库内容、外部数据）的编码或净化，防止 HTML/Markdown/脚本注入和 XSS。
- 上传/选择组件的类型与大小限制与后续处理方式一致。
- 新增或修改敏感操作要评估部署暴露面（host/share），不能只依赖控件是否可见。

### 2. inference 服务方法

适用条件：`inference/**` 有变更。

业务：

- 业务编排有完整生命周期/状态机（创建 → 执行 → 成功/失败）；失败路径记录可追踪的错误信息与时间点，不产生悬空记录、不吞异常。
- 外部库（openLLV）调用方式以其官方文档/参考技能为准，不臆测签名与返回值结构；结果转换与消费方组件类型匹配。
- 空值/类型不符输入有明确前置处理；参数默认值使用不可变对象并与调用方一致。
- 非法枚举/类型输入抛明确错误，不静默返回空或崩溃。
- 对外数据结构（列序、字段名、类型）是公共契约，变更必须同步消费方（UI、其他模块、测试、文档）。
- 分层：业务方法只做编排与数据读写，不掺入界面逻辑；界面层不直接访问数据层。

性能：

- 查询必须带排序与 limit，避免无界查询；条件尽量下推数据库，不加载整表再处理；模糊搜索/大结果集评估索引与执行成本。
- 资源（数据库会话、文件句柄、连接）生命周期明确、用完即关，不跨请求持有。
- 避免循环内查询/调用（N+1）。
- 大对象（图片、张量、大文件）处理评估内存占用。

安全：

- 用户可见错误收敛为可读信息，不暴露内部路径与堆栈。
- 用户可控内容透传给外部库/系统调用前，评估其使用方式（任意文件读取、命令执行、资源耗尽等风险），明显恶意输入要拦截。
- 动态查询值参数化，动态字段/表名白名单约束，不字符串拼接 SQL。

### 3. SQLAlchemy 模型与数据库

适用条件：`inference/model/**` 或建表/连接逻辑有变更。

业务：

- 字段类型、可空、默认值与业务语义一致；新增表/字段说明初始化方式与既有数据兼容性（初始化只建新表不迁移）。
- ORM 风格与项目约定一致（类型化列）；复杂类型列（JSON 等）读写类型明确。
- 状态/枚举值在模型、服务、界面各处保持一致。

性能：

- 高频过滤/排序字段声明索引。
- 批量写使用批量 API；事务范围最小化。
- 并发写入评估锁等待与冲突（尤其轻量级数据库），连接配置合理。

安全：

- 连接串、路径等敏感配置不进入日志、响应、测试快照。

### 4. utils 工具函数

适用条件：`inference/utils/**`（含后台线程与任务存储 `utils/task`）有变更。

业务：

- 单一职责、返回类型稳定、输入输出契约明确并写入 docstring。
- 异常输入（None、空集合、类型不符、非法值）行为明确（报错或约定转换），不静默产出损坏数据。
- 遵循项目规则：信任框架/库返回值，不添加冗余校验。

性能：

- 避免重复计算与重复 IO；批量文件/数据处理注意内存占用。
- 纯函数不隐式依赖可变全局状态。

安全：

- 文件写入目录固定或经校验，文件名不依赖用户可控内容，防路径穿越与覆盖；评估绝对路径、符号链接边界。
- 不把敏感数据返回给非预期调用方。

### 5. 文档

适用条件：`.agents/skills/openllv/reference/**`、`README.md` 有变更。

- 新增功能/参数/行为变更同步更新对应文档（参数名、默认值、支持列表、示例）。
- 教程/说明性文档与实际行为一致，示例可运行。
- 由脚本从外部来源同步的文档不本地手改覆盖；本地说明放对位置。

### 6. 测试覆盖

适用条件：任何行为变更都适用。

- 新行为、新分支必须有测试；测试数据用 mock，不依赖真实外部资源（网络、GPU、真实数据库）。
- 覆盖成功路径与关键错误分支：输入非法、依赖失败、边界值、空结果。
- 对外契约（数据结构、枚举、错误语义）有断言。
- 测试命名与组织符合项目约定；审核测试改动是否删除/放宽断言、增加 skip/xfail、mock 掉真实路径或削弱共享 fixture。项目规则中的“不擅自更新既有测试”约束审核者，不替代对 PR 测试变更的语义判断。
- 测试通过只是证据之一；无断言测试、只验证 mock 返回值或未覆盖真实调用链不能证明行为正确。

### 7. 依赖与配置

适用条件：依赖清单/锁文件、应用配置、启动/部署脚本或 CI 工作流有变更。

- 新依赖必须向用户报告（项目规则：不得自行添加），纳入统一依赖管理并同步锁定文件。
- 比较直接与传递依赖的名称、版本、来源与锁定文件变化，重点检查 Git/URL 依赖和异常的大规模锁文件变化。
- 新增配置项有默认值或明确的启动失败语义；路径类配置相对固定基准解析。
- 应用入口/启动链路（初始化 → 组装 → 启动）保持完整。
- 检查本地 pre-commit 门禁（`.husky/pre-commit`）未被绕过或放宽。

## 质量与严重性

逐文件审查：正确性（PR 意图、返回值、空值、生命周期/状态机、重复请求）、数据契约（模型、对外数据结构、文档）、分层（ui / inference / model 职责）、性能（查询、资源生命周期、大对象、并发）、安全（注入、路径、敏感信息、暴露面）、可维护性（命名、复杂度、生成物）、验证测试。

| 前缀          | 含义           | 作者需要                                                                                                |
| ------------- | -------------- | ------------------------------------------------------------------------------------------------------- |
| **阻塞:**     | 阻塞合并       | 破坏主链路、明显构建/运行失败、数据丢失或不可恢复、注入/路径穿越/凭证泄露等严重安全问题                 |
| **必须修改:** | 合并前必须处理 | 返回值/状态码错误、状态不一致、对外契约不同步、覆盖范围缺失、分层明显违规、关键分支无测试、明显性能劣化 |
| **建议:**     | 建议处理       | 值得改进但不阻塞，例如命名、局部抽象、测试增强、文档更清晰、查询加索引                                  |
| **细节:**     | 次要问题       | 格式、拼写、微小风格问题，通常可由 formatter/linter 处理                                                |
| **说明:**     | 信息记录       | 不要求行动，记录上下文或后续风险                                                                        |

变更规模：100 行左右最好；300 行如果是单一逻辑可接受；超过 500 行应要求拆分。大重构混在一起时优先要求拆分或至少解释边界。

## 提交审核

使用 `gh` ，优先把可行动的 finding 提交为 **PR diff 上的 inline review comment**，这样作者能在 GitHub 网页上逐条 Resolve。`gh pr review --body-file` 只适合提交顶层 review 结论；顶层正文里的 finding 不是可 resolve 的代码线程。

### 选择提交方式

- **无 finding 或只需总评**：用 `gh pr review --approve/--comment --body-file` 提交顶层结论。
- **有可定位 finding**：用 `gh api repos/{owner}/{repo}/pulls/<PR>/reviews --input <review-json>` 批量创建 review，并把每个 finding 放进 `comments[]`。
- **有阻塞或必须修改 finding**：review `event` 用 `REQUEST_CHANGES`；只有建议/细节时用 `COMMENT`；确实通过且无可行动 finding 时才用 `APPROVE`。
- **无法挂到 diff 行的 finding**：例如缺少测试、缺少文档、跨文件架构问题，放进顶层 `body` 的 “未挂行发现” 部分，不要强行挂到无关代码行。

### 定位 inline comment

1. 先取 patch，确认 finding 的位置在 PR diff 中：

```bash
gh pr diff <PR> --patch --color=never
```

2. 对每个可定位 finding 选择最贴近根因的 diff 行：
   - 新增或修改后的代码：`side: "RIGHT"`，`line` 使用新文件中的行号。
   - 删除导致的问题：`side: "LEFT"`，`line` 使用旧文件中的行号。
   - 多行问题可用 `start_line`、`line`、`start_side`、`side`，但单行更稳定。
3. 只评论 diff 中存在的行。若目标行不在 diff 中，改放顶层 `body`，避免 API 失败或把评论挂错位置。
4. inline comment 内容要直接说明问题、影响和建议；不要在同一条 comment 中塞多个独立 finding。

### 提交 inline review

写入 `/tmp/pr-review.json` 后提交：

```bash
gh api --method POST repos/{owner}/{repo}/pulls/<PR>/reviews --input /tmp/pr-review.json
```

提交后核对 API 返回的 review ID 与状态；权限不足或提交失败时不得把本地草稿报告为已提交。

JSON 结构见 `reference/review-comments.json`，逐条替换 `comments[]` 后提交。

如果没有 inline finding，仅提交顶层 review。审核正文含 Markdown、引号或特殊字符时用 `--body-file`：

```bash
gh pr review <PR> --request-changes --body-file <review-body>
gh pr review <PR> --approve --body-file <review-body>
gh pr review <PR> --comment --body-file <review-body>
```

正文结构见 `reference/review-body.md`。

## 验证要求

默认门禁：

```bash
uv run pytest
```

按变更补充：

```bash
uv run pytest test/inference/enhance -q
uv run pytest test/inference/train -q
```

- 项目规则：不要自行启动 `gradio` 运行冒烟测试，审核结论中直接给出最简要的测试点即可。
- 测试均为 mock data；涉及数据库操作使用 `test/mock` 导出的 `mock_*` 上下文管理器（`mock_db` / `mock_records_db` / `mock_train_db` / `mock_train_records_db`），另有 `mock_hf_download`（数据集下载）与 `mock_config`（配置）供测试使用。
- 本地运行 pytest 前需保证 `config.yaml` 存在（`inference` 包 import 时即读取配置并创建 engine）；缺失时执行 `cp example.config.yaml config.yaml`，与 CI（`.github/workflows/test.yml`）一致。
- 如果本地环境因依赖下载或 sandbox 缓存不可用导致无法运行，审核结论必须写明原因，并尽量运行更窄的包级测试。CI/pre-commit 失败时优先以 CI 日志为准。

## 代码规范门禁

以项目规则（`AGENTS.md`）、`pyproject.toml`、`uv.lock` 和既有代码风格为准。不要因个人偏好要求重写；违反项目规则、可维护性或明显错误语义时才作为 finding。

| 主题    | 门禁                                                                                                    |
| ------- | ------------------------------------------------------------------------------------------------------- |
| 依赖    | 不得自行添加新依赖，确需新增要向用户报告；依赖与 Python 环境统一用 uv 管理，`pyproject.toml` 不擅自更新 |
| 路径    | 同一个包下用相对路径，跨包一律用基于项目根目录的绝对路径                                                |
| 校验    | 信任 gradio 提供的参数和 openLLV 的返回值，不添加冗余的校验逻辑和测试                                   |
| openLLV | 不直接阅读 openLLV 源码，通过 `openllv` 技能了解其用法                                                  |
| 测试    | 测试文件/测试函数以 `test_` 开头；图片、数据库操作均为 mock data；不擅自更新既有测试                    |
| 可读性  | 函数职责清晰；避免用 `data`、`result`、`temp` 承载复杂业务语义                                          |

## 完成验证

- [ ] 所有阻塞发现已解决
- [ ] 所有必须修改发现已解决或明确延期并附理由
- [ ] 适用范围维度已确认
- [ ] 完整文件列表与特殊文件变化已核对
- [ ] `uv run pytest` 已通过，或明确说明无法运行的原因
- [ ] finding 已进入审核草稿；若用户授权提交，可定位 finding 使用 inline comments，无法挂行的问题进入顶层 body
- [ ] 若已提交，用户授权与 review 状态已核对
