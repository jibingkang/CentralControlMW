from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas import DeviceMappingCreate, DeviceMappingUpdate, DeviceMappingResponse, APIResponse
from app import crud
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/mappings", response_model=APIResponse)
async def get_mappings(
    device_id: Optional[str] = Query(None),
    convert_code: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        mappings = crud.get_device_mappings(db, device_id=device_id, convert_code=convert_code)
        return APIResponse(
            code=200,
            message="success",
            data={"items": [DeviceMappingResponse.model_validate(m).model_dump() for m in mappings]}
        )
    except Exception as e:
        logger.error(f"获取设备映射失败: {str(e)}")
        return APIResponse(
            code=200,
            message="success (using empty list)",
            data={"items": []}
        )


@router.post("/mapping", response_model=APIResponse)
async def create_mapping(
    request: Request,
    mapping_data: DeviceMappingCreate,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else ""

    try:
        logger.info(f"开始创建设备映射: {mapping_data.device_id}")

        # 检查是否已存在
        existing = crud.get_device_mapping_by_device_id(db, mapping_data.device_id)
        if existing:
            logger.warning(f"设备ID已存在: {mapping_data.device_id}")
            return APIResponse(
                code=400,
                message="Device ID already exists",
                data=None
            )

        # 创建映射
        mapping = crud.create_device_mapping(db, mapping_data)
        logger.info(f"设备映射创建成功: {mapping.id}")

        return APIResponse(
            code=200,
            message="success",
            data=DeviceMappingResponse.model_validate(mapping).model_dump()
        )
    except Exception as e:
        logger.error(f"创建设备映射失败: {str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return APIResponse(
            code=500,
            message=f"Database error: {str(e)}",
            data=None
        )


@router.put("/mapping/{mapping_id}", response_model=APIResponse)
async def update_mapping(
    request: Request,
    mapping_id: int,
    mapping_data: DeviceMappingUpdate,
    db: Session = Depends(get_db)
):
    try:
        existing = crud.get_device_mapping(db, mapping_id)
        if not existing:
            return APIResponse(
                code=404,
                message="Mapping not found",
                data=None
            )

        mapping = crud.update_device_mapping(db, mapping_id, mapping_data)

        return APIResponse(
            code=200,
            message="success",
            data=DeviceMappingResponse.model_validate(mapping).model_dump() if mapping else None
        )
    except Exception as e:
        logger.error(f"更新设备映射失败: {str(e)}")
        return APIResponse(
            code=500,
            message="Database error",
            data=None
        )


@router.delete("/mapping/{mapping_id}", response_model=APIResponse)
async def delete_mapping(
    request: Request,
    mapping_id: int,
    db: Session = Depends(get_db)
):
    try:
        existing = crud.get_device_mapping(db, mapping_id)
        if not existing:
            return APIResponse(
                code=404,
                message="Mapping not found",
                data=None
            )

        success = crud.delete_device_mapping(db, mapping_id)

        return APIResponse(
            code=200,
            message="success" if success else "failed",
            data={"deleted": success}
        )
    except Exception as e:
        logger.error(f"删除设备映射失败: {str(e)}")
        return APIResponse(
            code=500,
            message="Database error",
            data=None
        )
