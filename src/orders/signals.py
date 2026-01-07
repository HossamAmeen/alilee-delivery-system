from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from orders.models import Order, OrderStatus, ProductPaymentStatus
from transactions.helpers import create_order_transaction
from transactions.models import TransactionType
from utilities.exceptions import CustomValidationError


@receiver(post_save, sender=Order)
def update_order_status_to_assigned_after_created(sender, instance, created, **kwargs):
    if created and instance.driver:
        instance.status = OrderStatus.ASSIGNED
        instance.save()


@receiver(post_save, sender=Order)
def update_order_status_to_completed_after_created(sender, instance, created, **kwargs):
    if not created and instance.status == OrderStatus.ASSIGNED and not instance.driver:
        raise CustomValidationError("يجب تعين سائق للطلب")


@receiver(post_save, sender=Order)
def check_order_have_trader(sender, instance, created, **kwargs):
    if created and not instance.trader:
        raise CustomValidationError("يجب تعين مورد للطلب")


@receiver(pre_save, sender=Order)
def update_postpone_count(sender, instance, **kwargs):
    if instance.status == OrderStatus.POSTPONED:
        instance.postpone_count += 1


@receiver(post_save, sender=Order)
def create_transaction_for_postponed_order(sender, instance, created, **kwargs):
    if not created and instance.status == OrderStatus.POSTPONED:
        create_order_transaction(
            user_id=instance.trader_id,
            amount=instance.trader_merchant_cost,
            transaction_type=TransactionType.DEPOSIT,
            order_id=instance.id,
            notes=f"تحصيل رسوم شحن {instance.tracking_number}",
        )


# Make trader transaction, order cancelled, office will take trader_merchant_cost from trader
@receiver(post_save, sender=Order)
def cancelled_order_withdraw_transaction_from_trader(
    sender, instance, created, **kwargs
):
    if not created and instance.trader and instance.status == OrderStatus.CANCELLED:
        create_order_transaction(
            user_id=instance.trader_id,
            amount=instance.trader_merchant_cost,
            transaction_type=TransactionType.DEPOSIT,
            order_id=instance.id,
            notes=f"تحصيل رسوم شحن {instance.tracking_number}",
        )


# Make trader transaction, order (paid or remaining fees), office will take delivery cost from trader
@receiver(post_save, sender=Order)
def delivered_order_withdraw_transaction_from_trader(
    sender, instance, created, **kwargs
):
    if not created and instance.status == OrderStatus.DELIVERED:
        if instance.product_payment_status == ProductPaymentStatus.PAID:
            create_order_transaction(
                user_id=instance.trader_id,
                amount=instance.trader_merchant_cost,
                transaction_type=TransactionType.WITHDRAW,
                order_id=instance.id,
                notes=f"سحب رسوم شحن {instance.tracking_number}",
            )
        elif instance.product_payment_status == ProductPaymentStatus.COD:
            create_order_transaction(
                user_id=instance.trader_id,
                amount=instance.trader_merchant_cost,
                transaction_type=TransactionType.WITHDRAW,
                order_id=instance.id,
                notes=f"سحب رسوم شحن {instance.tracking_number}",
            )

            create_order_transaction(
                user_id=instance.trader_id,
                amount=instance.product_cost,
                transaction_type=TransactionType.DEPOSIT,
                order_id=instance.id,
                notes=f"إيداع فلوس المنتج الخاص في  {instance.tracking_number}",
            )
        else:
            return


# Driver Transaction
@receiver(post_save, sender=Order)
def delivered_order_remaining_fees_deposit_transaction_to_driver(
    sender, instance, created, **kwargs
):
    if not created and instance.driver and instance.status == OrderStatus.DELIVERED:
        if instance.product_payment_status == ProductPaymentStatus.REMAINING_FEES:
            create_order_transaction(
                user_id=instance.driver_id,
                amount=instance.delivery_cost + instance.extra_delivery_cost,
                transaction_type=TransactionType.DEPOSIT,
                order_id=instance.id,
                notes=f"إيداع رسوم الشحن الخاصه بالمندوب {instance.tracking_number}",
            )

            create_order_transaction(
                user_id=instance.driver_id,
                amount=instance.trader_merchant_cost,
                transaction_type=TransactionType.WITHDRAW,
                order_id=instance.id,
                notes=f"سحب رسوم الشحن الخاصه بالمنطقة {instance.tracking_number}",
            )

        elif instance.product_payment_status == ProductPaymentStatus.PAID:
            create_order_transaction(
                user_id=instance.driver_id,
                amount=instance.delivery_cost + instance.extra_delivery_cost,
                transaction_type=TransactionType.DEPOSIT,
                order_id=instance.id,
                notes=f"إيداع رسوم الشحن الخاصه بالمنطقة {instance.tracking_number}",
            )
        elif instance.product_payment_status == ProductPaymentStatus.COD:
            create_order_transaction(
                user_id=instance.driver_id,
                amount=instance.product_cost,
                transaction_type=TransactionType.WITHDRAW,
                order_id=instance.id,
                notes=f"سحب فلوس المنتج الخاص وفلوس الشحن الخاص بالمنطقة في {instance.tracking_number}",
            )

            create_order_transaction(
                user_id=instance.driver_id,
                amount=instance.delivery_cost + instance.extra_delivery_cost,
                transaction_type=TransactionType.DEPOSIT,
                order_id=instance.id,
                notes=f"إيداع رسوم الشحن الخاصه بالمندوب {instance.tracking_number}",
            )
