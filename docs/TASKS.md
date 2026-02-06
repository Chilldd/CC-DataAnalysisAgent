# DataAnalysisAgent 任务清单

本文档记录待办任务和未来规划。

> **项目状态**: v0.13.0 (2026-02-06)
> **最新版本**: 代码质量提升 - 类型注解、异常处理、配置文件支持

---

## 高优先级

### 1. CSV 编码自动检测 (P0)

**问题**: CSV 文件编码不统一可能导致读取失败

**方案**:
```python
# core/excel_reader.py
import chardet

def _detect_encoding(self):
    with open(self.file_path, 'rb') as f:
        result = chardet.detect(f.read(10000))
        return result['encoding'] or 'utf-8'
```

**影响**: 提升兼容性

---

## 功能增强

### 4. 支持更多文件格式 (P1)

**当前支持**: .xlsx, .xls, .csv

**计划添加**: .parquet, .json, .jsonl, .tsv, .xlsb, .ods

**位置**: `core/excel_reader.py:_read_file`

---

### 5. 数据导出功能 (P2)

**新增工具**: `export_data`

**导出格式**: Excel, CSV, JSON, PNG

**用途**: 将分析结果导出为各种格式

---

### 6. 多文件关联分析 (P2)

**新增**: `join_reader.py`, `join_data.py`

**支持**: 内连接、左连接、右连接

**用途**: 关联多个数据源进行分析

---

### 7. 数据清洗功能 (P2)

**新增工具**: `clean_data`

**功能**: 去重、空值处理、类型转换、异常检测

**用途**: 自动化数据清洗流程

---

### 8. 自定义图表主题 (P2)

**位置**: `core/chart_renderer.py`

**主题**: 暗色、科技蓝、暖色、极简

**用途**: 一键切换图表风格

---

### 9. 图表导出功能 (P2)

**位置**: `core/chart_renderer.py`

**导出**: PNG, SVG, PDF

**用途**: 将图表导出为静态图片

---

## 配置与部署

### 14. Docker 镜像 (P2)

**文件**: Dockerfile, docker-compose.yml

**用途**: 容器化部署

---

### 15. 发布到 PyPI (P1)

**完善**: pyproject.toml, README 英文版, CHANGELOG.md

**用途**: 方便用户安装

---

## 性能优化

### 16. 缓存预热优化 (P2)

**位置**: `core/excel_reader.py`

**功能**:
- 在 `session_start` 时预加载常用列
- 自动分析历史查询模式
- 智能预测可能需要的列

---

### 17. 查询结果缓存 (P2)

**位置**: `core/excel_reader.py`

**功能**:
- 缓存聚合查询结果（不仅仅是原始数据）
- 支持不同参数的查询结果缓存
- LRU 清理策略

---

### 18. 增量数据读取 (P2)

**功能**:
- 支持 CSV 增量读取（只读取新增行）
- 追加模式数据处理
- 大文件持续监控

---

### 19. 性能监控增强 (P2)

**基于**: `MetricsLogger`

**功能**:
- 导出 Prometheus 指标格式
- 添加内存使用监控
- DataFrame 内存占用追踪
- 自定义指标阈值

---

### 20. Token 优化建议系统 (P2)

**新增**: `token_optimizer.py`

**功能**:
- 自动检测可优化的工具调用
- 建议使用 `usecols` 参数
- 建议分页读取大文件
- 检测重复查询

---

## 智能化

### 21. 数据验证功能 (P2)

**新增**: `validators.py`

**功能**:
- 列数据类型验证
- 数据范围验证
- 必填字段检查
- 自定义验证规则

---

### 22. 智能列推荐增强 (P2)

**位置**: `mcp/tools/get_excel_schema.py`

**功能**:
- 基于数据分布推荐图表类型
- 自动检测时间序列数据
- 检测分类/数值列的基数
- 推荐合适的聚合方式

---

### 23. 错误恢复机制 (P2)

**功能**:
- 文件读取失败重试
- 大文件处理进度保存
- 部分数据返回机制

---

## 版本规划

| 版本 | 里程碑 | 内容 |
|------|--------|------|
| v0.13.0 | ✅ 已完成 | 类型注解完善、异常处理优化、代码格式化配置、配置文件支持增强 |
| v0.12.0 | ✅ 已完成 | 扩展过滤操作符（in, not_in, is_null, is_not_null, starts_with, ends_with, regex）、扩展聚合函数进阶（percentile25/75/90, mode, cumsum/cummax/cummin, rolling_avg） |
| v0.11.0 | ✅ 已完成 | 扩展聚合函数：median, std, var, first, last, nunique |
| v0.10.1 | ✅ 已完成 | Bug 修复：修复预加载 bug，移除数据表格功能 |
| v0.10.0 | ✅ 已完成 | 首次加载优化：预加载文件功能 |
| v0.9.1 | ✅ 已完成 | Bug 修复：usecols 参数传递，字节解析 |
| v0.9.0 | ✅ 已完成 | 缓存优化：标准化缓存键、智能缓存共享、批量查询 |
| v0.8.0 | ✅ 已完成 | 日志系统增强：数据传输统计、性能监控 |
| v0.6.0 | ✅ 已完成 | Token 优化：get_excel_schema、usecols 参数 |
| v0.14.0 | 📋 规划中 | CSV 编码检测 |
| v1.0.0 | 🎯 长期目标 | 多文件关联、数据清洗、自定义主题、Docker |

---

## 备注

- **优先级**: P0 (紧急) > P1 (高) > P2 (中)
- **状态**: ✅ 已完成 | 🚧 进行中 | 📋 规划中 | 🎯 长期目标
- 每次发布版本后，对应任务从此文档中移除，更新至 DESIGN.md 版本历史
