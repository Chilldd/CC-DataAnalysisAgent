"""TOON 序列化模块 - 将数据转换为 TOON (Token-Oriented Object Notation) 格式

TOON 格式特点：
- 比 JSON 节省约 40% 的 token
- 保持 JSON 数据模型
- 使用缩进表示层级
- 表格数据使用类似 CSV 的紧凑格式

GitHub: https://github.com/toon-format/toon
"""

import json
from typing import Any, Union
import pandas as pd
import numpy as np


def to_toon(data: Any, delimiter: str = ",") -> str:
    """
    将 Python 数据结构转换为 TOON 格式

    Args:
        data: 要转换的数据（dict, list, 或基本类型）
        delimiter: 表格数据的分隔符，默认逗号

    Returns:
        TOON 格式的字符串

    Examples:
        >>> data = {"name": "Alice", "age": 30, "hobbies": ["reading", "gaming"]}
        >>> print(to_toon(data))
        name: Alice
        age: 30
        hobbies[2]: reading,gaming

        >>> data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
        >>> print(to_toon(data))
        users[2]{id,name}:
          1,Alice
          2,Bob
    """
    if data is None:
        return "~"

    return _convert_value(data, delimiter=delimiter)


def _convert_value(value: Any, delimiter: str = ",") -> str:
    """转换单个值

    Args:
        value: 要转换的值
        delimiter: 分隔符

    Returns:
        TOON 格式字符串
    """
    if value is None:
        return "~"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        return _escape_string(value)
    elif isinstance(value, dict):
        return _convert_dict(value, delimiter=delimiter)
    elif isinstance(value, list):
        return _convert_list(value, delimiter=delimiter)
    elif isinstance(value, tuple):
        return _convert_list(list(value), delimiter=delimiter)
    elif isinstance(value, (np.integer, np.int64, np.int32)):
        return str(int(value))
    elif isinstance(value, (np.floating, np.float64, np.float32)):
        return str(float(value))
    elif isinstance(value, (np.bool_, bool)):
        return "true" if value else "false"
    elif pd.isna(value):
        return "~"
    elif hasattr(value, 'isoformat'):  # datetime
        return value.isoformat()
    else:
        # 其他类型转字符串
        return _escape_string(str(value))


def _convert_dict(data: dict, delimiter: str = ",") -> str:
    """转换字典为 TOON 格式

    Args:
        data: 字典数据
        delimiter: 分隔符

    Returns:
        TOON 格式字符串
    """
    if not data:
        return "{}"

    lines = []

    for key, value in data.items():
        key_str = _sanitize_key(key)
        value_str = _convert_value(value, delimiter=delimiter)

        # 如果是数组，添加数组长度和字段信息
        if isinstance(value, list) and value:
            array_line = _convert_array_inline(key_str, value, delimiter=delimiter)
            lines.append(array_line)
        else:
            lines.append(f"{key_str}: {value_str}")

    return "\n".join(lines)


def _convert_list(data: list, delimiter: str = ",") -> str:
    """转换列表为 TOON 格式

    Args:
        data: 列表数据
        delimiter: 分隔符

    Returns:
        TOON 格式字符串
    """
    if not data:
        return "[]"

    # 检查是否是对象数组（所有元素都是字典且有相同的键）
    if all(isinstance(item, dict) for item in data):
        return _convert_object_array(data, delimiter=delimiter)

    # 对于嵌套数组或复杂结构，使用多行格式
    if any(isinstance(item, (list, dict)) for item in data):
        lines = [f"[{len(data)}]:"]
        for item in data:
            if isinstance(item, list):
                # 嵌套数组：转换为 JSON 字符串表示
                item_str = json.dumps(item, ensure_ascii=False)
            elif isinstance(item, dict):
                # 嵌套对象：转换为 JSON 字符串表示
                item_str = json.dumps(item, ensure_ascii=False)
            else:
                item_str = _convert_value(item, delimiter=delimiter)
            lines.append(f"  {item_str}")
        return "\n".join(lines)

    # 简单数组（所有元素都是基本类型）
    values = [_convert_value(item, delimiter=delimiter) for item in data]
    return f"[{len(data)}]: " + delimiter.join(values)


