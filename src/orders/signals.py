from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Order, OrderStatus, ProductPaymentStatus
from transactions.models import TransactionType, UserAccountTransaction


# Make trader transaction, order paid, office will take delivery cost from trader
@receiver(post_save, sender=Order)
def delivered_order_withdraw_transaction_from_trader(
    sender, instance, created, **kwargs
):
    if (
        not created
        and instance.trader
        and instance.status == OrderStatus.DELIVERED
        and instance.product_payment_status == ProductPaymentStatus.PAID
    ):
        total_withdraw = instance.trader_merchant_cost

        already_exists = UserAccountTransaction.objects.filter(
            notes__contains=instance.tracking_number,
            user_account=instance.trader
        ).exists()
        if already_exists:
            return

        UserAccountTransaction.objects.create(
            user_account=instance.trader,
            amount=total_withdraw,
            transaction_type=TransactionType.WITHDRAW,
            notes=instance.tracking_number,
        )


# Make trader transaction, order cancelled, office will take trader_merchant_cost from trader
@receiver(post_save, sender=Order)
def cancelled_order_withdraw_transaction_from_trader(
    sender, instance, created, **kwargs
):
    if not created and instance.trader and instance.status == OrderStatus.CANCELLED:
        total_withdraw = instance.trader_merchant_cost

        already_exists = UserAccountTransaction.objects.filter(
            notes__contains=instance.tracking_number,
            user_account=instance.trader
        ).exists()
        if already_exists:
            return

        UserAccountTransaction.objects.create(
            user_account=instance.trader,
            amount=total_withdraw,
            transaction_type=TransactionType.WITHDRAW,
            notes=instance.tracking_number,
        )


# Make trader transaction, order COD, office will transfer product cost to trader
@receiver(post_save, sender=Order)
def delivered_order_deposit_and_withdraw_transaction_to_trader(
    sender, instance, created, **kwargs
):
    if (
        not created
        and instance.trader
        and instance.status == OrderStatus.DELIVERED
        and instance.product_payment_status == ProductPaymentStatus.COD
    ):
        total_deposit = instance.product_cost

        already_exists = UserAccountTransaction.objects.filter(
            notes__contains=instance.tracking_number,
            user_account=instance.trader
        ).exists()
        if already_exists:
            return

        UserAccountTransaction.objects.create(
            user_account=instance.trader,
            amount=total_deposit,
            transaction_type=TransactionType.DEPOSIT,
            notes=instance.tracking_number,
        )

        total_withdraw = instance.trader_merchant_cost
        already_exists = UserAccountTransaction.objects.filter(
            notes__contains=instance.tracking_number,
            user_account=instance.trader
        ).exists()
        if already_exists:
            return

        UserAccountTransaction.objects.create(
            user_account=instance.trader,
            amount=total_withdraw,
            transaction_type=TransactionType.WITHDRAW,
            notes=instance.tracking_number,
        )


# Driver Transaction
# Make driver transaction, order COD, office will transfer balance to driver
@receiver(post_save, sender=Order)
def delivered_order_deposit_and_withdraw_transaction_to_driver(
    sender, instance, created, **kwargs
):
    if (
        not created
        and instance.driver
        and instance.status == OrderStatus.DELIVERED
        and instance.product_payment_status == ProductPaymentStatus.COD
    ):
        total_deposit = instance.product_cost + instance.trader_merchant_cost

        already_exists = UserAccountTransaction.objects.filter(
            notes__contains=instance.tracking_number,
            user_account=instance.driver
        ).exists()
        if already_exists:
            return

        UserAccountTransaction.objects.create(
            user_account=instance.driver,
            amount=total_deposit,
            transaction_type=TransactionType.DEPOSIT,
            notes=instance.tracking_number,
        )

        total_withdraw = instance.delivery_cost + instance.extra_delivery_cost
        already_exists = UserAccountTransaction.objects.filter(
            notes__contains=instance.tracking_number,
            user_account=instance.driver
        ).exists()
        if already_exists:
            return

        UserAccountTransaction.objects.create(
            user_account=instance.driver,
            amount=total_withdraw,
            transaction_type=TransactionType.WITHDRAW,
            notes=instance.tracking_number,
        )


# Make driver transaction, order paid, office will transfer balance to driver
@receiver(post_save, sender=Order)
def delivered_order_deposit_transaction_to_driver(sender, instance, created, **kwargs):
    if (
        not created
        and instance.driver
        and instance.status == OrderStatus.DELIVERED
        and instance.product_payment_status == ProductPaymentStatus.PAID
    ):
        total_deposit = instance.delivery_cost + instance.extra_delivery_cost

        already_exists = UserAccountTransaction.objects.filter(
            notes__contains=instance.tracking_number,
            user_account=instance.driver
        ).exists()
        if already_exists:
            return

        UserAccountTransaction.objects.create(
            user_account=instance.driver,
            amount=total_deposit,
            transaction_type=TransactionType.WITHDRAW,
            notes=instance.tracking_number,
        )


# Make driver transaction, order cancelled, office will give delivery cost to driver
@receiver(post_save, sender=Order)
def cancelled_order_withdraw_transaction_from_driver(
    sender, instance, created, **kwargs
):
    if not created and instance.driver and instance.status == OrderStatus.CANCELLED:
        total_withdraw = instance.delivery_cost + instance.extra_delivery_cost

        already_exists = UserAccountTransaction.objects.filter(
            notes__contains=instance.tracking_number,
            user_account=instance.driver
        ).exists()
        if already_exists:
            return

        UserAccountTransaction.objects.create(
            user_account=instance.driver,
            amount=total_withdraw,
            transaction_type=TransactionType.WITHDRAW,
            notes=instance.tracking_number,
        )


# Make driver transaction, order paid, office will transfer balance to driver
@receiver(post_save, sender=Order)
def update_order_status_to_assigned_after_created(sender, instance, created, **kwargs):
    if created and instance.driver:
        instance.status = OrderStatus.ASSIGNED
        instance.save()
