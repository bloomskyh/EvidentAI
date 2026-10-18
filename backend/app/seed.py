from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from .models import (
    BankTransaction, BankDisputeRule, StoreOrder, StorePayment,
    StoreRefund, StoreMessage
)

def seed_database(db: Session):
    # Only seed if bank_transactions is empty
    if db.query(BankTransaction).first():
        return

    now = datetime.now(timezone.utc)

    # 1. Bank Dispute Rules (Configurable per currency/bank)
    rules_inr = BankDisputeRule(
        id="RULE-INR-STANDARD",
        currency="INR",
        dispute_window_days=60,
        require_merchant_contact=True,
        requires_written_explanation=True,
        allowed_reasons=[
            "PRODUCT_NOT_RECEIVED",
            "DUPLICATE_CHARGE",
            "INCORRECT_AMOUNT",
            "SUSPECTED_FRAUD"
        ]
    )
    db.add(rules_inr)

    # -------------------------------------------------------------
    # SCENARIOS SETUP
    # -------------------------------------------------------------

    # TC1: Disputed Charge (Product Not Received - genuine case)
    # Transaction 12 days ago, store order exists, undelivered, merchant ticket acknowledges shipping delay
    tc1_date = now - timedelta(days=12)
    txn_tc1 = BankTransaction(
        id="TXN-IND-1001",
        account_number="AC-9874563210",
        card_last4="4242",
        order_id="ORD-IND-9001",
        merchant_name="ApexRetail India",
        amount=4999.00,
        currency="INR",
        transaction_date=tc1_date,
        posted_date=tc1_date + timedelta(days=1),
        status="SETTLED",
        refund_status="NONE",
        description="ApexRetail - Noise Cancelling Headphones",
        has_provisional_credit=False,
        provisional_credit_amount=0.0
    )
    ord_tc1 = StoreOrder(
        id="ORD-IND-9001",
        customer_email="rahul.sharma@example.com",
        customer_name="Rahul Sharma",
        order_date=tc1_date,
        amount=4999.00,
        currency="INR",
        fulfillment_status="UNFULFILLED",
        tracking_number="TRK-BLUEDART-882190",
        items_summary="1x UltraBass Pro ANC Wireless Headphones",
        linked_transaction_id="TXN-IND-1001"
    )
    pay_tc1 = StorePayment(
        id="PAY-IND-8001",
        order_id="ORD-IND-9001",
        transaction_id="TXN-IND-1001",
        amount=4999.00,
        currency="INR",
        payment_method="CREDIT_CARD",
        payment_status="CAPTURED"
    )
    msg_tc1 = StoreMessage(
        id="MSG-IND-5001",
        order_id="ORD-IND-9001",
        sender="MERCHANT",
        timestamp=now - timedelta(days=8),
        subject="Shipment Delay Notice",
        message_body="Dear Rahul, your package TRK-BLUEDART-882190 has been stuck at the warehouse due to courier logistics failure. We sincerely apologize.",
        channel="EMAIL"
    )
    db.add_all([txn_tc1, ord_tc1, pay_tc1, msg_tc1])

    # TC2: Already Refunded (Merchant issued full refund)
    tc2_date = now - timedelta(days=20)
    txn_tc2 = BankTransaction(
        id="TXN-IND-1002",
        account_number="AC-9874563210",
        card_last4="4242",
        order_id="ORD-IND-9002",
        merchant_name="Cloudmart Gadgets",
        amount=2499.00,
        currency="INR",
        transaction_date=tc2_date,
        posted_date=tc2_date + timedelta(days=1),
        status="SETTLED",
        refund_status="FULL",
        description="Cloudmart - Ergonomic Keyboard",
        has_provisional_credit=False,
        provisional_credit_amount=0.0
    )
    ord_tc2 = StoreOrder(
        id="ORD-IND-9002",
        customer_email="rahul.sharma@example.com",
        customer_name="Rahul Sharma",
        order_date=tc2_date,
        amount=2499.00,
        currency="INR",
        fulfillment_status="CANCELLED",
        items_summary="1x Ergonomic Mechanical Keyboard",
        linked_transaction_id="TXN-IND-1002"
    )
    pay_tc2 = StorePayment(
        id="PAY-IND-8002",
        order_id="ORD-IND-9002",
        transaction_id="TXN-IND-1002",
        amount=2499.00,
        currency="INR",
        payment_method="CREDIT_CARD",
        payment_status="REFUNDED"
    )
    ref_tc2 = StoreRefund(
        id="REF-IND-3002",
        order_id="ORD-IND-9002",
        transaction_id="TXN-IND-1002",
        amount=2499.00,
        currency="INR",
        refund_date=now - timedelta(days=15),
        reason="Order cancelled by buyer prior to dispatch",
        status="COMPLETED",
        reference_number="REF-BANK-ARN-778899"
    )
    msg_tc2 = StoreMessage(
        id="MSG-IND-5002",
        order_id="ORD-IND-9002",
        sender="SUPPORT",
        timestamp=now - timedelta(days=15),
        subject="Refund Confirmation: ORD-IND-9002",
        message_body="Your refund of ₹2499.00 has been credited back to your original payment card ending in 4242. ARN: REF-BANK-ARN-778899.",
        channel="EMAIL"
    )
    db.add_all([txn_tc2, ord_tc2, pay_tc2, ref_tc2, msg_tc2])

    # TC3: Fraud Claim Without Evidence (User claims stolen card, but 3DS OTP was verified and IP was regular home address)
    tc3_date = now - timedelta(days=5)
    txn_tc3 = BankTransaction(
        id="TXN-IND-1003",
        account_number="AC-9874563210",
        card_last4="4242",
        order_id="ORD-IND-9003",
        merchant_name="VogueIndia Apparels",
        amount=8999.00,
        currency="INR",
        transaction_date=tc3_date,
        posted_date=tc3_date + timedelta(days=1),
        status="SETTLED",
        refund_status="NONE",
        description="VogueIndia - Designer Silk Saree",
        has_provisional_credit=False,
        provisional_credit_amount=0.0
    )
    ord_tc3 = StoreOrder(
        id="ORD-IND-9003",
        customer_email="rahul.sharma@example.com",
        customer_name="Rahul Sharma",
        order_date=tc3_date,
        amount=8999.00,
        currency="INR",
        fulfillment_status="DELIVERED",
        delivery_date=tc3_date + timedelta(days=3),
        tracking_number="TRK-DELHIVERY-994411",
        items_summary="1x Embroidered Silk Ethnic Wear",
        linked_transaction_id="TXN-IND-1003"
    )
    pay_tc3 = StorePayment(
        id="PAY-IND-8003",
        order_id="ORD-IND-9003",
        transaction_id="TXN-IND-1003",
        amount=8999.00,
        currency="INR",
        payment_method="CREDIT_CARD",
        payment_status="CAPTURED"
    )
    # Note: No police report, no fraudulent IP log, no device mismatch record.
    db.add_all([txn_tc3, ord_tc3, pay_tc3])

    # TC4: Provisional Credit (Bank granted interim credit pending dispute investigation)
    tc4_date = now - timedelta(days=25)
    txn_tc4 = BankTransaction(
        id="TXN-IND-1004",
        account_number="AC-9874563210",
        card_last4="4242",
        order_id="ORD-IND-9004",
        merchant_name="ElectroTech Superstore",
        amount=15499.00,
        currency="INR",
        transaction_date=tc4_date,
        posted_date=tc4_date + timedelta(days=1),
        status="SETTLED",
        refund_status="NONE",
        description="ElectroTech - 4K Monitor",
        has_provisional_credit=True,
        provisional_credit_amount=15499.00,
        provisional_credit_date=now - timedelta(days=10)
    )
    ord_tc4 = StoreOrder(
        id="ORD-IND-9004",
        customer_email="rahul.sharma@example.com",
        customer_name="Rahul Sharma",
        order_date=tc4_date,
        amount=15499.00,
        currency="INR",
        fulfillment_status="TRANSIT",
        tracking_number="TRK-EKART-110022",
        items_summary="1x 27-inch 4K IPS Gaming Display",
        linked_transaction_id="TXN-IND-1004"
    )
    pay_tc4 = StorePayment(
        id="PAY-IND-8004",
        order_id="ORD-IND-9004",
        transaction_id="TXN-IND-1004",
        amount=15499.00,
        currency="INR",
        payment_method="CREDIT_CARD",
        payment_status="CAPTURED"
    )
    msg_tc4 = StoreMessage(
        id="MSG-IND-5004",
        order_id="ORD-IND-9004",
        sender="MERCHANT",
        timestamp=now - timedelta(days=18),
        subject="Shipment Lost in Transit Inquiry",
        message_body="Courier partner reports cargo container damaged. Investigation ticket #TK-88712 opened.",
        channel="TICKET"
    )
    db.add_all([txn_tc4, ord_tc4, pay_tc4, msg_tc4])

    # Additional Realistic Records:
    # 5. Expired Dispute Window Transaction (> 60 days)
    tc5_date = now - timedelta(days=95)
    txn_expired = BankTransaction(
        id="TXN-IND-1005",
        account_number="AC-9874563210",
        card_last4="4242",
        order_id="ORD-IND-9005",
        merchant_name="OldBook Emporium",
        amount=1200.00,
        currency="INR",
        transaction_date=tc5_date,
        posted_date=tc5_date + timedelta(days=1),
        status="SETTLED",
        refund_status="NONE",
        description="OldBook Emporium - Antique Encyclopedia",
        has_provisional_credit=False,
        provisional_credit_amount=0.0
    )
    ord_expired = StoreOrder(
        id="ORD-IND-9005",
        customer_email="rahul.sharma@example.com",
        customer_name="Rahul Sharma",
        order_date=tc5_date,
        amount=1200.00,
        currency="INR",
        fulfillment_status="DELIVERED",
        items_summary="Rare Vintage Volume 1",
        linked_transaction_id="TXN-IND-1005"
    )
    db.add_all([txn_expired, ord_expired])

    # 6. Duplicate charge scenario
    tc6_date = now - timedelta(days=4)
    txn_dup = BankTransaction(
        id="TXN-IND-1006",
        account_number="AC-9874563210",
        card_last4="4242",
        order_id="ORD-IND-9006",
        merchant_name="Zomato Foods",
        amount=750.00,
        currency="INR",
        transaction_date=tc6_date,
        posted_date=tc6_date,
        status="SETTLED",
        refund_status="NONE",
        description="Zomato - Gourmet Kitchen (Duplicate Billing)",
        has_provisional_credit=False,
        provisional_credit_amount=0.0
    )
    ord_dup = StoreOrder(
        id="ORD-IND-9006",
        customer_email="rahul.sharma@example.com",
        customer_name="Rahul Sharma",
        order_date=tc6_date,
        amount=750.00,
        currency="INR",
        fulfillment_status="DELIVERED",
        items_summary="Dinner combo delivery",
        linked_transaction_id="TXN-IND-1006"
    )
    msg_dup = StoreMessage(
        id="MSG-IND-5006",
        order_id="ORD-IND-9006",
        sender="CUSTOMER",
        timestamp=tc6_date + timedelta(hours=1),
        subject="Charged twice for single order",
        message_body="I observed two identical charges of ₹750.00 for order #9006 on my statement.",
        channel="CHAT"
    )
    db.add_all([txn_dup, ord_dup, msg_dup])

    db.commit()
