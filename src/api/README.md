# API 客户端

本模块封装 openLLV-server 的 HTTP 接口，负责传输配置、路径与查询参数编码、响应解包和响应归一化。业务状态和页面交互不应放在这里。

## 模块结构

- `http.ts`：共享 Axios 实例，使用 `/api/v1` 作为 `baseURL`。
- `artifacts.ts`：图片上传、Artifact 元数据和文件或目录内容读取。
- `enhancement.ts`：增强能力目录和增强任务提交。
- `training.ts`：训练能力目录、可用数据集、任务提交和任务详情。
- `datasets.ts`：数据集目录、下载任务和已管理数据集列表。
- `tasks.ts`：通用任务列表、详情、取消和 Artifact 浏览器地址。

接口契约以 [后端 API 文档](../../docs/README.md) 为准，前端类型位于 `@/types`。

## 约定

- 端点模块必须复用 `@/api/http`，不要直接创建新的 Axios 实例。
- API 函数返回解包后的 `data`，不向调用方暴露 `AxiosResponse`。
- 可取消请求接收可选的 `AbortSignal`，调用方负责请求替换和组件卸载时取消。
- 路径中的外部 ID 必须使用 `encodeURIComponent`。
- 请求和响应字段保留服务端的 snake_case 命名，不在传输层转换字段名。
- 新增或修改端点时，同步更新 `src/types/` 中的请求和响应类型。
