## 项目开发规则（必须遵守）

- 不得自行添加任何新依赖，若要添加请向用户报告，python 环境使用 uv 管理
- 当在同一个子包内部的模块之间相互引用时，使用显式相对路径；当一个子包需要引用另一个子包的内容时，必须使用基于项目根包的绝对路径。
- 不要直接阅读 openLLV 项目的源码，通过 `$openllv` 这个技能了解 openLLV 的使用方法
- 不得更新 `pyproject.toml`，如要更新请跟用户报告
- 不要自行启动 `gradio` 运行冒烟测试
- 禁止使用可变默认参数
- 修改公共接口签名时，同步更新所有调用点与 `__all__`、`inference/__init__.py` 的导出
- 修改后运行 pytest，只跑受影响接口关联的测试文件，尽量不跑全量测试

## webui 技术栈

- gradio
- openLLV
- sqlalchemy
- pytest
- swanlab

## webui 项目结构

- `config.yaml` 全局配置：数据库路径、输出/数据集目录、SwanLab 设置
- `inference` webui 服务方法，包入口初始化数据库会话（`SessionLocal`）并统一导出各领域公共入口
  - `model`: SQLAlchemy 模型定义（`TraditionalTask`/`DeepLearningTask`/`TrainingTask`）
  - `utils`: 工具函数（配置读取、图片处理、后台线程、SwanLab 链接解析）
  - `enhance`: 增强业务（单张/批量共享实现、记录查询）
  - `train`: 训练业务（训练执行、数据集下载、SwanLab 监控、记录查询）
- `ui` webui 界面，每个子包负责组装页面组件，直接引用 `inference` 包的方法，不能引用其子包的方法
  - `components`: 通用可复用组件（HTML 记录表格）
  - `enhance`: 增强页面（传统算法/深度学习/记录浏览）
  - `train`: 训练页面（数据集下载与选择/训练/记录浏览/SwanLab 扩展）
- `test` : webui 测试用例，需要更新或添加测试时先报告用户、同意后再更新；测试文件/测试函数命名必须以 `test_` 开头，图片、数据库操作均为 mock data
  - 涉及数据库操作，使用 `test/mock` 中导出的 `mock_**` 上下文管理器
