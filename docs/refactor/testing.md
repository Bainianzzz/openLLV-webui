# openLLV WebUI 后端测试边界

> 状态：提案  
> 适用架构：FastAPI + SQLAlchemy + 三个固定 worker slot  
> 更新日期：2026-08-21

## 1. 测试目标

测试重点不是证明 openLLV 或 PyTorch 本身正确，而是验证本项目对它们的编排是否正确：

- API 是否正确校验请求并返回稳定的 HTTP 合约。
- 任务是否正确进入队列、运行和最终状态。
- enhancement、training、dataset_download 三个固定 worker slot 是否互不阻塞。
- 同一个 slot 是否最多执行一个任务。
- 取消、超时、异常退出和 API 重启是否有明确结果。
- 文件是否只在 managed storage 内读写。
- 数据库事务和状态 compare-and-set 是否避免竞态覆盖。
- openLLV、SwanLab、Hugging Face 等外部集成的参数映射是否正确。

测试不验证第三方框架内部实现，也不依赖 GPU、外部网络、真实 SwanLab 项目或真实 Hugging Face 仓库。

## 2. 测试分层

```text
Unit tests
  -> API / service / storage / schema / handler

Component tests
  -> WorkerSupervisor + fake process + temporary SQLite

Integration tests
  -> FastAPI + SQLAlchemy + fixed worker process + fake handlers

Contract tests
  -> API response shape + frontend API client

Migration tests
  -> legacy SQLite -> new schema
```

默认执行单元和 component tests；integration tests 在 CI 中执行；真实设备测试单独执行，不作为普通 pytest 默认路径。

## 3. 测试替身边界

### 3.1 openLLV

测试代码不得加载真实模型或调用真实推理。使用 fake adapter：

```text
FakeCatalog
FakeEnhancementAdapter
FakeTrainingAdapter
```

fake adapter 能配置：

- 成功返回。
- 抛出普通异常。
- 在指定检查点等待取消。
- 返回单图结果。
- 返回批量 saved paths。
- 返回训练 history 和 checkpoint metadata。
- 模拟未知模型、未知算法和非法参数。

测试 handler 与 adapter 之间的参数映射，不测试模型输出质量。

### 3.2 SwanLab

使用 fake monitor 或 mock `BatchSwanLabTrainer`：

- 验证启用监控时选择正确的 trainer path。
- 验证 API key 来自服务端配置，而不是 task payload。
- 验证 project、experiment 和 URL 被正确记录。
- 验证监控失败时按照配置决定任务失败或只记录 warning。

测试中不使用真实 API key，也不连接 SwanLab。

### 3.3 Hugging Face

mock：

- `list_repo_files()` 返回固定文件列表。
- `hf_hub_download()` 写入临时目录中的 mock 文件。
- 下载过程中在文件边界收到取消。
- 某个文件下载失败。

不执行真实网络请求，不使用用户 home 目录的 Hugging Face cache。

### 3.4 文件和图片

所有图片使用临时目录中的 mock data。测试：

- 合法 JPEG/PNG 上传。
- 非图片文件。
- 超过大小限制。
- 文件名包含路径分隔符。
- 符号链接越界。
- 临时文件成功发布和失败清理。
- 批量目录 artifact 的内容和路径边界。

## 4. API 测试边界

API 测试使用 FastAPI test client 和 dependency override，不启动真实 uvicorn，不启动真实 openLLV worker。

### 4.1 Health

必须覆盖：

- `/health/live` 在数据库不可用时仍只反映进程存活。
- `/health/ready` 在数据库不可用时返回 `503`。
- `/health/ready` 在 storage 不可写时返回 `503`。
- worker slot 尚未启动时返回 `503`。
- 正常状态返回三个 worker slot 的状态。

### 4.2 Catalog

必须覆盖：

- catalog response 只包含 JSON 可序列化字段。
- algorithms、models、datasets 的名称和 aliases 正确映射。
- `llv.list_available()` 的展示名称与可接受 lookup key 不混淆。
- form schema 的默认值和范围来自项目定义，而不是任意反射。
- catalog adapter 异常时返回稳定错误，不泄露 traceback。

### 4.3 Artifact

必须覆盖：

- 单文件上传返回 `201` 和 image artifact。
- 多文件上传返回一个 directory artifact。
- 文件大小、MIME 和内容校验。
- 文件发布失败时不留下可用 artifact 记录。
- artifact content endpoint 不允许 `../`、绝对路径和符号链接越界。
- 已删除或不存在的 artifact 返回 `404 artifact_not_found`。
- 响应不包含服务器绝对路径。

### 4.4 Enhancement

必须覆盖：

