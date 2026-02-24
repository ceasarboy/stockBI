# MacroQuant 需求分析文档

## 1. 需求概述
MacroQuant 是一款个人量化与投资辅助系统，旨在打造个人投资逻辑知识库。

## 2. 技术需求

### 2.1 后端技术栈
- Python 3.11+
- FastAPI（异步、高性能）
- SQLAlchemy 2.0+（ORM）
- PostgreSQL（关系型数据库）
- Redis（缓存和状态管理）

### 2.2 数据源
- **A股日线数据**：
  - AkShare（主数据源）
  - Baostock（备用数据源，解决 AkShare 拉取困难问题）
- **全球宏观数据**：yfinance（Yahoo Finance）或 TradingView Webhook

### 2.3 UI/UX 设计
- 使用 `ui-ux-pro-max` 技能进行 UI/UX 设计
- 风格：Bloomberg Terminal 极简暗色调（Dark Mode）
- 原则：高信噪比，拒绝花哨动画，强调专业感
- 技术栈：Flutter / React Native（移动端）

### 2.4 部署
- Docker 容器化
- 云服务器部署

## 3. 功能需求分解

### 3.1 权限系统 (Auth & Roles)
| ID | 需求描述 | 优先级 | 测试要求 |
|----|----------|--------|----------|
| AUTH-001 | JWT 用户登录认证 | 高 | 验证 token 生成和验证 |
| AUTH-002 | 角色区分（管理员/普通用户） | 高 | 验证权限控制 |
| AUTH-003 | 用户注册功能 | 中 | 验证用户创建流程 |

### 3.2 行情引擎 (Market Data Engine)
| ID | 需求描述 | 优先级 | 测试要求 |
|----|----------|--------|----------|
| MARKET-001 | A 股日线数据自动拉取（收盘后） | 高 | 验证 AkShare/Baostock 数据获取 |
| MARKET-002 | 全球宏观数据获取（实时/延时） | 高 | 验证 yfinance 数据获取 |
| MARKET-003 | 数据存储到 PostgreSQL | 高 | 验证数据持久化 |
| MARKET-004 | 数据源切换（AkShare ↔ Baostock） | 高 | 验证故障转移机制 |

### 3.3 实时报警系统 (Real-time Alert System)
| ID | 需求描述 | 优先级 | 测试要求 |
|----|----------|--------|----------|
| ALERT-001 | TradingView Webhook 接收 | 高 | 验证 Webhook 接口 |
| ALERT-002 | 报警规则设置（价格、涨跌幅等） | 高 | 验证规则创建和存储 |
| ALERT-003 | 报警推送（Server酱/Telegram/企业微信） | 高 | 验证推送功能 |
| ALERT-004 | 报警历史记录 | 中 | 验证日志存储 |

### 3.4 资讯与影响追踪 (News & Impact Tracker) - 核心模块
| ID | 需求描述 | 优先级 | 测试要求 |
|----|----------|--------|----------|
| NEWS-001 | 资讯分类管理 | 高 | 验证分类 CRUD |
| NEWS-002 | 资讯录入（标题、内容、来源、发布时间） | 高 | 验证资讯创建 |
| NEWS-003 | 影响预判录入（目标标的、影响评分、发酵周期、逻辑备注） | 高 | 验证预判功能 |
| NEWS-004 | 事后复盘（实际影响、复盘笔记、预判状态） | 高 | 验证复盘功能 |
| NEWS-005 | 资讯与 A 股日线表现关联 | 中 | 验证数据关联 |

