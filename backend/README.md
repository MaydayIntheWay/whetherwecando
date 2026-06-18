# Idea可行性验证工具 - 后端服务

## 环境要求

- Python >= 3.10
- uv 包管理器

## 安装依赖

```bash
uv pip install -e .
```

## 开发依赖

```bash
uv pip install -e ".[dev]"
```

## 运行服务

```bash
uvicorn main:app --reload --port 8000
```
