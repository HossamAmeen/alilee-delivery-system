from orders.models import Order
from transactions.models import TransactionType, UserAccountTransaction


def create_transaction(user_id, amount, transaction_type, order_id, notes=""):
    UserAccountTransaction.objects.create(
        user_account_id=user_id,
        amount=amount,
        transaction_type=transaction_type,
        notes=notes,
        order_id=order_id,
    )


def roll_back_order_transactions(ids):
    transactions = UserAccountTransaction.objects.filter(
        id__in=ids, is_rolled_back=False
    )
    for transaction in transactions:
        transaction.is_rolled_back = True
        transaction.notes = transaction.notes + " (استرجاع)"
        transaction.save()
        if transaction.transaction_type == TransactionType.WITHDRAW:
            UserAccountTransaction.objects.create(
                user_account_id=transaction.user_account_id,
                amount=transaction.amount,
                transaction_type=TransactionType.DEPOSIT,
                notes="مبلغ مسترجع الخاص بالطلب رقم "
                + transaction.order.tracking_number,
                order_id=transaction.order_id,
            )
        elif transaction.transaction_type == TransactionType.DEPOSIT:
            UserAccountTransaction.objects.create(
                user_account_id=transaction.user_account_id,
                amount=transaction.amount,
                transaction_type=TransactionType.WITHDRAW,
                notes="مبلغ مسترجع الخاص بالطلب رقم "
                + transaction.order.tracking_number,
                order_id=transaction.order_id,
            )


def create_order_transaction(user_id, amount, transaction_type, order_id, notes=""):
    already_exists = UserAccountTransaction.objects.filter(
        order_id=order_id,
        transaction_type=transaction_type,
        user_account_id=user_id,
        is_rolled_back=False,
    ).exists()
    if already_exists:
        return

    order = Order.objects.filter(id=order_id).first()

    if not order:
        return

    if order.postpone_count > 1:
        return

    create_transaction(
        user_id=user_id,
        amount=amount,
        transaction_type=transaction_type,
        order_id=order_id,
        notes=notes,
    )
