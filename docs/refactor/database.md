# openLLV WebUI 数据库设计

> 状态：提案  
> ORM：SQLAlchemy 2.x  
> 数据库：首期 SQLite  
> 更新日期：2026-08-21

## 1. 设计目标

数据库负责保存任务的持久化事实和文件资源的索引，不负责保存运行中的 Python worker 对象。

必须满足：

- enhancement、training、dataset_download 使用统一任务生命周期。
- 三个固定 worker slot 可以独立并行，每个 kind 同时最多一个任务。
- API 重启后可以识别 queued、running、cancelling 任务。
- 取消和成功事件不会互相无条件覆盖。
- 输入、输出、checkpoint 和 dataset 使用受管理路径引用。
- 数据库不保存图片二进制和模型权重二进制。
- API response 不暴露绝对路径、worker traceback 和密钥。
- 旧的三张任务表可以迁移到新模型。

## 2. ORM 选择

继续使用 SQLAlchemy 2.x，不引入 SQLModel。

模型使用：

```python
class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
```

统一使用 `Mapped`、`mapped_column`、`select`、`update` 和每次操作独立 Session。ORM model 与 FastAPI/Pydantic schema 分离，不直接把数据库模型当作公共 API 契约。

## 3. 模型关系

```text
Task
|-- 0..1 EnhancementJob
|-- 0..1 TrainingJob
`-- 0..1 DatasetDownloadJob

Task --> Artifact           # 输入、输出、checkpoint 通过 ID 引用
TrainingJob --> Dataset
DatasetDownloadJob --> Dataset
```

使用组合关系，不使用 SQLAlchemy polymorphic inheritance。`tasks` 保存跨任务共享字段，详情表保存 kind 专属字段。

不采用以下两种结构：

- 一个包含所有 kind 字段并产生大量 NULL 的宽表。
- 一个只包含 `payload JSON` 和 `result JSON` 的无约束任务表。

JSON 适合算法参数、训练 history 和扩展 metadata；核心状态、外键和需要查询的字段使用明确列。

## 4. 枚举和值域

首期使用字符串值而不是数据库原生 enum，便于 SQLite 迁移和旧数据兼容。应用 schema 和数据库 CHECK 约束共同校验。

### 4.1 Task kind

```text
enhancement
training
```

### 4.2 Task status

```text
queued
running
cancelling
succeeded
failed
cancelled
```

合法状态迁移：

```text
queued -> running -> succeeded
                  -> failed
                  -> cancelling -> cancelled
