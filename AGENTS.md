## 项目开发规则

- 不得自行添加任何新依赖，若要添加请向用户报告，python 环境使用 uv 管理
- 同一个包下的用相对路径，不同包的一律用基于项目根目录的绝对路径
- 不要直接阅读 openLLV 项目的源码，通过 `$openllv` 这个技能了解 openLLV 的使用方法
- 信任 gradio 提供的参数以及 openLLV 的返回值，不要添加冗余的校验逻辑和测试
- 不得更新 `pyproject.toml`，如要更新请跟用户报告
- 不要自行启动 `gradio` 运行冒烟测试，直接告知用户最简要的测试点

## webui 技术栈

- gradio
- openLLV
- sqlalchemy
- pytest

## webui 项目结构

- `inference` webui 服务方法
  - `model`：SQLAlchemy 模型定义
  - `utils` 工具函数
- `ui` webui 界面，每个包的 **init**.py 负责组装页面组件
  - `ui/<domain>` : 各业务邻域的子组件模块
- `test` : webui 测试用例，不要擅自更新，测试文件/测试函数命名必须以 `test_` 开头，图片、数据库操作均为 mock data
  - 涉及数据库操作，使用 `test/mock/db.py` 中 `mock_db` 上下文管理器
