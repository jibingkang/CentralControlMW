from sqlalchemy.orm import Session
from app.models import DeviceMapping, SystemConfig, OperationLog
from app.schemas import DeviceMappingCreate, DeviceMappingUpdate, TCPConfigUpdate
from typing import Optional, List
import json
from datetime import datetime


def get_device_mapping_by_device_id(db: Session, device_id: str) -> Optional[DeviceMapping]:
    return db.query(DeviceMapping).filter(DeviceMapping.device_id == device_id).first()


def get_device_mapping(db: Session, mapping_id: int) -> Optional[DeviceMapping]:
    return db.query(DeviceMapping).filter(DeviceMapping.id == mapping_id).first()


def get_device_mappings(db: Session, skip: int = 0, limit: int = 100, device_id: Optional[str] = None, convert_code: Optional[str] = None) -> List[DeviceMapping]:
    query = db.query(DeviceMapping)
    
    if device_id:
        query = query.filter(DeviceMapping.device_id.like(f"%{device_id}%"))
    if convert_code:
        query = query.filter(DeviceMapping.convert_code.like(f"%{convert_code}%"))
    
    return query.offset(skip).limit(limit).all()


def create_device_mapping(db: Session, mapping: DeviceMappingCreate) -> DeviceMapping:
    db_mapping = DeviceMapping(
        device_id=mapping.device_id,
        convert_code=mapping.convert_code,
        description=mapping.description or ""
    )
    db.add(db_mapping)
    db.commit()
    db.refresh(db_mapping)
    return db_mapping


def update_device_mapping(db: Session, mapping_id: int, mapping: DeviceMappingUpdate) -> Optional[DeviceMapping]:
    db_mapping = get_device_mapping(db, mapping_id)
    if not db_mapping:
        return None
    if mapping.device_id is not None:
        db_mapping.device_id = mapping.device_id
    if mapping.convert_code is not None:
        db_mapping.convert_code = mapping.convert_code
    if mapping.description is not None:
        db_mapping.description = mapping.description
    db.commit()
    db.refresh(db_mapping)
    return db_mapping


def delete_device_mapping(db: Session, mapping_id: int) -> bool:
    db_mapping = get_device_mapping(db, mapping_id)
    if not db_mapping:
        return False
    db.delete(db_mapping)
    db.commit()
    return True


def get_tcp_config(db: Session) -> dict:
    host = db.query(SystemConfig).filter(SystemConfig.config_key == "tcp_server_host").first()
    port = db.query(SystemConfig).filter(SystemConfig.config_key == "tcp_server_port").first()
    return {
        "tcp_server_host": host.config_value if host else "192.168.1.200",
        "tcp_server_port": int(port.config_value) if port else 8080
    }


def update_tcp_config(db: Session, config: TCPConfigUpdate) -> dict:
    if config.tcp_server_host is not None:
        db_config = db.query(SystemConfig).filter(SystemConfig.config_key == "tcp_server_host").first()
        if db_config:
            db_config.config_value = config.tcp_server_host
        else:
            db_config = SystemConfig(config_key="tcp_server_host", config_value=config.tcp_server_host)
            db.add(db_config)

    if config.tcp_server_port is not None:
        db_config = db.query(SystemConfig).filter(SystemConfig.config_key == "tcp_server_port").first()
        if db_config:
            db_config.config_value = str(config.tcp_server_port)
        else:
            db_config = SystemConfig(config_key="tcp_server_port", config_value=str(config.tcp_server_port))
            db.add(db_config)

    db.commit()
    return get_tcp_config(db)


def create_operation_log(
    db: Session,
    log_type: str,
    device_id: str,
    convert_code: str,
    request_data: dict,
    response_data: dict,
    status: str,
    error_message: Optional[str] = None,
    client_ip: str = ""
) -> OperationLog:
    db_log = OperationLog(
        log_type=log_type,
        device_id=device_id,
        convert_code=convert_code,
        request_data=json.dumps(request_data, ensure_ascii=False),
        response_data=json.dumps(response_data, ensure_ascii=False),
        status=status,
        error_message=error_message,
        client_ip=client_ip
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_operation_logs(
    db: Session,
    log_type: Optional[str] = None,
    device_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> tuple:
    query = db.query(OperationLog)

    if log_type:
        query = query.filter(OperationLog.log_type == log_type)
    if device_id:
        query = query.filter(OperationLog.device_id == device_id)
    if status:
        query = query.filter(OperationLog.status == status)
    if start_date:
        query = query.filter(OperationLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(OperationLog.created_at <= datetime.fromisoformat(end_date))

    total = query.count()
    logs = query.order_by(OperationLog.created_at.desc()).offset(skip).limit(limit).all()
    return total, logs


def get_operation_log(db: Session, log_id: int) -> Optional[OperationLog]:
    return db.query(OperationLog).filter(OperationLog.id == log_id).first()


def delete_operation_log(db: Session, log_id: int) -> bool:
    """删除操作日志"""
    db_log = get_operation_log(db, log_id)
    if not db_log:
        return False
    db.delete(db_log)
    db.commit()
    return True


def delete_operation_logs(db: Session, log_ids: List[int]) -> int:
    """批量删除操作日志"""
    deleted_count = db.query(OperationLog).filter(OperationLog.id.in_(log_ids)).delete(synchronize_session=False)
    db.commit()
    return deleted_count
