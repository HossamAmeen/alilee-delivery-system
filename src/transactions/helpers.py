from transactions.models import UserAccountTransaction


def create_transaction(user_id, amount, transaction_type, order_id, notes=""):
    UserAccountTransaction.objects.create(
        user_account_id=user_id,
        amount=amount,
        transaction_type=transaction_type,
        notes=notes,
        order_id=order_id,
    )


def roll_back_transactions(transaction_ids):
    transactions = UserAccountTransaction.objects.filter(id__in=transaction_ids)
    transactions.update(is_rolled_back=True)

def create_order_transaction(user_id, amount, transaction_type, order_id, notes=""):
    already_exists = UserAccountTransaction.objects.filter(order_id=order_id).exists()
    if already_exists:
        return

    create_transaction(
        user_id=user_id,
        amount=amount,
        transaction_type=transaction_type,
        order_id=order_id,
        notes=notes
    )
