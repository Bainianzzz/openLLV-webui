## 项目开发规则

- 不得自行添加任何新依赖，若要添加请向用户报告，python 环境使用 uv 管理
- 当在同一个子包内部的模块之间相互引用时，使用显式相对路径；当一个子包需要引用另一个子包的内容时，必须使用基于项目根包的绝对路径。
- 不要直接阅读 openLLV 项目的源码，通过 `$openllv` 这个技能了解 openLLV 的使用方法
- 信任 gradio 提供的参数以及 openLLV 的返回值，不要添加冗余的校验逻辑和测试
- 不得更新 `pyproject.toml`，如要更新请跟用户报告
- 不要自行启动 `gradio` 运行冒烟测试，直接告知用户最简要的测试点
- **不要编写任何临时测试代码/脚本进行测试、验证**，仅通过静态语法检查以及针对修改运行个别测试文件即可。如果缺少测试，告知用户

## webui 技术栈

- gradio
- openLLV
- sqlalchemy
- pytest

## webui 项目结构

- `inference` webui 服务方法
  - `model`: SQLAlchemy 模型定义
  - `utils` 工具函数
  - `<domain>`: 各领域模块业务方法；公共入口放包 `__init__.py`，跨单张/批量复用的共享实现放同名字模块（如 `enhance/enhance.py` 的 `_enhance`）
- `ui` webui 界面，每个包的 **init**.py 负责组装页面组件，直接引用 `interface` 包中的方法，不能引用其子包的方法
  - `ui/<domain>` : 各业务邻域的子组件模块
  - `ui/components`: 通用可复用组件
- `test` : webui 测试用例，不要擅自更新，测试文件/测试函数命名必须以 `test_` 开头，图片、数据库操作均为 mock data
  - 涉及数据库操作，使用 `test/mock` 中导出的 `mock_**` 上下文管理器
  - 涉及图片，使用 `test/mock` 导出的 `TEST_IMAGE`（`test/assets/` 下的共享测试照片路径）
  - `test/performance`: 性能相关测试
