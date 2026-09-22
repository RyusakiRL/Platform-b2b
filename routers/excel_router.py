"""Router for handling Excel file uploads and processing."""

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from models.workforce import Account
from dependencies import get_current_account
from services.excel_service import process_inventory_excel

router = APIRouter(prefix="/excel", tags=["Data Import"])


@router.post("/upload/inventory")
def upload_excel(
    current_account: Account = Depends(get_current_account),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Endpoint for importing inventory data from an Excel file. Only managers can perform this action."""
    return process_inventory_excel(file=file, current_account=current_account, db=db)
