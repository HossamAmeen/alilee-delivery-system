from django.db.models.signals import post_save
from django.dispatch import receiver

from transactions.models import TransactionType, UserAccountTransaction


@receiver(post_save, sender=UserAccountTransaction)
def update_user_account_balance_for_transaction(sender, instance, created, **kwargs):
    if created:
        if instance.transaction_type == TransactionType.WITHDRAW:
            instance.user_account.update_balance(-instance.amount)
        elif instance.transaction_type == TransactionType.DEPOSIT:
            instance.user_account.update_balance(instance.amount)

        instance.user_account.save()
