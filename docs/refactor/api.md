# openLLV WebUI 后端 API

> 状态：提案  
> 适用架构：FastAPI + 三个固定 worker slot  
> 更新日期：2026-08-21

## 1. API 约定

API 是前端 Vue 与后端服务之间的唯一业务边界。前端不读取 SQLite，不访问服务器文件路径，也不直接调用 openLLV。

基础 URL：

```text
/api/v1
```

所有业务 ID 使用 UUID 字符串。所有时间使用 UTC ISO 8601，例如：

```text
2026-08-21T08:00:00Z
```

后端固定维护三个 worker slot：

| kind | worker | 并发规则 |
| --- | --- | --- |
| `enhancement` | Enhancement Worker | 同时最多一个增强任务 |
| `training` | Training Worker | 同时最多一个训练任务 |
| `dataset_download` | Download Worker | 同时最多一个下载任务 |

三个 slot 可以并行；同一个 kind 的任务按创建顺序排队。

## 2. 通用响应

### 2.1 成功响应

资源创建返回 `201 Created`，异步任务创建返回 `202 Accepted`，查询返回 `200 OK`。

异步任务创建的最小响应：

```json
{
  "id": "5c4f1d53-4e88-4e34-9a1d-f7f4b8f95d2e",
  "kind": "enhancement",
  "status": "queued",
  "created_at": "2026-08-21T08:00:00Z"
}
```

### 2.2 错误响应

所有业务错误使用统一结构：

```json
{
  "error": {
    "code": "artifact_not_found",
    "message": "Input artifact does not exist",
    "details": null,
    "request_id": "req-01H..."
  }
}
```

`details` 只返回可展示的字段，不返回 traceback、绝对路径、环境变量或 API key。

常用错误码：

| HTTP | code | 说明 |
| --- | --- | --- |
| 400 | `invalid_request` | 请求结构或业务参数无效 |
| 400 | `invalid_transition` | 任务状态不允许当前操作 |
| 404 | `task_not_found` | 任务不存在 |
| 404 | `artifact_not_found` | artifact 不存在或已不可用 |
| 404 | `dataset_not_found` | 数据集不存在 |
| 409 | `worker_busy` | 仅用于不允许排队的操作；普通任务创建不使用此错误 |
| 409 | `duplicate_artifact` | 文件或资源已存在且不能覆盖 |
| 409 | `unsupported_method` | openLLV 不支持该算法或模型 |
| 409 | `worker_unavailable` | 对应固定 worker 当前不可用 |
| 413 | `file_too_large` | 上传文件超过服务端限制 |
| 415 | `unsupported_media_type` | 文件类型不支持 |
| 422 | `validation_error` | Pydantic 请求校验失败 |
| 500 | `internal_error` | 未分类服务错误 |
| 503 | `service_not_ready` | 数据库、storage 或 worker 未就绪 |

