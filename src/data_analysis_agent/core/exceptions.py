"""DataAnalysisAgent 自定义异常类

提供统一的异常处理机制，便于错误追踪和用户友好的错误提示。
"""

from typing import Optional, Any


class DataAnalysisAgentError(Exception):
    """DataAnalysisAgent 基础异常类

    所有自定义异常的父类，提供统一的错误处理接口。
    """

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        """初始化异常

        Args:
            message: 错误信息
            details: 额外的错误详情（可选）
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """将异常转换为字典格式

        Returns:
            包含错误信息的字典
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class FileError(DataAnalysisAgentError):
    """文件相关异常

    当文件读取、解析或处理失败时抛出。
    """

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        """初始化文件异常

        Args:
            message: 错误信息
            file_path: 文件路径（可选）
            details: 额外的错误详情
        """
        if details is None:
            details = {}
        if file_path:
            details["file_path"] = file_path
        super().__init__(message, details)
        self.file_path = file_path


class FileNotFoundError(FileError):
    """文件不存在异常"""

    def __init__(self, file_path: str) -> None:
        super().__init__(
            f"文件不存在: {file_path}",
            file_path=file_path
        )


class FileFormatError(FileError):
    """文件格式不支持异常"""

    def __init__(self, file_path: str, format: str, supported_formats: list[str]) -> None:
        super().__init__(
            f"不支持的文件格式: .{format}。支持的格式: {', '.join(supported_formats)}",
            file_path=file_path,
            details={"format": format, "supported_formats": supported_formats}
        )


class FileEncodingError(FileError):
    """文件编码异常"""

    def __init__(self, file_path: str, encoding: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(
            f"文件编码错误: {encoding}",
            file_path=file_path,
            details=details
        )


class DataError(DataAnalysisAgentError):
    """数据处理相关异常

    当数据验证、转换或聚合失败时抛出。
    """

    def __init__(
        self,
        message: str,
        column: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        """初始化数据异常

        Args:
            message: 错误信息
            column: 相关列名（可选）
            details: 额外的错误详情
        """
        if details is None:
            details = {}
        if column:
            details["column"] = column
        super().__init__(message, details)
        self.column = column


class ColumnNotFoundError(DataError):
    """列不存在异常"""

    def __init__(self, column: str, available_columns: Optional[list[str]] = None) -> None:
        details = {"available_columns": available_columns} if available_columns else None
        super().__init__(
            f"列不存在: {column}",
            column=column,
            details=details
        )


class AggregationError(DataError):
    """聚合操作异常"""

    def __init__(
        self,
        message: str,
        aggregation: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        if details is None:
            details = {}
        if aggregation:
            details["aggregation"] = aggregation
        super().__init__(message, details=details)
        self.aggregation = aggregation


class FilterError(DataError):
    """过滤条件异常"""

    def __init__(
        self,
        message: str,
        filter_details: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details=filter_details)


class ConfigError(DataAnalysisAgentError):
    """配置相关异常

    当配置加载、验证或使用失败时抛出。
    """

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        """初始化配置异常

        Args:
            message: 错误信息
            config_key: 配置键（可选）
            details: 额外的错误详情
        """
        if details is None:
            details = {}
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, details)
        self.config_key = config_key


class ValidationError(DataAnalysisAgentError):
    """数据验证异常

    当数据不符合预期格式或约束时抛出。
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        """初始化验证异常

        Args:
            message: 错误信息
            field: 验证失败的字段（可选）
            value: 验证失败的值（可选）
            details: 额外的错误详情
        """
        if details is None:
            details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(message, details)
        self.field = field
        self.value = value


class CacheError(DataAnalysisAgentError):
    """缓存相关异常

    当缓存操作失败时抛出。
    """

    def __init__(
        self,
        message: str,
        cache_key: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        """初始化缓存异常

        Args:
            message: 错误信息
            cache_key: 缓存键（可选）
            details: 额外的错误详情
        """
        if details is None:
            details = {}
        if cache_key:
            details["cache_key"] = cache_key
        super().__init__(message, details)
        self.cache_key = cache_key


class ChartError(DataAnalysisAgentError):
    """图表生成相关异常

    当图表配置或渲染失败时抛出。
    """

    def __init__(
        self,
        message: str,
        chart_type: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        """初始化图表异常

        Args:
            message: 错误信息
            chart_type: 图表类型（可选）
            details: 额外的错误详情
        """
        if details is None:
            details = {}
        if chart_type:
            details["chart_type"] = chart_type
        super().__init__(message, details)
        self.chart_type = chart_type
