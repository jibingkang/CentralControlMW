from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db, get_db_status, update_db_config
from app.tcp_client import get_tcp_status, check_tcp_connection, reconnect_tcp, send_custom_message, close_tcp_connection
from app.schemas import TCPConfigUpdate, TCPConfigResponse, DatabaseConfigUpdate, DatabaseConfigResponse, APIResponse
from pydantic import BaseModel
from app import crud
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/config/tcp", response_model=APIResponse)
async def get_tcp_config(
    db: Session = Depends(get_db)
):
    try:
        config = crud.get_tcp_config(db)
        return APIResponse(
            code=200,
            message="success",
            data=config
        )
    except Exception as e:
        # 返回默认配置
        return APIResponse(
            code=200,
            message="success (using default config)",
            data={
                "tcp_server_host": "192.168.1.200",
                "tcp_server_port": 8080
            }
        )


@router.put("/config/tcp", response_model=APIResponse)
async def update_tcp_config(
    request: Request,
    config_data: TCPConfigUpdate,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else ""

    try:
        old_config = crud.get_tcp_config(db)
        new_config = crud.update_tcp_config(db, config_data)

        crud.create_operation_log(
            db=db,
            log_type="config",
            device_id="",
            convert_code="",
            request_data={"old": old_config, "new": config_data.model_dump(exclude_none=True)},
            response_data=new_config,
            status="success",
            client_ip=client_ip
        )

        return APIResponse(
            code=200,
            message="success",
            data=new_config
        )
    except Exception as e:
        return APIResponse(
            code=500,
            message="Database error",
            data=None
        )


@router.get("/config/status", response_model=APIResponse)
async def get_system_status():
    """获取系统状态（数据库和TCP连接状态）"""
    db_status = get_db_status()
    tcp_status = get_tcp_status()
    
    return APIResponse(
        code=200,
        message="success",
        data={
            "database": db_status,
            "tcp": tcp_status
        }
    )


@router.post("/config/tcp/check", response_model=APIResponse)
async def check_tcp_connectivity(
    request: Request,
    config_data: TCPConfigUpdate
):
    """检查TCP连接状态"""
    client_ip = request.client.host if request.client else ""
    
    try:
        is_connected = check_tcp_connection(
            host=config_data.tcp_server_host,
            port=config_data.tcp_server_port
        )
        
        return APIResponse(
            code=200,
            message="success",
            data={
                "connected": is_connected,
                "host": config_data.tcp_server_host,
                "port": config_data.tcp_server_port,
                "status": get_tcp_status()
            }
        )
    except Exception as e:
        return APIResponse(
            code=500,
            message=str(e),
            data=None
        )


@router.get("/config/database", response_model=APIResponse)
async def get_database_config():
    """获取数据库配置"""
    from app.config import settings
    
    try:
        return APIResponse(
            code=200,
            message="success",
            data={
                "db_host": settings.DB_HOST,
                "db_port": settings.DB_PORT,
                "db_user": settings.DB_USER,
                "db_name": settings.DB_NAME
            }
        )
    except Exception as e:
        logger.error(f"获取数据库配置失败: {str(e)}")
        return APIResponse(
            code=500,
            message="Database error",
            data=None
        )


@router.put("/config/database", response_model=APIResponse)
async def update_database_config(
    request: Request,
    config_data: DatabaseConfigUpdate
):
    """更新数据库配置"""
    client_ip = request.client.host if request.client else ""
    
    try:
        # 更新数据库配置
        success = update_db_config(
            host=config_data.db_host,
            port=config_data.db_port,
            user=config_data.db_user,
            password=config_data.db_password,
            db_name=config_data.db_name
        )
        
        if success:
            logger.info(f"数据库配置更新成功: {config_data.model_dump(exclude_none=True)}")
            return APIResponse(
                code=200,
                message="success",
                data=config_data.model_dump(exclude_none=True)
            )
        else:
            return APIResponse(
                code=500,
                message="Failed to update database config",
                data=None
            )
    except Exception as e:
        logger.error(f"更新数据库配置失败: {str(e)}")
        return APIResponse(
            code=500,
            message=f"Database error: {str(e)}",
            data=None
        )


class TCPReconnectRequest(BaseModel):
    host: str
    port: int


class TCPCustomMessageRequest(BaseModel):
    host: str
    port: int
    message: str


@router.post("/config/tcp/reconnect", response_model=APIResponse)
async def reconnect_tcp_connection(
    request: Request,
    reconnect_data: TCPReconnectRequest
):
    """重新连接TCP"""
    client_ip = request.client.host if request.client else ""
    
    try:
        success = reconnect_tcp(
            host=reconnect_data.host,
            port=reconnect_data.port
        )
        
        return APIResponse(
            code=200 if success else 500,
            message="success" if success else "failed",
            data={
                "connected": success,
                "host": reconnect_data.host,
                "port": reconnect_data.port,
                "status": get_tcp_status()
            }
        )
    except Exception as e:
        logger.error(f"重新连接TCP失败: {str(e)}")
        return APIResponse(
            code=500,
            message=str(e),
            data=None
        )


@router.post("/config/tcp/send", response_model=APIResponse)
async def send_tcp_test_message(
    request: Request,
    message_data: TCPCustomMessageRequest
):
    """发送自定义TCP消息（用于测试）"""
    client_ip = request.client.host if request.client else ""
    
    try:
        result = send_custom_message(
            host=message_data.host,
            port=message_data.port,
            message=message_data.message
        )
        
        logger.info(f"发送自定义TCP消息结果: {result}")
        return APIResponse(
            code=200 if result["success"] else 500,
            message="success" if result["success"] else "failed",
            data=result
        )
    except Exception as e:
        logger.error(f"发送自定义TCP消息失败: {str(e)}")
        return APIResponse(
            code=500,
            message=str(e),
            data=None
        )


@router.post("/config/tcp/close", response_model=APIResponse)
async def close_tcp(
    request: Request
):
    """关闭TCP连接"""
    client_ip = request.client.host if request.client else ""
    
    try:
        success = close_tcp_connection()
        
        return APIResponse(
            code=200 if success else 500,
            message="success" if success else "failed",
            data={
                "closed": success,
                "status": get_tcp_status()
            }
        )
    except Exception as e:
        logger.error(f"关闭TCP连接失败: {str(e)}")
        return APIResponse(
            code=500,
            message=str(e),
            data=None
        )