FastAPI 默认的校验错误也转换为统一格式：

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": {
      "fields": [
        {
          "path": "body.epochs",
          "message": "Input should be greater than 0"
        }
      ]
    },
    "request_id": "req-01H..."
  }
}
```

## 3. Health API

### `GET /health/live`

只判断 API 进程是否存活，不访问外部服务。

成功响应：

```json
{
  "status": "ok"
}
```

### `GET /health/ready`

检查：

- SQLite 是否可连接。
- managed storage 目录是否可读写。
- 三个固定 worker slot 是否已启动或处于可恢复状态。
- 当前服务是否正在关闭。

成功响应：

```json
{
  "status": "ready",
  "workers": {
    "enhancement": "idle",
    "training": "running",
    "dataset_download": "idle"
  }
}
```

如果 supervisor 尚未启动或数据库不可用，返回 `503 service_not_ready`。

## 4. Catalog API

### `GET /api/v1/catalog`

返回前端构建下拉框和表单所需的受支持能力。catalog 是展示和请求校验的来源，前端不能自行硬编码方法名称。

响应：

```json
{
  "algorithms": [
    {
      "name": "Gamma",
      "aliases": ["gamma"]
    }
  ],
  "models": [
    {
      "name": "ZeroDCE",
      "aliases": ["zero_dce"]
    }
  ],
  "datasets": [
    {
      "name": "CommonDataset",
      "aliases": []
    }
  ],
  "devices": ["auto", "cpu", "mps", "cuda:0"],
  "forms": {
    "enhancement": {
      "traditional_params": {
        "gamma": {
          "type": "number",
          "minimum": 0,
          "default": 0.6
        }
      }
    },
    "training": {
      "epochs": {"type": "integer", "minimum": 1},
      "batch_size": {"type": "integer", "minimum": 1},
      "lr": {"type": "number", "exclusiveMinimum": 0}
    }
  }
}
```

`llv.list_available()` 只提供名称和 aliases。参数范围、默认值和可展示 schema 由后端显式维护，不通过反射任意暴露 Python 签名。

## 5. Artifact API

### `POST /api/v1/artifacts/images`

以 `multipart/form-data` 上传一张或多张图片。

请求字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `files` | file[] | 图片文件，受服务端数量和大小限制 |

响应：

```json
{
  "id": "b9b5...",
  "kind": "image",
  "path_type": "file",
  "display_name": "input.jpg",
  "content_url": "/api/v1/artifacts/b9b5.../content"
}
```

单文件上传创建一个 `path_type=file` 的 artifact。多文件上传将文件写入服务端生成的目录，并创建一个 `path_type=directory` 的 artifact。单文件和批量输入使用同一种 artifact，客户端永远不提交服务器目录路径。

后端必须：

- 校验 MIME、文件扩展名和图片内容。
- 为文件生成服务端文件名，不能信任客户端文件名作为路径。
- 写入 `uploads` 根目录下的临时文件，完成后原子发布。
- 记录 artifact 类型、路径类型和相对路径。
- 拒绝路径穿越、符号链接越界和超过大小限制的请求。

### `GET /api/v1/artifacts/{artifact_id}`

返回 artifact 元数据，不返回服务器绝对路径。

### `GET /api/v1/artifacts/{artifact_id}/content`

下载或预览 artifact。后端根据数据库中的 `storage_kind + relative_path` 解析路径，并再次检查路径位于允许的 managed root 内。`path_type=file` 返回文件内容；`path_type=directory` 返回目录列表或按需打包的下载内容。

## 6. Enhancement API

### `POST /api/v1/enhancements`

创建增强任务，立即返回 `202 Accepted`。

请求：

```json
{
  "backend": "traditional",
  "method": "Gamma",
  "input_artifact_id": "b9b5...",
  "checkpoint_artifact_id": null,
  "params": {
    "gamma": 0.6
  },
  "device": "auto"
}
```

字段规则：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `backend` | 是 | `traditional` 或 `deep` |
| `method` | 是 | 来自 catalog 的算法或模型名称 |
| `input_artifact_id` | 是 | image 文件或目录 artifact |
| `checkpoint_artifact_id` | 否 | 深度模型 checkpoint artifact |
| `params` | 否 | 已按 backend/method 校验的参数对象 |
| `device` | 否 | 默认 `auto`，只能使用 catalog 中的值 |

服务端校验：

- `traditional` 不接受深度模型 checkpoint。
- `deep` 的 method 必须是已注册模型或受管理 checkpoint。
- 参数必须是对象，未知参数按方法策略拒绝或明确忽略并记录 warning。
- 输入 artifact 必须存在且路径可用。

任务详情中的增强结果统一使用 `output_artifact_id`。单图任务的 artifact 是文件，批量任务的 artifact 是包含所有输出文件的目录。

## 7. Dataset API

### `GET /api/v1/datasets`

列出已管理的数据集，不返回任意本机目录。

查询参数：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `page` | `1` | 从 1 开始 |
| `page_size` | `20` | 最大 100 |
| `status` | 无 | `downloading`、`available`、`failed` |

### `POST /api/v1/datasets/downloads`

创建数据集下载任务。

请求：

```json
{
  "dataset_key": "LOLv1",
  "overwrite": false
}
```

`dataset_key` 必须来自服务端配置的允许下载列表，例如：

```yaml
datasets:
  downloads:
    LOLv1: bainianzzz/lolv1
