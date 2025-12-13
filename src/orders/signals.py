from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Order, OrderStatus, ProductPaymentStatus
from transactions.helpers import create_order_transaction
from transactions.models import TransactionType


# Make trader transaction, order cancelled, office will take trader_merchant_cost from trader
@receiver(post_save, sender=Order)
def cancelled_order_withdraw_transaction_from_trader(
    sender, instance, created, **kwargs
):
    if not created and instance.trader and instance.status == OrderStatus.CANCELLED:
        create_order_transaction(
            user=instance.trader,
            amount=instance.trader_merchant_cost,
            transaction_type=TransactionType.DEPOSIT,
            tracking_number=instance.tracking_number,
            order_id=instance.id,
        )


# Make trader transaction, order (paid or remaining fees), office will take delivery cost from trader
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
        create_order_transaction(
            user=instance.trader,
            amount=instance.trader_merchant_cost,
            transaction_type=TransactionType.WITHDRAW,
            tracking_number=instance.tracking_number,
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
        create_order_transaction(
            user=instance.trader,
            amount=instance.product_cost,
            transaction_type=TransactionType.DEPOSIT,
            tracking_number=instance.tracking_number,
        )


# Driver Transaction


# Make driver transaction, order cancelled, office will give delivery cost to driver
@receiver(post_save, sender=Order)
def cancelled_order_withdraw_transaction_from_driver(
    sender, instance, created, **kwargs
):
    if not created and instance.driver and instance.status == OrderStatus.CANCELLED:
        create_order_transaction(
            user=instance.driver,
            amount=instance.delivery_cost + instance.extra_delivery_cost,
            transaction_type=TransactionType.DEPOSIT,
            tracking_number=instance.tracking_number,
        )


# Make driver transaction, order REMAINING FEES, office will transfer balance to driver
@receiver(post_save, sender=Order)
def delivered_order_remaining_fees_deposit_transaction_to_driver(
    sender, instance, created, **kwargs
):
    if (
        not created
        and instance.driver
        and instance.status == OrderStatus.DELIVERED
        and instance.product_payment_status == ProductPaymentStatus.REMAINING_FEES
    ):
        create_order_transaction(
            user=instance.driver,
            amount=instance.delivery_cost + instance.extra_delivery_cost,
            transaction_type=TransactionType.DEPOSIT,
            tracking_number=instance.tracking_number,
        )

        create_order_transaction(
            user=instance.driver,
            amount=instance.trader_merchant_cost,
            transaction_type=TransactionType.WITHDRAW,
            tracking_number=instance.tracking_number,
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
        create_order_transaction(
            user=instance.driver,
            amount=instance.delivery_cost + instance.extra_delivery_cost,
            transaction_type=TransactionType.DEPOSIT,
            tracking_number=instance.tracking_number,
        )


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

        create_order_transaction(
            user=instance.driver,
            amount=instance.product_cost + instance.trader_merchant_cost,
            transaction_type=TransactionType.WITHDRAW,
            tracking_number=instance.tracking_number,
        )

        create_order_transaction(
            user=instance.driver,
            amount=instance.delivery_cost + instance.extra_delivery_cost,
            transaction_type=TransactionType.DEPOSIT,
            tracking_number=instance.tracking_number,
        )


# Make driver transaction, order paid, office will transfer balance to driver
@receiver(post_save, sender=Order)
def update_order_status_to_assigned_after_created(sender, instance, created, **kwargs):
    if created and instance.driver:
        instance.status = OrderStatus.ASSIGNED
        instance.save()