- traditional 请求正常创建 queued task。
- deep 请求正常创建 queued task。
- 不存在的 method 返回 `409 unsupported_method`。
- backend 与 method 类型不匹配时拒绝请求。
- 不存在的 input artifact 返回 `404`。
- 参数不是 JSON object 时返回 `422`。
- 单图结果关联 `output_artifact_id`。
- 批量结果关联一个 directory `output_artifact_id`，目录中包含所有输出文件。
- 后端不在 HTTP 请求中执行 fake adapter。

### 4.5 Dataset

必须覆盖：

- 允许的 `dataset_key` 可以创建下载任务。
- 未配置的 repo ID 不能通过请求直接注入。
- 同一 dataset 的重复下载策略符合 `overwrite` 约定。
- 下载失败记录 error code 和 dataset 状态。
- 下载取消后不把半成品标记为 available。

### 4.6 Training

必须覆盖：

- model、dataset、epochs、batch_size、lr、resize、device 校验。
- 不存在或非 available dataset 被拒绝。
- 不支持的 device 被拒绝。
- `num_workers` 不能由客户端任意覆盖，首期固定为 0。
- SwanLab key 不出现在请求模型、数据库 payload 或 response。
- 训练完成后保存 history、best_val_loss 和 checkpoint artifact。
- checkpoint 不存在时任务不能错误标记为 succeeded。

### 4.7 Task

必须覆盖：

- 列表分页、kind 筛选和 status 筛选。
- 默认排序为 `created_at DESC, id DESC`。
- 详情正确返回对应 job 类型。
- 不存在 task 返回 `404 task_not_found`。
- queued 任务取消后不启动 worker。
- running 任务取消后进入 cancelling。
- 最终状态重复取消是幂等的。
- response 不暴露 worker 内部 traceback、绝对路径和密钥。

## 5. Service 和数据库测试边界

Service 测试使用临时 SQLite 和每个测试独立 Session。测试不连接真实 `data/app.db`。

### 5.1 Task 创建

测试：

- task 与 enhancement/training/download detail 在同一个事务中创建。
- 任一 detail 校验失败时不留下孤立 task。
- task 初始状态为 `queued`。
- created_at 使用 UTC。
- artifact、dataset、method 的外键或业务校验失败时完整回滚。

### 5.2 状态迁移

测试允许和禁止的迁移：

| 当前状态 | 允许 |
| --- | --- |
| `queued` | `running`、`cancelled` |
| `running` | `succeeded`、`failed`、`cancelling` |
| `cancelling` | `cancelled`、`failed` |
| `succeeded` | 无 |
| `failed` | 无 |
| `cancelled` | 无 |

重点测试：

- 成功事件与取消请求同时到达时，只有先提交的条件更新生效。
- cancelling 状态不能被后到的 succeeded 无条件覆盖。
- 失败 task 不能再次被 worker 领取。
- slot 只能领取同 kind 的 queued task。

### 5.3 查询和分页

测试：

- 相同 created_at 时使用 id 保证稳定排序。
- page/page_size 边界和最大值。
- kind/status 组合筛选。
- total 与 items 一致。
- 列表查询不会触发不必要的关系级联加载。

### 5.4 路径和 artifact

测试：

- relative path 解析始终位于对应 managed root。
- uploads、output、checkpoints、datasets 不能互相越界访问。
- 临时文件不出现在成功 artifact 列表中。
- task 删除或失败不会自动删除仍被历史记录引用的 artifact。

## 6. WorkerSupervisor 测试边界

Supervisor 测试不加载真实模型，使用 fake process 或短生命周期的测试子进程。

### 6.1 固定 slot 并发

必须验证：

- 启动后存在 enhancement、training、dataset_download 三个 slot。
- 每个 slot 同时最多有一个 active task。
- 三个不同 kind 可以同时运行。
- enhancement-2 不会在 enhancement-1 结束前发送给 enhancement worker。
- training 任务不会阻塞 enhancement 和 download slot。
- task kind 与 worker kind 不匹配时不会发送 command。

### 6.2 正常生命周期

测试：

- queued task 被对应 slot 领取并更新为 running。
- worker 发出 started event 后 task 保持 running。
- succeeded event 创建结果 artifact 并最终化 task。
- handler exception 产生 failed task 和 error code。
- 一个任务结束后固定 worker 可以继续处理同 kind 的下一个任务。

### 6.3 取消和重启

测试：

- queued 取消不启动子进程。
- running 取消发送一次 cancel control message。
- 重复取消不重复发送信号。
- 协作式下载在文件边界停止。
- 阻塞 fake handler 在宽限期后被终止。
- 取消或异常后的 worker slot 被重启，其他两个 slot 不受影响。
- worker crash 将当前 task 标记为 `failed/worker_lost`，并恢复该 kind 的空闲 worker。
- API 关闭时三个 worker 都收到 shutdown。

