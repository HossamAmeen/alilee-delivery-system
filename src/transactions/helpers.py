from transactions.models import UserAccountTransaction


def create_transaction(user_id, amount, transaction_type, order_id, notes=""):
    UserAccountTransaction.objects.create(
        user_account_id=user_id,
        amount=amount,
        transaction_type=transaction_type,
        notes=notes,
        order_id=order_id,
    )


def roll_back_order_transactions(order_id):
    transactions = UserAccountTransaction.objects.filter(order_id=order_id)
    for transaction in transactions:
        transaction.is_rolled_back = True
        transaction.save()

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
