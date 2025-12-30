from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.service import send_notification
from transactions.models import Expense, TransactionType, UserAccountTransaction


@receiver(post_save, sender=UserAccountTransaction)
def update_user_account_balance_for_transaction(sender, instance, created, **kwargs):
    if created:
        if instance.transaction_type == TransactionType.WITHDRAW:
            instance.user_account.update_balance(instance.amount)
        elif instance.transaction_type == TransactionType.DEPOSIT:
            instance.user_account.update_balance(-instance.amount)
        elif instance.transaction_type == TransactionType.EXPENSE:
            instance.user_account.update_balance(-instance.amount)


@receiver(post_save, sender=UserAccountTransaction)
def create_expense(sender, instance, created, **kwargs):
    if created:
        if instance.transaction_type == TransactionType.EXPENSE:
            Expense.objects.create(
                description=instance.notes,
                date=instance.created,
                cost=instance.amount,
            )


@receiver(post_save, sender=UserAccountTransaction)
def send_notification_after_transaction(sender, instance, created, **kwargs):
    if created:
        if instance.transaction_type == TransactionType.WITHDRAW:
            description = f"تم سحب {instance.amount} من حسابك"
            title = "سحب من حسابك"
        elif instance.transaction_type == TransactionType.DEPOSIT:
            description = f"تم إيداع {instance.amount} إلى حسابك"
            title = "إيداع إلى حسابك"
        elif instance.transaction_type == TransactionType.EXPENSE:
            description = f"تم إيداع {instance.amount} إلى حسابك"
            title = "إيداع إلى حسابك"
        send_notification(instance.user_account_id, title, description)
