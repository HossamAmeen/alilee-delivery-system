from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404

from transactions.models import TransactionType, UserAccountTransaction
from users.models import UserAccount, Trader, Driver


# Office transfer amount to trader
@receiver(post_save, sender=UserAccountTransaction)
def update_trader_balance_for_deposit_transaction(sender, instance, created, **kwargs):
    if (created and instance.transaction_type == TransactionType.DEPOSIT and
            instance.user_account.role == UserAccount.Role.TRADER):
        total_deposit = instance.amount

        trader = get_object_or_404(Trader, pk=instance.user_account)
        trader.balance -= total_deposit
        trader.save()


# Trader transfer amount to office
@receiver(post_save, sender=UserAccountTransaction)
def update_trader_balance_for_withdraw_transaction(sender, instance, created, **kwargs):
    if (created and instance.transaction_type == TransactionType.WITHDRAW and
            instance.user_account.role == UserAccount.Role.TRADER):
        total_withdraw = instance.amount

        trader = get_object_or_404(Trader, pk=instance.user_account)
        trader.balance += total_withdraw
        trader.save()


# Office transfer amount to driver
@receiver(post_save, sender=UserAccountTransaction)
def update_driver_balance_for_deposit_transaction(sender, instance, created, **kwargs):
    if (created and instance.transaction_type == TransactionType.DEPOSIT and
            instance.user_account.role == UserAccount.Role.DRIVER):
        total_deposit = instance.amount

        driver = get_object_or_404(Driver, pk=instance.user_account)
        driver.balance -= total_deposit
        driver.save()


# Driver transfer amount to office
@receiver(post_save, sender=UserAccountTransaction)
def update_driver_balance_for_withdraw_transaction(sender, instance, created, **kwargs):
    if (created and instance.transaction_type == TransactionType.WITHDRAW and
            instance.user_account.role == UserAccount.Role.DRIVER):
        total_withdraw = instance.amount

        driver = get_object_or_404(Driver, pk=instance.user_account)
        driver.balance += total_withdraw
        driver.save()
