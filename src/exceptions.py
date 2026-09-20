from src.schemas import ExtractResult


class DataContractValidationError(ValueError):
    """Raised when a data contract contains invalid values or structure."""


class DataQualityThresholdExceeded(ValueError):
    def __init__(
        self,
        *,
        error_rate: float,
        max_error_rate: float,
        extract_result: ExtractResult,
    ) -> None:
        self.error_rate = error_rate
        self.max_error_rate = max_error_rate
        self.extract_result = extract_result
        super().__init__(
            f"Error rate {error_rate:.2%} exceeds maximum allowed {max_error_rate:.2%}"
        )
