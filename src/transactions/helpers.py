from transactions.models import UserAccountTransaction


def create_transaction(user, amount, transaction_type, order_id, notes=""):
    UserAccountTransaction.objects.create(
        user_account=user,
        amount=amount,
        transaction_type=transaction_type,
        notes=notes,
        order_id=order_id,
    )


def create_order_transaction(user, amount, transaction_type, tracking_number, order_id):
    already_exists = UserAccountTransaction.objects.filter(
        notes__contains=f"{transaction_type} + {tracking_number}", user_account=user
    ).exists()
    if already_exists:
        return

    create_transaction(
        user=user,
        amount=amount,
        transaction_type=transaction_type,
        order_id=order_id,
        notes=f"{transaction_type} + {tracking_number}",
    )
