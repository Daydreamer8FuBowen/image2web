from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorCode:
    code: str
    message: str


INVALID_API_KEY = ErrorCode("AUTH_001", "Key 无效")
INSUFFICIENT_BALANCE = ErrorCode("AUTH_002", "可用次数不足")
DISABLED_API_KEY = ErrorCode("AUTH_003", "Key 已被禁用")
UNAUTHORIZED_ADMIN = ErrorCode("AUTH_004", "管理员 Key 无效")
IMAGE_LIMIT_EXCEEDED = ErrorCode("GEN_001", "最多只能上传 3 张图片")
IMAGE_FORMAT_INVALID = ErrorCode("GEN_002", "仅支持 png、jpg、jpeg、webp 图片")
IMAGE_TOO_LARGE = ErrorCode("GEN_003", "图片大小超出限制")
EMPTY_GENERATION_INPUT = ErrorCode("GEN_004", "提示词和输入图片不能同时为空")
TASK_NOT_FOUND = ErrorCode("GEN_005", "任务不存在")
PROVIDER_CALL_FAILED = ErrorCode("GEN_006", "图像生成服务调用失败")
IMAGE_URL_NOT_FOUND = ErrorCode("GEN_007", "未能从接口返回中提取图片地址")
FILE_SAVE_FAILED = ErrorCode("GEN_008", "文件保存失败")


class AppError(Exception):
    def __init__(self, error_code: ErrorCode, detail: str | None = None, status_code: int = 400):
        self.error_code = error_code
        self.detail = detail or error_code.message
        self.status_code = status_code
        super().__init__(self.detail)

    def to_dict(self) -> dict[str, str]:
        return {"code": self.error_code.code, "message": self.detail}
