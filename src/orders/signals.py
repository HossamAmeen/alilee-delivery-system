from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Order, OrderStatus
from transactions.models import TransactionType, UserAccountTransaction


@receiver(post_save, sender=Order)
def create_driver_withdraw_transaction(sender, instance, created, **kwargs):
    if not created and instance.status == "delivered" and instance.driver:
        total_withdraw = instance.delivery_cost + instance.extra_delivery_cost

        already_exists = UserAccountTransaction.objects.filter(
            user_account=instance.driver,
            amount=total_withdraw,
            transaction_type=TransactionType.WITHDRAW,
            created__date=instance.modified.date(),
        ).exists()
        if already_exists:
            return

        UserAccountTransaction.objects.create(
            user_account=instance.driver,
            amount=total_withdraw,
            transaction_type=TransactionType.WITHDRAW,
        )