```

客户端不能直接提交任意 Hugging Face `repo_id`。服务端把配置中的 repo ID 复制到 job 快照中，避免配置变化导致历史任务语义改变。

## 8. Training API

### `POST /api/v1/trainings`

创建训练任务，返回 `202 Accepted`。

请求：

```json
{
  "model": "ZeroDCE",
  "dataset_id": "d3c1...",
  "epochs": 20,
  "batch_size": 8,
  "lr": 0.0001,
  "resize": 256,
  "device": "auto",
  "swanlab": {
    "project": "openLLV",
    "experiment": "zero-dce-demo"
  }
}
```

字段规则：

| 字段 | 规则 |
| --- | --- |
| `model` | 必须是 catalog 中的模型名 |
| `dataset_id` | 必须是 `available` 状态的数据集 |
| `epochs` | 正整数 |
| `batch_size` | 正整数 |
| `lr` | 大于 0 |
| `resize` | 正整数或受支持的尺寸数组 |
| `device` | `auto`、`cpu`、`mps` 或受服务端允许的 CUDA 设备 |
| `swanlab` | 可选；存在时启用监控 |
| `swanlab.project` | 非敏感项目名 |
| `swanlab.experiment` | 非敏感实验名 |

SwanLab API key 不允许出现在请求中。后端从环境变量或受保护配置读取，并在 worker 子进程中使用。请求中没有 `swanlab` 配置时不启用监控。

训练完成后返回：

```json
{
  "task": {
    "id": "5c4f...",
    "kind": "training",
    "status": "succeeded"
  },
  "training": {
    "checkpoint_artifact_id": "c8a1...",
    "history": [],
    "best_val_loss": 0.031,
    "swanlab_url": "https://swanlab.cn/..."
  }
}
```

## 9. Task API

### `GET /api/v1/tasks`

查询所有任务。

查询参数：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `page` | `1` | 从 1 开始 |
| `page_size` | `20` | 最大 100 |
| `kind` | 无 | 任务类型 |
| `status` | 无 | 任务状态 |
| `created_after` | 无 | UTC 时间 |
| `created_before` | 无 | UTC 时间 |

默认按 `created_at DESC, id DESC` 排序，保证分页稳定。

响应：

```json
{
  "items": [
    {
      "id": "5c4f...",
      "kind": "enhancement",
      "status": "running",
      "message": "Enhancement is running",
      "created_at": "2026-08-21T08:00:00Z",
      "started_at": "2026-08-21T08:00:01Z",
      "finished_at": null
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### `GET /api/v1/tasks/{task_id}`

返回通用 task、对应的 job 详情、artifact 引用和错误信息。

状态字段：

```text
queued -> running -> succeeded
                  -> failed
                  -> cancelling -> cancelled
queued -------------------------> cancelled
```

### `POST /api/v1/tasks/{task_id}/cancel`

请求体为空，取消操作幂等。

行为：

- `queued` 直接变成 `cancelled`，不会启动 worker。
- `running` 变成 `cancelling`，由对应固定 worker 处理取消。
- `cancelling` 返回当前 task，不重复发送终止信号。
- `succeeded`、`failed`、`cancelled` 返回当前最终状态。

取消 endpoint 只确认取消请求，不等待进程退出。前端继续查询 task，直到进入最终状态。

成功响应：

```json
{
  "id": "5c4f...",
  "kind": "training",
  "status": "cancelling"
}
```

成功事件与取消请求之间使用数据库 compare-and-set 决定先后：成功提交先发生时保留 `succeeded`；取消先发生时，后到的成功结果不能覆盖 `cancelling`。

## 10. 前端调用边界

页面与 API 的对应关系：

| 页面 | API |
| --- | --- |
| Enhance | catalog、artifacts、enhancements、tasks |
| Training | catalog、datasets、trainings、tasks |
| Datasets | catalog、datasets、dataset downloads、tasks |
| Tasks | tasks、artifacts |
| Task Detail | task detail、cancel、artifact content |

前端规则：

- 所有请求通过 `frontend/src/api/client.ts`。
- feature 的 `api.ts` 只封装 endpoint，不拼接业务 URL。
- 活跃任务使用 REST 轮询，最终状态后停止轮询。
- 请求切换或页面卸载时使用 `AbortController`。
- 前端不保存 SwanLab API key。
- 前端不展示服务器绝对路径。

## 11. 版本与兼容

- 新增字段优先保持可选，避免破坏旧前端。
- 删除字段或修改状态语义需要增加 API 版本或迁移窗口。
- `kind`、`status`、artifact `kind` 属于公共枚举，修改前要同步更新后端 schema、前端类型和测试。
- API 文档中的示例只使用 mock ID，不使用真实数据库或文件路径。