def _convert_object_array(data: list[dict], delimiter: str = ",") -> str:
    """转换对象数组为 TOON 表格格式

    Args:
        data: 对象数组
        delimiter: 分隔符

    Returns:
        TOON 表格格式字符串
    """
    if not data:
        return "[]"

    # 获取所有字段
    fields = []
    for item in data:
        for key in item.keys():
            if key not in fields:
                fields.append(key)

    if not fields:
        return f"[{len(data)}]{{}}:"

    # 构建表头
    header = f"{len(data)}{{{delimiter.join(fields)}}}:"

    # 构建数据行
    rows = []
    for item in data:
        row_values = []
        for field in fields:
            value = item.get(field)
            row_values.append(_convert_value(value, delimiter=delimiter))
        rows.append("  " + delimiter.join(row_values))

    return header + "\n" + "\n".join(rows)


def _convert_array_inline(key: str, data: list, delimiter: str = ",") -> str:
    """将数组转换为内联格式

    Args:
        key: 键名
        data: 数组数据
        delimiter: 分隔符

    Returns:
        TOON 内联数组字符串
    """
    if not data:
        return f"{key}[0]:"

    # 检查是否是对象数组
    if all(isinstance(item, dict) for item in data):
        # 使用表格格式
        if not data:
            return f"{key}[0]{{}}:"

        # 获取所有字段
        fields = []
        for item in data:
            for k in item.keys():
                if k not in fields:
                    fields.append(k)

        if not fields:
            return f"{key}[{len(data)}]{{}}:"

        # 构建表头
        header = f"{key}[{len(data)}]{{{delimiter.join(fields)}}}:"

        # 构建数据行
        rows = []
        for item in data:
            row_values = []
            for field in fields:
                value = item.get(field)
                row_values.append(_convert_value(value, delimiter=delimiter))
            rows.append("  " + delimiter.join(row_values))

        return header + "\n" + "\n".join(rows)

    # 简单数组
    values = [_convert_value(item, delimiter=delimiter) for item in data]
    return f"{key}[{len(data)}]: " + delimiter.join(values)


def _sanitize_key(key: str) -> str:
    """清理键名，确保安全性

    Args:
        key: 原始键名

    Returns:
        清理后的键名
    """
    # 移除控制字符和特殊字符
    if not isinstance(key, str):
        key = str(key)
    # 保留字母、数字、下划线和连字符
    return "".join(c if c.isalnum() or c in "_-." else "_" for c in key)


def _escape_string(value: str) -> str:
    """转义字符串值

    Args:
        value: 原始字符串

    Returns:
        转义后的字符串
    """
    if not isinstance(value, str):
        value = str(value)

    # 如果包含特殊字符（逗号、换行、引号），使用引号包裹
    if any(c in value for c in [",", "\n", '"', "'"]):
        # 使用双引号包裹，转义内部引号
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'

    return value


def serialize_result(
    data: Any,
    format_type: str = "json",
    delimiter: str = ",",
    show_format: bool = True
) -> str:
    """
    序列化结果数据为指定格式

    Args:
        data: 要序列化的数据
        format_type: 格式类型 ("json" 或 "toon")
        delimiter: TOON 格式的分隔符（默认逗号）
        show_format: 是否在输出中显示格式信息

    Returns:
        序列化后的字符串
    """
    if format_type == "toon":
        result = to_toon(data, delimiter=delimiter)
        if show_format:
            result = f"```toon\n{result}\n```"
        return result
    else:
        return json.dumps(data, ensure_ascii=False, indent=2)


def estimate_token_savings(json_data: Union[str, dict]) -> dict:
    """
    估算使用 TOON 格式相比 JSON 的 token 节省

    Args:
        json_data: JSON 数据（字符串或字典）

    Returns:
        包含估算结果的字典
    """
    if isinstance(json_data, dict):
        json_str = json.dumps(json_data, ensure_ascii=False)
    else:
        json_str = json_data

    toon_str = to_toon(json.loads(json_str))

    # 简单估算：使用字符数作为 token 的近似值
    json_tokens = len(json_str)
    toon_tokens = len(toon_str)

    savings = json_tokens - toon_tokens
    savings_percent = (savings / json_tokens * 100) if json_tokens > 0 else 0

    return {
        "json_size": json_tokens,
        "toon_size": toon_tokens,
        "saved_tokens": savings,
        "savings_percent": round(savings_percent, 1)
    }
