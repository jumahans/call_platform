from ninja import Router
from django.http import HttpRequest
from typing import List
from decimal import Decimal
from accounts.api import JWTAuth
from .schemas import (
    DepositSchema, UpdateBillingSchema,
    BillingAccountOutSchema, TransactionOutSchema,
    InvoiceOutSchema, MessageResponseSchema
)
from .services import BillingService

router = Router(tags=["Billing"], auth=JWTAuth())


@router.get("/account", response={200: BillingAccountOutSchema})
def get_account(request: HttpRequest):
    account = BillingService.get(request.auth)
    return 200, BillingService.format_account(account)


@router.patch("/account", response={200: BillingAccountOutSchema, 400: dict})
def update_account(request: HttpRequest, data: UpdateBillingSchema):
    try:
        account = BillingService.update(data, request.auth)
        return 200, BillingService.format_account(account)
    except ValueError as e:
        return 400, {"detail": str(e)}


@router.post("/deposit", response={200: dict, 400: dict})
def create_payment_intent(request: HttpRequest, data: DepositSchema):
    try:
        result = BillingService.create_stripe_payment_intent(
            data.amount, request.auth
        )
        return 200, result
    except ValueError as e:
        return 400, {"detail": str(e)}


@router.post("/deposit/confirm", response={200: dict, 400: dict})
def confirm_deposit(request: HttpRequest, data: DepositSchema):
    try:
        tx = BillingService.deposit(
            data.amount,
            request.auth,
            payment_method_id=data.payment_method_id
        )
        return 200, {
            'message': f"${data.amount} deposited successfully",
            'balance': str(tx.balance_after),
            'transaction_id': str(tx.id),
        }
    except ValueError as e:
        return 400, {"detail": str(e)}


@router.get("/transactions", response={200: List[TransactionOutSchema]})
def list_transactions(request: HttpRequest):
    transactions = BillingService.list_transactions(request.auth)
    return 200, [
        {
            'id': str(t.id),
            'transaction_type': t.transaction_type,
            'amount': t.amount,
            'balance_before': t.balance_before,
            'balance_after': t.balance_after,
            'description': t.description,
            'reference_id': t.reference_id,
            'call_sid': t.call_sid,
            'campaign_name': t.campaign_name,
            'buyer_name': t.buyer_name,
            'publisher_name': t.publisher_name,
            'status': t.status,
            'created_at': t.created_at.isoformat(),
        }
        for t in transactions
    ]


@router.get("/invoices", response={200: List[InvoiceOutSchema]})
def list_invoices(request: HttpRequest):
    invoices = BillingService.list_invoices(request.auth)
    return 200, [
        {
            'id': str(i.id),
            'invoice_number': i.invoice_number,
            'period_start': i.period_start.isoformat(),
            'period_end': i.period_end.isoformat(),
            'total_calls': i.total_calls,
            'total_revenue': i.total_revenue,
            'total_payout': i.total_payout,
            'total_amount': i.total_amount,
            'status': i.status,
            'paid_at': i.paid_at.isoformat() if i.paid_at else None,
            'created_at': i.created_at.isoformat(),
        }
        for i in invoices
    ]



@router.post("/payment-methods", response={200: dict, 400: dict})
def save_payment_method(request: HttpRequest, payment_method_id: str):
    try:
        result = BillingService.save_payment_method(payment_method_id, request.auth)
        return 200, result
    except ValueError as e:
        return 400, {"detail": str(e)}


@router.get("/payment-methods", response={200: list})
def list_payment_methods(request: HttpRequest):
    try:
        methods = BillingService.list_payment_methods(request.auth)
        return 200, methods
    except ValueError as e:
        return 400, {"detail": str(e)}


@router.delete("/payment-methods/{payment_method_id}", response={200: dict, 400: dict})
def delete_payment_method(request: HttpRequest, payment_method_id: str):
    try:
        BillingService.delete_payment_method(payment_method_id, request.auth)
        return 200, {"message": "Payment method removed", "success": True}
    except ValueError as e:
        return 400, {"detail": str(e)}


@router.post("/stripe-webhook", auth=None, response={200: dict})
def stripe_webhook(request: HttpRequest):
    import stripe
    from django.conf import settings
    stripe.api_key = settings.STRIPE_SECRET_KEY

    payload = request.body
    sig_header = request.headers.get('Stripe-Signature', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        return 200, {"status": "ignored"}

    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        organization_id = intent.get('metadata', {}).get('organization_id')
        amount = Decimal(intent['amount']) / 100

        if organization_id:
            try:
                from accounts.models import Organization
                org = Organization.objects.get(id=organization_id)
                account = BillingAccount.objects.get(organization=org)
                user = org.members.filter(role='admin').first()
                if user:
                    BillingService.deposit(
                        amount=amount,
                        user=user,
                        stripe_payment_intent_id=intent['id']
                    )
            except Exception:
                pass

    return 200, {"status": "ok"}