queued -------------------------> cancelled
```

最终状态不可修改。服务层和 SQL 条件更新都必须检查旧状态。

### 4.3 Artifact kind

```text
image
output
checkpoint
dataset
```

单个文件和批量目录使用同一种 artifact 模型，差异由 `path_type` 表示，不再创建额外的聚合 artifact。

### 4.4 Storage kind

```text
uploads
output
datasets
checkpoints
tmp
```

`tmp` 只允许运行期记录，不允许作为最终 artifact 的公开 storage kind。

## 5. 表设计

### 5.1 `tasks`

所有异步任务的主表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | `String(36)` | PK | UUID 字符串 |
| `kind` | `String(32)` | NOT NULL | 任务类型 |
| `status` | `String(16)` | NOT NULL | 当前生命周期状态 |
| `message` | `String(512)` | NULL | 面向用户的状态文本 |
| `error_code` | `String(64)` | NULL | 稳定错误代码 |
| `error_detail` | `Text` | NULL | 已清理敏感信息的详情 |
| `created_at` | `DateTime` | NOT NULL | UTC 创建时间 |
| `started_at` | `DateTime` | NULL | 进入 running 的时间 |
| `finished_at` | `DateTime` | NULL | 进入最终状态的时间 |

### 5.2 `enhancement_jobs`

增强任务详情，一条 task 最多一条。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `task_id` | `String(36)` | PK, FK | 关联 `tasks.id` |
| `backend` | `String(16)` | NOT NULL | `traditional` 或 `deep` |
| `method` | `String(128)` | NOT NULL | catalog 方法名 |
| `input_artifact_id` | `String(36)` | FK | 输入图片文件或目录 |
| `checkpoint_artifact_id` | `String(36)` | NULL, FK | 自定义 checkpoint |
| `params` | `JSON` | NOT NULL | 已校验算法参数，默认 `{}` |
| `device` | `String(32)` | NOT NULL | 归一化后的设备名 |
| `output_artifact_id` | `String(36)` | NULL, FK | 单图文件或批量输出目录 |

约束：

- `backend=traditional` 时 checkpoint 必须为空。
- `backend=deep` 时 method 或 checkpoint 至少有一个有效选择。
- 单图和批量任务都只使用 `output_artifact_id`；artifact 的 `path_type` 区分文件和目录。

### 5.3 `training_jobs`

训练任务详情，一条 task 最多一条。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `task_id` | `String(36)` | PK, FK | 关联 `tasks.id` |
| `model` | `String(128)` | NOT NULL | catalog 模型名 |
| `dataset_id` | `String(36)` | NOT NULL, FK | 可用数据集 |
| `hyperparameters` | `JSON` | NOT NULL | epochs、batch_size、lr、resize 等 |
| `device` | `String(32)` | NOT NULL | 归一化设备 |
| `num_workers` | `Integer` | NOT NULL | 首期固定为 0 |
| `checkpoint_artifact_id` | `String(36)` | NULL, FK | 最终或中断 checkpoint |
| `history` | `JSON` | NULL | 训练 history |
| `best_val_loss` | `Float` | NULL | 最佳验证损失 |
| `swanlab_url` | `String(512)` | NULL | 成功初始化后的公开链接 |

禁止保存：

- SwanLab API key。
- SwanLab enabled 标志；是否启用由训练请求中是否存在 SwanLab 配置决定。
- SwanLab project 和 experiment；只保留最终公开 URL。
- 训练过程中的绝对 checkpoint 路径。
- 未清理的 Python exception traceback。

### 5.4 `dataset_download_jobs`

数据集下载任务详情，一条 task 最多一条。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `task_id` | `String(36)` | PK, FK | 关联 `tasks.id` |
| `dataset_id` | `String(36)` | NULL, FK | 下载目标 dataset，创建任务时可先创建 pending 记录 |
| `dataset_key` | `String(128)` | NOT NULL | 服务端配置 key 快照 |
| `repo_id` | `String(256)` | NOT NULL | 服务端配置中的 repo ID 快照 |
| `target_relative_path` | `String(512)` | NOT NULL | 相对于 datasets root |
| `file_count` | `Integer` | NULL | 成功下载文件数 |
| `downloaded_bytes` | `Integer` | NULL | 已下载字节数 |
| `overwrite` | `Boolean` | NOT NULL | 是否允许覆盖 |

客户端只能提交 `dataset_key`，不能直接提交任意 repo ID。repo ID 在创建任务时复制到 job，保证配置变化不影响历史任务语义。

### 5.5 `datasets`

受管理的数据集索引。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | `String(36)` | PK | dataset ID |
| `dataset_key` | `String(128)` | UNIQUE, NOT NULL | 配置或 UI 展示 key |
| `display_name` | `String(256)` | NOT NULL | 展示名 |
| `repo_id` | `String(256)` | NOT NULL | 来源 repo |
| `relative_path` | `String(512)` | NOT NULL | 相对于 datasets root |
| `status` | `String(32)` | NOT NULL | `downloading`、`available`、`failed` |
| `file_count` | `Integer` | NULL | 可用文件数量 |
| `total_bytes` | `Integer` | NULL | 总大小 |
| `error_code` | `String(64)` | NULL | 最近一次下载错误 |
| `created_at` | `DateTime` | NOT NULL | 创建时间 |
| `updated_at` | `DateTime` | NOT NULL | 更新时间 |

只有 `available` 状态的数据集可以创建训练任务。

### 5.6 `artifacts`

受管理文件或目录的索引。文件内容保存在 managed storage，表中只保存最小必要信息。单图、批量输入、批量输出和 checkpoint 目录都使用同一张表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | `String(36)` | PK | artifact ID |
| `kind` | `String(32)` | NOT NULL | `image`、`output`、`checkpoint`、`dataset` |
| `storage_kind` | `String(32)` | NOT NULL | uploads/output/checkpoints/datasets |
| `path_type` | `String(16)` | NOT NULL | `file` 或 `directory` |
| `relative_path` | `String(1024)` | NOT NULL | 相对于对应 root，可以指向文件或目录 |
| `display_name` | `String(256)` | NULL | 展示名称，不作为路径依据 |
| `task_id` | `String(36)` | NULL, FK | 产生该 artifact 的 task |
| `created_at` | `DateTime` | NOT NULL | 创建时间 |

`storage_kind + relative_path` 必须唯一。relative path 不能是绝对路径，不能包含解析后越出 managed root 的路径。

`path_type=file` 时 artifact 指向单个文件；`path_type=directory` 时指向一个受管理目录。目录内容由后端根据 artifact ID 列出或打包下载，不在数据库中创建额外的子 artifact 记录。

## 6. 索引和约束

### 6.1 任务领取索引

固定 worker 按 kind 领取队列，必须有：

```text
tasks(kind, status, created_at, id)
```

任务列表和状态筛选使用：

```text
tasks(status, created_at, id)
```

### 6.2 唯一和外键

- `datasets.dataset_key` 唯一。
- `artifacts.storage_kind + relative_path` 唯一。
- 每个 job detail 的 `task_id` 唯一。
- job detail 的 `task_id` 必须引用 `tasks.id`。
- 所有 artifact 外键必须引用存在的 artifact。
- 所有 training dataset 外键必须引用存在的 dataset。
- SQLite 开启 foreign keys。

### 6.3 状态 CHECK

数据库层至少限制：

```text
status IN ('queued', 'running', 'cancelling', 'succeeded', 'failed', 'cancelled')
kind IN ('enhancement', 'training', 'dataset_download')
```

复杂的状态迁移仍由 service 使用条件 `UPDATE` 处理，不能只依赖 CHECK。

## 7. 事务边界

### 7.1 创建任务

创建 API 请求在一个事务中完成：

1. 校验 method、artifact、dataset 和参数。
2. 创建 `tasks(status=queued)`。
3. 创建对应 detail row。
4. 提交事务。

任一步失败，task 和 detail 都回滚。

不要在数据库事务中启动 worker。提交成功后由 supervisor 领取，避免 worker 执行成功但 task 创建事务回滚。

### 7.2 领取任务

每个固定 slot 独立领取对应 kind：

1. 查询最早的 `queued` task。
2. 使用 `WHERE id = ? AND status = 'queued'` 更新为 `running`。
3. 写入 `started_at`。
4. 提交后发送 `TaskCommand`。

如果条件更新影响行数为 0，重新查询，不发送 command。

### 7.3 取消任务

queued 取消：

```text
UPDATE tasks
SET status = 'cancelled',
    finished_at = :now
