# 基于 RAG 的多模态电商智能导购 Agent

本项目是一个完全本地运行的服装/穿搭导购 Demo。它使用 H&M 公开商品图文数据，支持文本检索、图片检索、图文融合检索、轻量 LangChain Agent、多轮偏好、商品对比、购物车和模拟下单。

## 当前数据规模

- 官方 ZIP：`D:\datasets\hm_raw\h-and-m-personalized-fashion-recommendations.zip`
- 本地样本：5,000 条商品和 5,000 张图片
- 原始 ZIP 不进入 Git，不做全量解压
- 后续模块只读取 `backend/data/sample/` 中的样本数据

## 环境要求

- Windows 10/11
- Python 3.12
- Node.js 20
- 首次构建模型索引时需要访问 Hugging Face；模型缓存后可离线运行

## 1. 安装后端依赖

```powershell
cd D:\Desktop\bytedance
python -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

## 2. 数据工程

已完成抽样时无需重复执行第一条命令。

```powershell
python backend\scripts\sample_dataset.py `
  --zip_path D:\datasets\hm_raw\h-and-m-personalized-fashion-recommendations.zip `
  --out_dir backend\data\sample `
  --sample_size 5000

python backend\scripts\inspect_data.py
python backend\scripts\clean_articles.py
python backend\scripts\build_product_profiles.py
python backend\scripts\build_sqlite.py
```

验证：

```powershell
(Import-Csv backend\data\sample\product_profiles.csv).Count
python -c "import sqlite3; c=sqlite3.connect(r'backend/data/sqlite/app.db'); print(c.execute('select count(*) from products').fetchone()[0])"
```

两条命令都应输出 `5000`。

## 3. 构建向量索引

```powershell
python backend\scripts\build_text_index.py `
  --input_csv backend\data\sample\product_profiles.csv `
  --index_dir backend\data\vector_store\text `
  --backend sentence-transformers `
  --force

python backend\scripts\build_image_index.py `
  --input_csv backend\data\sample\product_profiles.csv `
  --index_dir backend\data\vector_store\image `
  --backend transformers-clip `
  --device cpu `
  --force
```

## 4. 启动后端

当前机器的 8000 端口被其他应用占用，因此示例使用 18000。

```powershell
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 18000
```

接口文档：<http://127.0.0.1:18000/docs>

健康检查：

```powershell
curl.exe http://127.0.0.1:18000/health
```

## 5. 启动前端

新开一个 PowerShell：

```powershell
cd D:\Desktop\bytedance\frontend
npm install
npm run dev
```

访问：<http://127.0.0.1:5173>

## 6. 可选 LLM 配置

不配置 LLM 时，Agent 使用确定性的真实商品推荐理由，其他功能仍可运行。使用 OpenAI-compatible API 时设置：

```powershell
$env:LLM_BASE_URL="https://api.example.com/v1"
$env:LLM_API_KEY="your-api-key"
$env:LLM_MODEL="your-model-name"
```

LLM 只接收检索候选商品，商品卡片由真实目录生成；模型返回的非候选商品 ID 会被丢弃。

## 7. 测试

```powershell
python -m pytest backend\tests -q

python backend\scripts\validate_real_retrieval.py `
  --sample_csv backend\data\sample\product_profiles.csv `
  --text_index_dir backend\data\vector_store\text `
  --image_index_dir backend\data\vector_store\image `
  --report_path backend\data\vector_store\integration_report.json `
  --device cpu

cd frontend
npm run build
```

## 主要接口

- `GET /api/products`
- `GET /api/products/{article_id}`
- `POST /api/search/text`
- `POST /api/search/image`
- `POST /api/search/hybrid`
- `POST /api/chat`
- `POST /api/chat/stream`
- `POST /api/compare`
- `POST /api/cart/add`
- `POST /api/cart/remove`
- `POST /api/checkout`

## 数据与 Git 安全

`.gitignore` 已忽略原始 ZIP、样本图片、SQLite、向量索引、环境变量、Python 虚拟环境、Node 依赖和构建产物。不要提交 `kaggle.json`。
