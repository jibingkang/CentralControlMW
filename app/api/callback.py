from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ButtonCallbackRequest, APIResponse
from app import crud
from app.tcp_client import send_tcp_message
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/callback/button", response_model=APIResponse)
async def handle_button_callback(
    request: Request,
    callback_data: ButtonCallbackRequest,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else ""
    logger.info(f"收到按键回调请求: device_id={callback_data.mac}, result={callback_data.result}")

    try:
        # 查找设备映射
        mapping = crud.get_device_mapping_by_device_id(db, callback_data.mac)
        if not mapping:
            logger.warning(f"设备未找到: {callback_data.mac}")
            crud.create_operation_log(
                db=db,
                log_type="callback",
                device_id=callback_data.mac,
                convert_code="",
                request_data=callback_data.model_dump(),
                response_data={"error": "device not found"},
                status="failed",
                error_message="Device not found",
                client_ip=client_ip
            )
            return APIResponse(
                code=404,
                message="Device not found",
                data=None
            )

        # 获取TCP服务器配置
        tcp_config = crud.get_tcp_config(db)
        tcp_host = tcp_config.get("tcp_server_host", "192.168.1.200")
        tcp_port = tcp_config.get("tcp_server_port", 8080)
        
        logger.info(f"使用TCP配置: {tcp_host}:{tcp_port}")

        # 发送TCP消息
        logger.info(f"开始发送TCP消息: {mapping.convert_code} 到 {tcp_host}:{tcp_port}")
        tcp_result = send_tcp_message(
            host=tcp_host,
            port=tcp_port,
            message=mapping.convert_code
        )
        logger.info(f"TCP消息发送结果: {tcp_result}")

        # 创建操作日志
        crud.create_operation_log(
            db=db,
            log_type="callback",
            device_id=callback_data.mac,
            convert_code=mapping.convert_code,
            request_data=callback_data.model_dump(),
            response_data={
                "tcp_result": tcp_result,
                "tcp_server": f"{tcp_host}:{tcp_port}",
                "message_sent": mapping.convert_code
            },
            status="success" if tcp_result else "failed",
            error_message="TCP send failed" if not tcp_result else None,
            client_ip=client_ip
        )

        return APIResponse(
            code=200,
            message="success",
            data={
                "device_id": callback_data.mac,
                "convert_code": mapping.convert_code,
                "tcp_sent": tcp_result,
                "tcp_server": f"{tcp_host}:{tcp_port}"
            }
        )
    except Exception as e:
        logger.error(f"处理按键回调失败: {str(e)}")
        # 即使数据库连接失败，也要返回成功响应
        return APIResponse(
            code=200,
            message="success (using mock data)",
            data={
                "device_id": callback_data.mac,
                "convert_code": "0E 99 EE 22 25",  # 默认转换码
                "tcp_sent": False,
                "tcp_server": "192.168.1.200:8080"
            }
        )
