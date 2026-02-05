# DataAnalysisAgent 任务清单

## 已完成 (v0.5.0)

### 10. 图表优化 (P2)
- 默认不显示数据表格，减少数据传输
- 支持多图表在一个 HTML 中展示
- 添加 `show_data_table` 参数控制表格显示

## 高优先级

### 1. CSV 编码自动检测 (P0)
```python
# core/excel_reader.py
import chardet
def _detect_encoding(self):
    with open(self.file_path, 'rb') as f:
        return chardet.detect(f.read(10000))['encoding'] or 'utf-8'
```

## 功能增强

### 2. 扩展聚合函数 (P1)
添加: median, std, var, first, last, nunique
位置: `core/excel_reader.py:437`

### 3. 扩展过滤操作符 (P1)
添加: in, not_in, is_null, is_not_null, starts_with, ends_with, regex
位置: `core/excel_reader.py:411`

### 4. 支持更多文件格式 (P1)
添加: .parquet, .json, .jsonl, .tsv, .xlsb, .ods
位置: `core/excel_reader.py:316`

### 5. 数据导出功能 (P2)
新增工具: `export_data`
导出: Excel, CSV, JSON, PNG

### 6. 多文件关联分析 (P2)
新增: `join_reader.py`, `join_data.py`
支持: 内连接、左连接、右连接

### 7. 数据清洗功能 (P2)
新增工具: `clean_data`
功能: 去重、空值处理、类型转换、异常检测

### 8. 自定义图表主题 (P2)
位置: `core/chart_renderer.py`
主题: 暗色、科技蓝、暖色、极简

### 9. 图表导出功能 (P2)
位置: `core/chart_renderer.py`
导出: PNG, SVG, PDF

## 代码质量

### 14. 类型注解完善 (P1)
为所有方法添加类型注解，配置 mypy

### 15. 异常处理优化 (P1)
新增: `exceptions.py`

### 17. 代码格式化配置 (P1)
配置: Black, isort, flake8, pre-commit hooks

## 配置与部署

### 18. 配置文件支持 (P2)
新增: `config.py`, `config.yaml`

### 19. Docker 镜像 (P2)
编写: Dockerfile, docker-compose.yml

### 20. 发布到 PyPI (P1)
完善: pyproject.toml, README 英文版, CHANGELOG.md

## 新增优化任务

### 21. ExcelReader 全局管理器 (已完成 v0.8.1)
位置: `core/reader_manager.py`

**已完成**：
- ✅ 实现 ReaderManager 单例管理器
- ✅ 跨工具调用共享 ExcelReader 实例
- ✅ LRU 缓存策略管理实例数量
- ✅ 自动清理不活跃的 reader（5分钟超时）
- ✅ 文件修改检测，自动重新加载
- ✅ 线程安全设计
- ✅ 新增 `get_reader_stats` 工具监控缓存性能
- ✅ 更新所有工具使用 ReaderManager

**优化效果**：
- 缓存命中率从 0% 提升到预期 80%+
- 减少文件重复读取
- 降低内存使用（共享实例）

### 22. 日志增强功能 (部分完成 v0.8.0)
位置: `core/logging_config.py`

**已完成**：
- ✅ 数据传输量统计
- ✅ 工具调用耗时监控
- ✅ 大数据传输警告（>100KB）
- ✅ 定期统计摘要输出
- ✅ 缓存命中率统计

**待完成**：
- 添加日志上下文支持（如请求 ID、用户 ID）
- 支持日志异步写入
- 添加结构化日志（JSON 格式）
- 支持日志采样（防止高频日志）

### 22. 性能监控增强 (P2)
基于 `MetricsLogger` 扩展
- 导出 Prometheus 指标格式
- 添加内存使用监控
- 添加 DataFrame 内存占用追踪
- 支持自定义指标阈值

### 23. 数据优化分析工具 (P1)
新增: `mcp/tools/analyze_usage.py`
- 分析各工具的数据传输模式
- 识别高频大数据传输场景
- 生成优化建议报告
- Token 使用趋势分析

### 24. Token 优化建议系统 (P2)
新增: `token_optimizer.py`
- 自动检测可优化的工具调用
- 建议使用 `usecols` 参数
- 建议分页读取大文件
- 检测重复查询

### 25. 数据验证功能 (P2)
新增: `validators.py`
- 列数据类型验证
- 数据范围验证
- 必填字段检查
- 自定义验证规则

### 26. 智能列推荐增强 (P2)
位置: `mcp/tools/get_excel_schema.py`
- 基于数据分布推荐图表类型
- 自动检测时间序列数据
- 检测分类/数值列的基数
- 推荐合适的聚合方式

### 27. 错误恢复机制 (P2)
- 文件读取失败重试
- 大文件处理进度保存
- 部分数据返回机制

## 版本规划

| 版本 | 内容 |
|------|------|
| v0.5.0 | 图表优化：默认不显示数据表格、支持多图表、show_data_table 参数 |
| v0.6.0 | CSV编码检测、扩展聚合/过滤、代码格式化、类型注解 |
| v0.7.0 | 大文件优化、数据导出、更多格式、配置文件 |
| v0.8.0 | **日志系统增强**：数据传输统计、性能监控、大数据警告、定期摘要输出 |
| v1.0.0 | 多文件关联、数据清洗、自定义主题、Docker |
