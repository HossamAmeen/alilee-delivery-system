from django.db.models.signals import post_save
from django.dispatch import receiver
from utilities.exceptions import CustomValidationError

from orders.models import Order, OrderStatus, ProductPaymentStatus
from transactions.helpers import create_order_transaction
from transactions.models import TransactionType


@receiver(post_save, sender=Order)
def update_order_status_to_assigned_after_created(sender, instance, created, **kwargs):
    if created and instance.driver:
        instance.status = OrderStatus.ASSIGNED
        instance.save()


@receiver(post_save, sender=Order)
def check_order_have_trader(sender, instance, created, **kwargs):
    if created and not instance.trader:
        raise CustomValidationError("Order must have a trader")


# Make trader transaction, order cancelled, office will take trader_merchant_cost from trader
@receiver(post_save, sender=Order)
def cancelled_order_withdraw_transaction_from_trader(
    sender, instance, created, **kwargs
):
    if not created and instance.trader and instance.status == OrderStatus.CANCELLED:
        transaction_type = TransactionType.DEPOSIT
        amount = instance.trader_merchant_cost
        create_order_transaction(
            user_id=instance.trader_id,
            amount=amount,
            transaction_type=transaction_type,
            order_id=instance.id,
            notes=f"تحصيل رسوم شحن {instance.tracking_number}"
        )


# Make trader transaction, order (paid or remaining fees), office will take delivery cost from trader
@receiver(post_save, sender=Order)
def delivered_order_withdraw_transaction_from_trader(
    sender, instance, created, **kwargs
):
    if not created and instance.status == OrderStatus.DELIVERED:
        if instance.product_payment_status == ProductPaymentStatus.PAID:
            transaction_type = TransactionType.WITHDRAW
            amount = instance.trader_merchant_cost
            notes = f"سحب رسوم شحن {instance.tracking_number}"
        elif instance.product_payment_status == ProductPaymentStatus.COD:
            transaction_type = TransactionType.DEPOSIT
            amount = instance.product_cost
            notes = f"إيداع فلوس المنتج الخاص في  {instance.tracking_number}"

        create_order_transaction(
            user_id=instance.trader_id,
            amount=amount,
            transaction_type=transaction_type,
            order_id=instance.id,
            notes=notes
        )


# Driver Transaction
@receiver(post_save, sender=Order)
def delivered_order_remaining_fees_deposit_transaction_to_driver(
    sender, instance, created, **kwargs
):
    if (
        not created
        and instance.driver
        and instance.status == OrderStatus.DELIVERED
    ):
        if instance.product_payment_status == ProductPaymentStatus.REMAINING_FEES:
            create_order_transaction(
                user_id=instance.driver_id,
                amount=instance.delivery_cost + instance.extra_delivery_cost,
                transaction_type=TransactionType.DEPOSIT,
                order_id=instance.id,
                notes=f"إيداع رسوم الشحن الخاصه بالمندوب {instance.tracking_number}"
            )

            create_order_transaction(
                user_id=instance.driver_id,
                amount=instance.trader_merchant_cost,
                transaction_type=TransactionType.WITHDRAW,
                order_id=instance.id,
                notes=f"سحب رسوم الشحن الخاصه بالمنطقة {instance.tracking_number}"
            )

        elif instance.product_payment_status == ProductPaymentStatus.PAID:
            create_order_transaction(
                user_id=instance.driver_id,
                amount=instance.delivery_cost + instance.extra_delivery_cost,
                transaction_type=TransactionType.DEPOSIT,
                order_id=instance.id,
                notes=f"إيداع رسوم الشحن الخاصه بالمنطقة {instance.tracking_number}"
            )
        elif instance.product_payment_status == ProductPaymentStatus.COD:
            create_order_transaction(
                user_id=instance.driver_id,
                amount=instance.product_cost + instance.trader_merchant_cost,
                transaction_type=TransactionType.WITHDRAW,
                order_id=instance.id,
                notes=f"سحب فلوس المنتج الخاص وفلوس الشحن الخاص بالمنطقة في {instance.tracking_number}"
            )

            create_order_transaction(
                user_id=instance.driver_id,
                amount=instance.delivery_cost + instance.extra_delivery_cost,
                transaction_type=TransactionType.DEPOSIT,
                order_id=instance.id,
                notes=f"إيداع رسوم الشحن الخاصه بالمندوب {instance.tracking_number}"
            )
