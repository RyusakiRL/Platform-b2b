"""This module contains functions to process Excel files and insert data into the database."""

import shutil
from pathlib import Path
import pandas as pd
from pydantic import ValidationError
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_403_FORBIDDEN,
)
from schemas import InventoryRequiredColumns
from models.inventory import CurrentInventory, InventoryMovement, Product
from models.workforce import Account
from models.enums import MovementType, AccountRole

UPLOADS_FOLDER = Path("uploads")
UPLOADS_FOLDER.mkdir(exist_ok=True)


def process_inventory_excel(file: UploadFile, current_account: Account, db: Session):
    """Processes an uploaded Excel file and inserts product data into the database."""
    if current_account.role != AccountRole.MANAGER:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Access denied: only managers can upload inventory data.",
        )
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400, detail="Invalid file format. Use .xlsx or .xls"
        )

    file_path = UPLOADS_FOLDER / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:

        df = pd.read_excel(file_path)

        df = df.dropna(how="all")
        df = df.replace({pd.NA: None})
        records = df.to_dict(orient="records")

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
            p_quantity = valid_data.quantity
            p_datetime = valid_data.timestamp

            p_movement_type = valid_data.movement_type

            p_price = valid_data.price
            ware_id = valid_data.warehouse_id
            product = db.query(Product).filter_by(product_name=p_name).first()
            if not product:
                product = Product(
                    product_name=p_name,
                    base_price=p_price,
                )
                db.add(product)
                db.flush()
                added_products += 1
            inventory = (
                db.query(CurrentInventory)
                .filter_by(product_id=product.id, departments_id=ware_id)
                .first()
            )
            if not inventory:
                inventory = CurrentInventory(
                    product_id=product.id,
                    departments_id=ware_id,
                    product_in_stock=0,
                    product_to_come=0,
                )
                db.add(inventory)
                db.flush()

            if p_movement_type == MovementType.IN and p_quantity > 0:
                inventory.product_in_stock += p_quantity
                movement = InventoryMovement(
                    current_inventory_id=inventory.id,
                    movement_type=MovementType.IN,
                    quantity=p_quantity,
                    unit_price_at_transaction=p_price,
                    timestamp=p_datetime,
                )
                db.add(movement)
                movements_recorded += 1
            if p_movement_type == MovementType.OUT and p_quantity > 0:
                if inventory.product_in_stock < p_quantity:
                    spreadsheet_errors.append(
                        {
                            "excel_row": index,
                            "errors": f"Insufficient stock for product '{p_name}'",
                        }
                    )
                    continue
                inventory.product_in_stock -= p_quantity

                movement = InventoryMovement(
                    current_inventory_id=inventory.id,
                    movement_type=MovementType.OUT,
                    quantity=p_quantity,
                    unit_price_at_transaction=p_price,
                    timestamp=p_datetime,
                )
                db.add(movement)
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
