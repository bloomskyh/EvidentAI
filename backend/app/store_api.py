from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .database import get_db
from .models import (
    StoreOrder, StorePayment, StoreRefund, StoreMessage
)
from .schemas import (
    StoreOrderSchema, StoreRefundSchema, StoreMessageSchema
)

router = APIRouter(prefix="/api/mock-store", tags=["Mock Store Service"])

@router.get("/orders", response_model=List[StoreOrderSchema])
def list_store_orders(db: Session = Depends(get_db)):
    """List orders registered in store commerce system."""
    return db.query(StoreOrder).order_by(StoreOrder.order_date.desc()).all()

@router.get("/orders/{order_id}", response_model=StoreOrderSchema)
def get_store_order(order_id: str, db: Session = Depends(get_db)):
    """Retrieve detailed store order information."""
    order = db.query(StoreOrder).filter(StoreOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store order '{order_id}' not found in merchant order management."
        )
    return order

@router.get("/orders/by-transaction/{transaction_id}", response_model=StoreOrderSchema)
def get_order_by_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """Find store order matching a given payment gateway transaction ID."""
    order = db.query(StoreOrder).filter(StoreOrder.linked_transaction_id == transaction_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No store order found associated with transaction '{transaction_id}'."
        )
    return order

@router.get("/refunds", response_model=List[StoreRefundSchema])
def list_refunds(transaction_id: Optional[str] = None, order_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Retrieve refunds matching transaction or order."""
    query = db.query(StoreRefund)
    if transaction_id:
        query = query.filter(StoreRefund.transaction_id == transaction_id)
    if order_id:
        query = query.filter(StoreRefund.order_id == order_id)
    return query.all()

@router.get("/messages", response_model=List[StoreMessageSchema])
def list_messages(order_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Retrieve merchant-customer communication records."""
    query = db.query(StoreMessage)
    if order_id:
        query = query.filter(StoreMessage.order_id == order_id)
    return query.order_by(StoreMessage.timestamp.asc()).all()