WHERE id = :id AND status = 'queued'
```

running 取消：

```text
UPDATE tasks
SET status = 'cancelling'
WHERE id = :id AND status = 'running'
```

### 7.4 成功和失败

成功只允许从 running 提交：

```text
UPDATE tasks
SET status = 'succeeded',
    finished_at = :now
WHERE id = :id AND status = 'running'
```

失败只允许从 running 或 cancelling 提交，具体 error code 区分普通失败、取消失败和 worker 丢失。

如果成功事件提交前 task 已经是 cancelling，不能无条件覆盖为 succeeded；需要清理未发布结果并最终化为 cancelled。

结果 artifact 的创建和最终状态更新应在同一个数据库事务中完成，但文件本身应在事务前写入临时路径，并在事务成功后发布或保留可重试的 publish marker。

## 8. SQLite 配置

首期 SQLite 只允许一个 FastAPI server worker，但三个固定任务 worker 进程会并行运行，因此每个进程必须使用自己的 Session，不能继承或共享连接。

建议：

- 开启 `PRAGMA foreign_keys=ON`。
- 开启 WAL 模式。
- 设置合理的 `busy_timeout`。
- engine 每个进程创建一次。
- Session 每个请求、supervisor 操作或 worker 操作独立创建。
- 提交后关闭 Session，不跨线程和跨进程传递。

任务 handler 不直接写数据库；由 supervisor 接收 event 后写入。这样可以避免三个 worker 同时修改同一 task 的生命周期字段。

## 9. Storage 与数据库一致性

数据库和文件系统不是一个事务，因此使用发布协议：

1. worker 写入 `tmp/{task_id}/`。
2. 校验文件、大小和可选 sha256。
3. 原子 rename 到目标 managed root。
4. supervisor 在数据库事务中创建 artifact。
5. 条件更新 task 为 succeeded。

如果第 4 或第 5 步失败：

- 不把 task 标记为 succeeded。
- 保留或清理临时文件由 publish recovery 决定。
- 记录可重试的 publish error。
- 启动时扫描没有数据库引用的临时或孤立文件。

历史 artifact 不因单次 task 失败自动删除，避免破坏已经可查询的历史结果。

## 10. 旧数据库迁移

当前旧表：

```text
traditional_tasks
deep_learning_tasks
training_tasks
```

迁移规则：

| 旧表 | 新表 |
| --- | --- |
| `traditional_tasks` | `tasks` + `enhancement_jobs` |
| `deep_learning_tasks` | `tasks` + `enhancement_jobs` |
| `training_tasks` | `tasks` + `training_jobs` |

字段映射：

| 旧字段 | 新字段 |
| --- | --- |
| `id` | 新 task ID 或 legacy ID 映射表 |
| `status=success` | `succeeded` |
| `status=stopped` | `cancelled` |
| `error` | `tasks.error_detail` |
| `created_at` | `tasks.created_at` |
| `finish_at` | `tasks.finished_at` |
| `input_path` | input artifact 的相对路径 |
| `output_path` | output artifact 的相对路径 |
| `model_path` | checkpoint artifact 的相对路径 |
| 训练字段 | `training_jobs` 对应字段 |

迁移脚本必须：

- 迁移前备份数据库。
- 使用 migration marker，重复执行不重复创建记录。
- 不移动已有 output 和 checkpoint 文件。
- 只把 managed root 内的路径转换为 artifact。
- 找不到的文件记录 `artifact_missing`，不静默忽略。
- 输出迁移前后总数、各状态数量和失败记录。

## 11. Schema 迁移策略

开发环境可以用 `metadata.create_all()` 创建全新临时数据库，但生产和已有用户数据不能依赖它升级 schema。

正式实施时需要选择并确认迁移工具。当前项目未因本文自动添加新的迁移依赖；在依赖确认前，可以使用版本化的 `scripts/migrate_*.py` 脚本完成一次性迁移。

每次 schema 变更需要：

- 增加版本号。
- 提供升级步骤。
- 评估 SQLite 表重建需求。
- 更新迁移测试 fixture。
- 更新 API schema 和数据库文档。
- 提供失败恢复或备份方案。

## 12. 数据库测试边界

数据库测试规则详见 `docs/refactor/testing.md`，核心约束如下：

- 使用临时 SQLite，不使用真实 `data/app.db`。
- 每个测试使用独立 Session。
- 测试 foreign key、唯一约束、状态 CHECK 和 CAS 更新。
- 测试三个固定 worker slot 按 kind 领取任务。
- 测试取消与成功事件的竞争顺序。
- 测试 legacy 数据迁移的幂等性。
- 测试 artifact 路径不会越出 managed root。
