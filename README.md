# StockBI - 股票数据分析系统

一个基于Python的股票数据分析和可视化系统，提供实时行情、历史数据分析、技术指标计算等功能。

## 功能特性

### 📊 数据管理
- **股票列表管理**: 支持A股全市场股票数据同步
- **日线数据**: 支持日K、周K、月K线数据同步和展示
- **分时数据**: 支持分时行情数据同步和展示
- **实时行情**: 支持实时行情数据获取和展示

### 📈 技术分析
- **K线图表**: 日K、周K、月K线图表展示
- **技术指标**: 支持MA、MACD、KDJ、RSI、OBV等技术指标
- **分时图**: 分时走势图和实时行情曲线

### 🔍 数据筛选
- **股票搜索**: 支持代码、名称、拼音首字母搜索
- **板块筛选**: 按交易所、行业等维度筛选
- **自选股**: 支持自选股管理

### 📱 界面功能
- **仪表盘**: 数据概览、板块分布、同步状态
- **个股详情**: 详细行情数据和技术分析
- **数据同步**: 批量数据同步和进度监控

## 技术栈

### 后端
- **Python 3.11+**
- **FastAPI**: Web框架
- **SQLAlchemy**: ORM
- **PostgreSQL**: 数据库
- **Baostock**: 股票数据源
- **Akshare**: 实时行情数据源

### 前端
- **HTML/CSS/JavaScript**
- **Tailwind CSS**: 样式框架
- **ECharts**: 图表库
- **Chart.js**: 图表库

## 项目结构

```
stock/
├── macroquant/
│   └── backend/
│       ├── app/
│       │   ├── api/           # API路由
│       │   ├── core/          # 核心配置
│       │   ├── data_providers/ # 数据提供者
│       │   ├── models/        # 数据模型
│       │   ├── services/      # 业务服务
│       │   └── templates/     # HTML模板
│       ├── requirements.txt   # Python依赖
│       └── main.py           # 入口文件
└── README.md
```

## 安装部署

### 环境要求
- Python 3.11+
- PostgreSQL 14+

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/ceasarboy/stockBI.git
cd stockBI
```

2. 创建虚拟环境
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. 安装依赖
```bash
cd macroquant/backend
pip install -r requirements.txt
```

4. 配置数据库
```bash
# 创建PostgreSQL数据库
createdb stockdb

# 配置环境变量
set DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/stockdb
```

5. 启动服务
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

6. 访问系统
- 仪表盘: http://localhost:8000/ui/
- 股票列表: http://localhost:8000/ui/stocks
- API文档: http://localhost:8000/docs

## 使用说明

### 数据同步

1. **同步股票列表**
   - 进入数据同步页面
   - 点击"同步股票列表"

2. **同步日线数据**
   - 选择股票范围（全部/自选）
   - 选择时间范围（30天/1年/3年）
   - 点击"开始同步"

3. **同步分时数据**
   - 进入个股详情页
   - 点击"同步分时信息"

### 实时行情

1. 进入个股详情页
2. 点击"开启实时行情"
3. 系统会自动在交易时间内更新数据

### 技术分析

1. 进入个股详情页
2. 选择图表类型（日K/周K/月K/分时）
3. 选择技术指标（交易量/MACD/KDJ/RSI/OBV）

## API接口

### 股票数据
- `GET /api/v1/data/stocks` - 搜索股票列表
- `GET /api/v1/data/stock/{symbol}` - 获取股票详情
- `GET /api/v1/data/stock/{symbol}/daily` - 获取日线数据
- `GET /api/v1/data/stock/{symbol}/timeline` - 获取分时数据
- `GET /api/v1/data/realtime/{symbol}` - 获取实时行情

### 数据同步
- `POST /api/v1/data/sync/stock-list` - 同步股票列表
- `POST /api/v1/data/sync/batch-stocks-daily` - 批量同步日线数据
- `POST /api/v1/data/sync/stock-timeline/{symbol}` - 同步分时数据

### 统计数据
- `GET /api/v1/data/statistics` - 获取系统统计

## 数据源

### Baostock
- 股票列表
- 历史K线数据（日/周/月）
- 历史分钟线数据

### Akshare
- 实时行情数据
- 分时数据

## 板块分类

| 板块 | 代码规则 |
|------|---------|
| 上证主板 | 60xxxx |
| 科创板 | 688xxx |
| 深证主板 | 00xxxx |
| 创业板 | 300xxx, 301xxx |
| 北交所 | 920xxx, 8xxxxx |

## 交易时间

- 上午: 9:30 - 11:30
- 下午: 13:00 - 15:00

## 版本历史

### v1.0.0 (2026-02-24)
- 初始版本发布
- 支持股票数据同步和展示
- 支持实时行情和技术分析
- 支持自选股管理

## 许可证

MIT License

## 作者

ceasarboy

## 贡献

欢迎提交Issue和Pull Request！
