from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class ButtonCallbackRequest(BaseModel):
    cmdToken: Optional[str] = ""
    mac: str
    result: int


class ButtonCallbackResponse(BaseModel):
    device_id: str
    convert_code_sent: str


class DeviceMappingBase(BaseModel):
    device_id: str
    convert_code: str
    description: Optional[str] = ""


class DeviceMappingCreate(DeviceMappingBase):
    pass


class DeviceMappingUpdate(BaseModel):
    device_id: Optional[str] = None
    convert_code: Optional[str] = None
    description: Optional[str] = None


class DeviceMappingResponse(DeviceMappingBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class TCPConfigBase(BaseModel):
    tcp_server_host: str
    tcp_server_port: int


class TCPConfigUpdate(BaseModel):
    tcp_server_host: Optional[str] = None
    tcp_server_port: Optional[int] = None


class TCPConfigResponse(TCPConfigBase):
    pass


class DatabaseConfigBase(BaseModel):
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str


class DatabaseConfigUpdate(BaseModel):
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    db_name: Optional[str] = None


class DatabaseConfigResponse(DatabaseConfigBase):
    pass


class OperationLogResponse(BaseModel):
    id: int
    log_type: str
    device_id: str
    convert_code: str
    request_data: Optional[str] = None
    response_data: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    client_ip: str
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class LogQueryParams(BaseModel):
    log_type: Optional[str] = None
    device_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    page: int = 1
    page_size: int = 20


class APIResponse(BaseModel):
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None
