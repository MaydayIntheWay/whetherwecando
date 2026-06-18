"""
爬虫相关Pydantic数据模型
"""
from typing import Optional, Literal, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum

T = TypeVar('T')


class Platform(str, Enum):
    XIAOHONGSHU = 'xiaohongshu'
    ZHIHU = 'zhihu'


class LoginType(str, Enum):
    QRCODE = 'qrcode'
    COOKIE = 'cookie'


class AuthStatus(str, Enum):
    VALID = 'valid'
    EXPIRING = 'expiring'
    EXPIRED = 'expired'
    INVALID = 'invalid'


class TaskStatus(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class LogLevel(str, Enum):
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    DEBUG = 'debug'


class CrawlerAuthConfig(BaseModel):
    platform: Platform
    login_type: LoginType
    encrypted_cookie: str
    status: AuthStatus = AuthStatus.INVALID
    expires_at: Optional[datetime] = None
    last_validated_at: Optional[datetime] = None


class CrawlTask(BaseModel):
    platform: Platform
    keyword: str = Field(..., min_length=1, max_length=255)
    max_count: int = Field(default=50, ge=1, le=100)
    status: TaskStatus = TaskStatus.PENDING
    total_count: int = 0
    success_count: int = 0
    error_count: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class CrawlLog(BaseModel):
    task_id: str
    level: LogLevel
    message: str
    details: Optional[dict] = None


class AuthConfigRequest(BaseModel):
    platform: Platform
    login_type: LoginType
    cookie_value: str = Field(..., min_length=10)
    
    @field_validator('cookie_value')
    @classmethod
    def validate_cookie(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError('Cookie值太短，请检查')
        return v.strip()


class AuthConfigResult(BaseModel):
    platform: Platform
    status: AuthStatus
    message: str
    expires_at: Optional[datetime] = None


class QRCodeResult(BaseModel):
    platform: Platform
    qrcode_url: str
    qrcode_base64: str
    expires_in: int


class AuthStatusResult(BaseModel):
    platform: Platform
    status: AuthStatus
    last_validated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    message: str


class CrawlRequest(BaseModel):
    platform: Platform
    keyword: str = Field(..., min_length=1, max_length=255)
    max_count: int = Field(default=50, ge=1, le=100)


class CrawlResult(BaseModel):
    task_id: str
    platform: Platform
    keyword: str
    total: int
    success: int
    items: list[dict]
    status: TaskStatus
    error_message: Optional[str] = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    error_code: str
    details: Optional[dict] = None