### 6.4 Worker 重启和遗留任务

必须验证：

- worker process handle 失效时，active task 被标记为 `failed/worker_lost`。
- 对应 kind 的固定 worker 可以重新启动。
- 其他两个 worker slot 不受影响。
- API 重启时遗留 `running/cancelling` task 被标记为 `failed/worker_lost`。
- worker 通过 control Pipe EOF 或 parent watchdog 退出。
- 临时目录在 worker 重启后被清理。
- 不依赖数据库保存或恢复操作系统进程信息。

## 7. Handler 测试边界

### EnhancementHandler

测试：

- traditional 参数映射到 `predict()`。
- deep model/checkpoint 参数映射到 `predict()`。
- 单图 PIL/NumPy 结果转换为 image artifact。
- 目录输入的 saved path 列表写入一个受管理输出目录。
- 输出目录固定由 WorkerContext 提供。
- handler 不写数据库。

### TrainingHandler

测试：

- 正常训练参数映射到 `llv.train()`。
- 请求存在 SwanLab 配置时走 BatchSwanLabTrainer adapter；没有配置时走 `llv.train()`。
- SwanLab 字段不会传给 `llv.train()`。
- 训练返回 history 和 checkpoint metadata。
- checkpoint 查找失败产生明确错误。
- KeyboardInterrupt/取消不会被错误转换成 succeeded。

### DatasetDownloadHandler

测试：

- repo ID 来自服务端创建的 job snapshot。
- 文件按顺序下载。
- 每个文件前检查本地 cancel event。
- 某个文件失败后不把数据集标记为 available。
- 重复下载符合 overwrite 策略。

## 8. Integration API 测试

集成测试把 FastAPI、临时 SQLite、临时 storage、fake supervisor 和 fake handler 组装起来，验证真实依赖方向：

```text
HTTP request
  -> route
  -> service
  -> SQLAlchemy
  -> fake WorkerSupervisor
  -> TaskEvent
  -> HTTP detail response
```

集成测试不使用真实 openLLV，但应覆盖完整的 HTTP 状态码和 JSON response shape。

推荐场景：

1. 上传图片并创建增强任务。
2. 查询 queued task。
3. fake worker 发布成功结果。
4. 查询 output directory artifact。
5. 创建训练任务并发布 checkpoint。
6. 创建下载任务并验证 dataset 状态。
7. 三种任务同时 queued，验证三个 slot 并行。
8. 一个 slot 失败，验证其他 slot 继续工作。

## 9. 数据迁移测试

迁移测试使用复制的 legacy SQLite 数据库，不修改真实 `data/app.db`。

必须验证：

- 三张旧 task 表的记录数量迁移正确。
- `success -> succeeded`。
- `stopped -> cancelled`。
- `running`、`pending` 等异常旧状态有明确映射。
- 旧 input/output/checkpoint 路径只在 managed root 内转换为 artifact。
- 找不到的文件产生 `artifact_missing` 标记，不静默丢弃记录。
- 迁移脚本重复执行不会重复创建 task。
- 迁移失败时事务或分批 checkpoint 行为明确。

## 10. 前端 API Contract 测试

前端测试不重复验证后端业务算法，重点验证：

- API client 正确解析统一错误结构。
- 非 JSON 错误响应不会导致解析异常泄露给用户。
- `AbortController` 能取消过期请求。
- task polling 在 succeeded/failed/cancelled 后停止。
- 页面切换不会用旧请求覆盖新 task。
- response 类型与 API 文档一致。

如果引入 OpenAPI client 生成，应把生成文件视为 contract artifact，并在后端 schema 变化时执行检查。

## 11. 禁止的测试依赖

默认测试禁止：

- 真实 GPU、MPS 或 CUDA。
- 真实 openLLV 模型权重。
- 真实 Hugging Face 网络下载。
- 真实 SwanLab API key 和远程项目。
- 真实 `data/app.db`。
- 真实生产 uploads、output、datasets 和 checkpoints。
- 依赖本机用户名、工作目录或 home cache。
- 通过 `uv run python app.py` 启动 Gradio 做冒烟测试。

## 12. 验收门槛

合并后端纵向切片前至少满足：

- schema、service、worker handler 单元测试通过。
- API happy path 和错误路径通过。
- 三个固定 slot 的并发边界通过。
- cancel、worker crash、recovery 测试通过。
- 数据库迁移测试通过。
- 测试输出不依赖真实外部服务。

真实设备验证、真实模型质量和长时间训练稳定性属于单独的手工或硬件 CI 流程，不作为普通单元测试的通过条件。