### 3.5 因子选股模块 (Factor-based Stock Selection) - 新增核心模块
| ID | 需求描述 | 优先级 | 测试要求 |
|----|----------|--------|----------|
| FACTOR-001 | 估值因子计算（PE、PB、PS、PCF） | 高 | 验证因子计算准确性 |
| FACTOR-002 | 动量与技术因子计算（Return_N、RSI、MACD、波动率、换手率） | 高 | 验证因子计算准确性 |
| FACTOR-003 | 质量因子计算（ROE、ROA、GPM、总资产周转率、资产负债率） | 高 | 验证因子计算准确性 |
| FACTOR-004 | 成长因子计算（净利润增长、营收增长、营业利润增长、可持续增长率） | 高 | 验证因子计算准确性 |
| FACTOR-005 | 流动性与市值因子计算（市值、流动性） | 高 | 验证因子计算准确性 |
| FACTOR-006 | 宏观联动因子计算（原油相关性、黄金相关性、汇率敏感度、利率 Beta） | 高 | 验证因子计算准确性 |
| FACTOR-007 | 情绪与资讯因子计算（资讯情绪分、分析师评级、资金流向） | 高 | 验证因子计算准确性 |
| FACTOR-008 | 因子组合有效性分析 | 高 | 验证回测结果 |
| FACTOR-009 | 因子选股回测 | 高 | 验证策略表现 |

### 3.6 策略模块 (Strategy)
| ID | 需求描述 | 优先级 | 测试要求 |
|----|----------|--------|----------|
| STRATEGY-001 | 策略代码编辑和保存 | 中 | 验证策略存储 |
| STRATEGY-002 | 策略回测功能 | 中 | 验证回测执行 |

## 4. 因子详细说明

### 4.1 估值因子家族 (Value Factors)
- **PE**：市盈率，股价 / 每股收益（使用 EP 盈利收益率参与计算）
- **PB**：市净率，股价 / 每股净资产（使用 BP 账面价值廉价程度）
- **PS**：市销率，股价 / 每股营业收入
- **PCF**：市现率，股价 / 每股经营现金流

### 4.2 动量与技术因子家族 (Momentum & Technical Factors)
- **Return_N**：N 日区间收益率（20 日、60 日、120 日）
- **RSI**：相对强弱指数，衡量买卖力量对比
- **MACD**：平滑异同移动平均线
- **Volatility**：波动率（过去 N 日收益率标准差）
- **Turnover Rate**：换手率，衡量交易活跃度

### 4.3 质量因子家族 (Quality Factors)
- **ROE**：净资产收益率，净利润 / 股东权益
- **ROA**：总资产收益率
- **GPM**：毛利率
- **Asset Turnover**：总资产周转率
- **Debt-to-Asset Ratio**：资产负债率

### 4.4 成长因子家族 (Growth Factors)
- **Net Profit Growth**：净利润同比增长率
- **Revenue Growth**：营业收入同比增长率
- **Operating Profit Growth**：营业利润增速
- **Sustainable Growth Rate**：可持续增长率

### 4.5 流动性与市值因子家族 (Liquidity & Size Factors)
- **Market Cap**：市值因子
- **Liquidity**：流动性因子（过去一月成交额、成交量）

### 4.6 宏观联动因子 (Macro Correlation Factors) - 特色需求
- **Oil Correlation**：个股与布伦特原油价格的相关系数
- **Gold Correlation**：与 COMEX 黄金的相关性
- **Currency Sensitivity**：对人民币汇率（USD/CNH）波动的敏感度
- **Interest Rate Beta**：对美债 10 年期收益率变化的反应系数

### 4.7 情绪与资讯因子 (Alternative & Sentiment Factors) - 特色需求
- **News Sentiment**：资讯情绪分（基于录入的逻辑 -5 到 +5）
- **Analyst Rating**：分析师评级调整
- **Institutional Flow**：北向资金流、主力资金流向

## 5. 非功能需求
| ID | 需求描述 | 优先级 |
|----|----------|--------|
| NFR-001 | 代码严格类型提示 | 高 |
| NFR-002 | 详细 Docstring | 高 |
| NFR-003 | 模块解耦 | 高 |
| NFR-004 | 高信噪比 UI（暗色调） | 中 |
| NFR-005 | 数据源故障转移机制 | 高 |

## 6. 今日开发目标
完成数据库连接层的集成，实现 NEWS-001 到 NEWS-005 的基础功能。
