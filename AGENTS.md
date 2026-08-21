## 项目开发规则（必须遵守）

- 不得自行添加任何新依赖，若要添加请向用户报告，python 环境使用 uv 管理
- 当在同一个子包内部的模块之间相互引用时，使用显式相对路径；当一个子包需要引用另一个子包的内容时，必须使用基于项目根包的绝对路径。
- 不要直接阅读 openLLV 项目的源码，通过 `$openllv` 这个技能了解 openLLV 的使用方法
- 不得更新 `pyproject.toml`，如要更新请跟用户报告
- 不要自行启动服务做长时间训练或推理冒烟测试
- 禁止使用可变默认参数
- 修改公共接口签名时，同步更新所有调用点与相关包的导出
- 修改后运行 pytest，只跑受影响接口关联的测试文件，尽量不跑全量测试

## backend 技术栈

- fastapi
- openLLV
- sqlalchemy
- pytest
- swanlab
- uv

## 项目结构

- `config.yaml` 全局配置：数据库、managed storage、数据集和 SwanLab 设置
- `backend` FastAPI 后端包
  - `api`: 路由、错误处理、artifact storage 和服务依赖
  - `db`: SQLAlchemy 2.x 模型和 session
  - `schemas`: API 请求/响应 schema
  - `workers`: 三个固定 worker slot、协议和任务 handler
- `test`: 后端测试，测试文件/测试函数命名必须以 `test_` 开头；数据库和文件均使用临时/mock data
- `docs/refactor`: 重构后的架构、API、worker、数据库和测试边界文档
