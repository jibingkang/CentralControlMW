from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger
from sqlalchemy.sql import func
from app.database import Base


class DeviceMapping(Base):
    __tablename__ = "device_mapping"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(50), unique=True, nullable=False, comment="设备ID")
    convert_code = Column(String(100), nullable=False, comment="转换码")
    description = Column(String(200), default="", comment="描述")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    config_key = Column(String(50), unique=True, nullable=False)
    config_value = Column(String(200), nullable=False)
    description = Column(String(200), default="")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class OperationLog(Base):
    __tablename__ = "operation_log"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    log_type = Column(String(20), nullable=False, comment="日志类型")
    device_id = Column(String(50), default="", comment="设备ID")
    convert_code = Column(String(100), default="", comment="转换码")
    request_data = Column(Text, comment="请求数据JSON")
    response_data = Column(Text, comment="响应数据JSON")
    status = Column(String(20), nullable=False, comment="状态")
    error_message = Column(Text, comment="错误信息")
    client_ip = Column(String(50), default="", comment="客户端IP")
    created_at = Column(DateTime, server_default=func.now())
