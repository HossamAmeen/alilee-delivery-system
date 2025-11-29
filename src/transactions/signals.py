from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404

from transactions.models import TransactionType, UserAccountTransaction


@receiver(post_save, sender=UserAccountTransaction)
def update_user_account_balance_for_transaction(sender, instance, created, **kwargs):
    if created:
        user_account = get_object_or_404(instance.user_account.get_user_account_role(), pk=instance.user_account)
        if instance.transaction_type == TransactionType.WITHDRAW:
            user_account.balance -= instance.amount
        elif instance.transaction_type == TransactionType.DEPOSIT:
            user_account.balance += instance.amount

        user_account.save()
