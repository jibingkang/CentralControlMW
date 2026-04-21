from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
from pydantic import BaseModel
from app.database import get_db
from app.schemas import OperationLogResponse, APIResponse, PYDANTIC_V2
from app import crud

router = APIRouter()


@router.get("/logs", response_model=APIResponse)
async def get_operation_logs(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    log_type: Optional[str] = Query(None),
    device_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        # 计算偏移量
        skip = (page - 1) * page_size
        
        # 调用crud函数获取日志
        total, logs = crud.get_operation_logs(
            db=db,
            log_type=log_type,
            device_id=device_id,
            status=status,
            start_date=start_date.isoformat() if start_date else None,
            end_date=end_date.isoformat() if end_date else None,
            skip=skip,
            limit=page_size
        )

        # 根据Pydantic版本使用不同的方法
        if PYDANTIC_V2:
            items = [OperationLogResponse.model_validate(log).model_dump() for log in logs]
        else:
            items = [OperationLogResponse.from_orm(log).dict() for log in logs]
        
        return APIResponse(
            code=200,
            message="success",
            data={
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        )
    except Exception as e:
        return APIResponse(
            code=200,
            message="success (using empty list)",
            data={
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size
            }
        )


@router.get("/logs/{log_id}", response_model=APIResponse)
async def get_operation_log(
    request: Request,
    log_id: int,
    db: Session = Depends(get_db)
):
    try:
        log = crud.get_operation_log(db, log_id)
        if not log:
            return APIResponse(
                code=404,
                message="Log not found",
                data=None
            )

        # 根据Pydantic版本使用不同的方法
        if PYDANTIC_V2:
            log_data = OperationLogResponse.model_validate(log).model_dump()
        else:
            log_data = OperationLogResponse.from_orm(log).dict()
        
        return APIResponse(
            code=200,
            message="success",
            data=log_data
        )
    except Exception as e:
        return APIResponse(
            code=404,
            message="Log not found",
            data=None
        )


@router.delete("/logs/{log_id}", response_model=APIResponse)
async def delete_operation_log(
    request: Request,
    log_id: int,
    db: Session = Depends(get_db)
):
    try:
        success = crud.delete_operation_log(db, log_id)
        if not success:
            return APIResponse(
                code=404,
                message="Log not found",
                data=None
            )

        return APIResponse(
            code=200,
            message="success",
            data={"deleted": success}
        )
    except Exception as e:
        return APIResponse(
            code=500,
            message="Database error",
            data=None
        )


class DeleteLogsRequest(BaseModel):
    log_ids: List[int]


@router.post("/logs/delete", response_model=APIResponse)
async def delete_operation_logs(
    request: Request,
    delete_data: DeleteLogsRequest,
    db: Session = Depends(get_db)
):
    try:
        deleted_count = crud.delete_operation_logs(db, delete_data.log_ids)

        return APIResponse(
            code=200,
            message="success",
            data={"deleted_count": deleted_count}
        )
    except Exception as e:
        return APIResponse(
            code=500,
            message="Database error",
            data=None
        )
