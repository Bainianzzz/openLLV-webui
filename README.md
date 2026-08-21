# openLLV WebUI

FastAPI backend for controlling openLLV enhancement, training, and dataset workers.

## 快速开始

```bash
# 1. 安装依赖（Python 环境与依赖由 uv 统一管理）
uv sync

# 2. 准备配置文件
cp example.config.yaml config.yaml

# 3. 启动后端
uv run fastapi dev backend/main.py
```

## 提交前检查

启用版本库中的 Git hook：

```bash
git config core.hooksPath .githooks
```

提交涉及后端代码、测试或 Python 依赖时，会自动执行 `uv run pytest -q`。
