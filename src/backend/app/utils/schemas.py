"""
Pydantic数据模型定义
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date

# ==================== 用户认证相关 ====================

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6)

class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    tokenType: str = "Bearer"
    expiresIn: int
    userInfo: dict

# ==================== 数据导入相关 ====================

class ImportErrorItem(BaseModel):
    """导入错误项"""
    row: int
    field: str
    error: str

class ImportResponse(BaseModel):
    """导入响应"""
    batchNo: str
    totalRows: int
    successRows: int
    repeatRows: int
    invalidRows: int
    errors: Optional[List[ImportErrorItem]] = None

# ==================== 工时查询相关 ====================

class ProjectQueryParams(BaseModel):
    """项目维度查询参数"""
    projectName: Optional[str] = None
    projectManager: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    sortBy: Optional[str] = 'start_time'
    sortOrder: str = 'desc'

class OrganizationQueryParams(BaseModel):
    """组织维度查询参数"""
    deptName: Optional[str] = None
    userName: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    sortBy: Optional[str] = 'start_time'
    sortOrder: str = 'desc'

# ==================== 工时核对相关 ====================

class IntegrityCheckParams(BaseModel):
    """完整性检查参数"""
    startDate: str  # YYYY-MM-DD
    endDate: str    # YYYY-MM-DD
    deptName: Optional[str] = None
    userName: Optional[str] = None
    workdays: List[int] = Field(default=[1, 2, 3, 4, 5])

    @validator('workdays')
    def validate_workdays(cls, v):
        if not all(1 <= d <= 7 for d in v):
            raise ValueError('工作日必须是1-7之间的整数')
        return v

class ComplianceCheckParams(BaseModel):
    """合规性检查参数"""
    startDate: str  # YYYY-MM-DD
    endDate: str    # YYYY-MM-DD
    deptName: Optional[str] = None
    userName: Optional[str] = None
    standardHours: float = Field(default=8, ge=1, le=24)
    minHours: float = Field(default=4, ge=0, le=24)
    maxOvertime: float = Field(default=4, ge=0, le=24)
    maxMonthlyOvertime: float = Field(default=80, ge=0, le=200)

# ==================== 通用响应 ====================

class ApiResponse(BaseModel):
    """统一API响应"""
    code: int = 200
    message: str = "操作成功"
    data: Optional[dict] = None
    timestamp: Optional[str] = None

class PaginatedResponse(BaseModel):
    """分页响应"""
    list: List[dict]
    total: int
    page: int
    size: int
    totalPages: int
