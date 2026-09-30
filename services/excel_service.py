"""This module contains functions to process Excel files and insert data into the database."""

from pathlib import Path
import pandas as pd
from pydantic import ValidationError
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
)
from schemas import InventoryRequiredColumns
from models.inventory import Product, Warehouse
from models.workforce import Account
from models.enums import MovementType, AccountRole
from services.inventory_service import apply_inventory_movement


def process_inventory_excel(file: UploadFile, current_account: Account, db: Session):
    """Processes an uploaded Excel file and inserts product data into the database."""
    if current_account.role != AccountRole.MANAGER:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Access denied: only managers can upload inventory data.",
        )

    filename = Path(file.filename or "")
    extension = filename.suffix.lower()
    if extension != ".xlsx":
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Invalid file format. Use .xlsx"
        )

    try:
        file.file.seek(0)
        df = pd.read_excel(file.file)
    except (ValueError, ImportError) as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Invalid or corrupted Excel file.",
        ) from exc
    df = df.dropna(how="all")
    df = df.replace({pd.NA: None})
    records = df.to_dict(orient="records")
    try:
        added_products = 0
        movements_recorded = 0
        spreadsheet_errors = []
        for index, row in enumerate(
            records, start=2
        ):  # Start at 2 to account for header row
            try:
                valid_data = InventoryRequiredColumns(**row)
            except ValidationError as e:
                spreadsheet_errors.append({"excel_row": index, "errors": e.errors()})
                continue

            p_name = valid_data.name
            p_sku = valid_data.sku
            p_quantity = valid_data.quantity
            p_datetime = valid_data.timestamp
            p_movement_type = valid_data.movement_type
            p_price = valid_data.price
            ware_id = valid_data.warehouse_id

            product = db.query(Product).filter_by(sku=p_sku).first()
            warehouse = db.query(Warehouse).filter_by(id=ware_id).first()
            if not warehouse or not warehouse.is_active:
                spreadsheet_errors.append(
                    {
                        "excel_row": index,
                        "errors": f"Active warehouse with ID {ware_id} was not found.",
                    }
                )
                continue
            if not product and p_movement_type == MovementType.OUT:
                spreadsheet_errors.append(
                    {
                        "excel_row": index,
                        "errors": f"Product with SKU '{p_sku}' was not found.",
                    }
                )
                continue
            if product and not product.is_active:
                spreadsheet_errors.append(
                    {
                        "excel_row": index,
                        "errors": f"Product with SKU '{p_sku}' is inactive.",
                    }
                )
                continue
            if not product and p_movement_type == MovementType.IN:
                product = Product(
                    product_name=p_name,
                    sku=p_sku,
                    base_price=p_price,
                )
                db.add(product)
                db.flush()
                added_products += 1
            try:
                apply_inventory_movement(
                    product_id=product.id,
                    warehouse_id=ware_id,
                    account_id=current_account.id,
                    movement_type=p_movement_type,
                    quantity=p_quantity,
                    unit_price=p_price,
                    timestamp=p_datetime,
                    db=db,
                )
            except HTTPException as exc:
                spreadsheet_errors.append(
                    {
                        "excel_row": index,
                        "errors": exc.detail,
                    }
                )
                continue
            else:
                movements_recorded += 1
        db.commit()
        return {
            "message": "Upload, inventory update and auditing completed successfully!",
            "rows_processed": len(records),
            "new_products_cataloged": added_products,
            "inventory_movements_recorded": movements_recorded,
            "error_found": spreadsheet_errors,
        }

    except Exception:
        db.rollback()
        raise
