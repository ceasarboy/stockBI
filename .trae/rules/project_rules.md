## ACP 每日开发流程
1. **架构师角色**：分析需求、更新需求、分解需求、确定测试要求
2. **项目经理角色**：项目进度管理、跟踪和更新项目进度
3. **开发人员角色**：审视架构和需求、编制软件、提交代码审查和测试
4. **代码审查人员角色**：审查语法错误和常见错误
5. **测试人员角色**：编制测试用例和测试大纲、执行测试
6. **客户验证**：提交给客户验证功能
7. **ACP 专员**：归档经验教训

## 开发规范（必须遵守）

### 1. API 自测规范
**每一个 API 端点必须经过自测试，任何功能也需要进行自测。**

- **后端 API**：创建后必须编写测试脚本验证
  ```python
  # 测试脚本示例：test_api_xxx.py
  import asyncio
  from app.services.xxx_service import xxx_service
  from app.core.database import AsyncSessionLocal
  
  async def test():
      async with AsyncSessionLocal() as db:
          result = await xxx_service.get_data(db)
          print(f"Test result: {result}")
          assert len(result) >= 0, "API should return data"
  
  if __name__ == "__main__":
      asyncio.run(test())
  ```

- **数据提供者**：每个数据源（baostock/akshare）必须单独测试
  - 测试登录功能
  - 测试数据获取
  - 测试错误处理

- **前端功能**：添加新功能后必须刷新页面测试
  - 检查浏览器控制台是否有错误
  - 验证功能是否按预期工作

### 2. 错误处理规范
- **外部 API 调用**：必须添加完整的错误处理
  - 检查返回值是否为 None
  - 检查必要的属性是否存在（使用 `hasattr`）
  - 使用 try-except 捕获异常
  - 记录详细的错误日志

### 3. 数据库操作规范
- **新增模型**：必须在 `app/models/__init__.py` 中导入
- **新增字段**：需要创建迁移脚本，不能直接修改 `init_db.py`
- **表创建**：运行 `python scripts/init_db.py` 验证表是否正确创建

## 核心文档位置
| 文档 | 位置 | 说明 |
|------|------|------|
| 项目开发计划 | `docs/01_项目开发计划.md` | 包含里程碑、项目进度 |
| 架构设计 | `docs/02_架构设计.md` | 系统架构、技术栈、数据库设计 |
| 需求分析 | `docs/03_需求分析.md` | 功能需求、非功能需求 |
| 测试文档 | `docs/04_测试文档.md` | 测试用例、测试执行记录 |

## 经验教训
### 2026-02-23 经验教训
1. **ACP 开发流程必须遵循**：开发前应执行ACP 每日开发流程。
2. **模型文件覆盖风险**：创建新模型时应先检查是否存在同名文件，避免覆盖现有代码。使用 `Glob` 工具搜索相关文件。
3. **数据库表同步**：新增 SQLAlchemy 模型后，必须运行 `python scripts/init_db.py` 创建新表。
4. **前端调试日志**：添加 `console.log` 有助于排查数据问题，但上线前应移除。
5. **ECharts 联动实现**：使用单实例 + 多 grid 布局比多实例更易实现图表联动。
6. **SQLAlchemy 关系预加载**：使用 `joinedload()` 预加载关联关系，避免 N+1 查询问题和加载失败。
7. **导入路径规范**：数据库连接使用 `from app.core.database import get_db`，不是 `from app.database import get_db`。
8. **数据有效性检查**：前端计算技术指标前应过滤无效数据（null/undefined），参数应自适应数据量。

### 2026-02-23 股票详情页开发经验教训
1. **JavaScript 变量作用域**：ECharts 事件监听器中使用的外部变量需要是全局可访问的，否则会出现 `undefined` 错误。
2. **技术指标数组长度一致性**：KDJ、RSI 等技术指标计算时，返回的数组长度必须与原始数据长度一致，否则 ECharts 会报错。
3. **ECharts 图例位置优化**：图例放在顶部会遮挡K线图，移到右侧垂直显示可以节省空间。
4. **MACD 柱状图颜色**：需要根据正负值动态设置颜色，使用 `itemStyle.color` 回调函数实现。
5. **数据过滤条件**：过滤股票数据时，不能简单用 `d.open && d.high` 判断，因为开盘价可能为0（停牌），应使用 `!== null && !== undefined` 判断。
6. **布局网格系统**：使用 `grid-cols-8` 配合 `col-span-7` 和 `col-span-1` 可以实现更精细的宽度控制（7:1比例）。

### 2026-02-24 拼音搜索与板块数据开发经验教训
1. **数据库迁移脚本**：新增字段到现有表需要创建独立的迁移脚本，不能直接修改 `init_db.py`。
2. **SQLAlchemy text() 函数**：执行原生 SQL 语句时，必须使用 `text()` 函数包装 SQL 字符串。
3. **拼音库使用**：使用 `pypinyin.lazy_pinyin()` 获取拼音列表，取首字母拼接成首字母缩写。
4. **AKShare 板块数据**：行业板块使用 `stock_board_industry_name_em()`，概念板块使用 `stock_board_concept_name_em()`。
5. **金额格式化**：前端自动将万元转换为亿元显示，提高可读性。
6. **多字段搜索**：后端使用 SQL `OR` 条件支持多字段搜索，前端通过单个搜索框输入关键词。
7. **排序功能实现**：后端支持 `sort_by` 和 `sort_order` 参数，前端通过下拉框选择排序方式。
