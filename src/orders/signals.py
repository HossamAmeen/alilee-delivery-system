from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Order
from transactions.models import TransactionType, UserAccountTransaction


@receiver(post_save, sender=Order)
def create_driver_withdraw_transaction(sender, instance, created, **kwargs):
    if not created and instance.status == Order.OrderStatus.DELIVERED and instance.driver:
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


# Make trader transaction, order paid, office will take delivery cost from trader
@receiver(post_save, sender=Order)
def delivered_order_withdraw_transaction_from_trader(sender, instance, created, **kwargs):
    if (not created and instance.status == Order.OrderStatus.DELIVERED and
            instance.product_payment_status == Order.ProductPaymentStatus.PAID and instance.trader):
        total_withdraw = instance.trader_merchant_cost

        already_exists = UserAccountTransaction.objects.filter(
            notes__contains=instance.tracking_number
        ).exists()
        if already_exists:
            return

        UserAccountTransaction.objects.create(
            user_account=instance.trader,
            amount=total_withdraw,
            transaction_type=TransactionType.WITHDRAW,
        )

        instance.trader.balance += total_withdraw
        instance.trader.save()


# Make trader transaction, order cancelled, office will take trader_merchant_cost from trader
@receiver(post_save, sender=Order)
def cancelled_order_withdraw_transaction_from_trader(sender, instance, created, **kwargs):
    if not created and instance.status == Order.OrderStatus.CANCELLED and instance.trader:
        total_withdraw = instance.trader_merchant_cost

        already_exists = UserAccountTransaction.objects.filter(
            notes__contains=instance.tracking_number
        ).exists()
        if already_exists:
            return

        UserAccountTransaction.objects.create(
            user_account=instance.trader,
            amount=total_withdraw,
            transaction_type=TransactionType.WITHDRAW,
        )

        instance.trader.balance += total_withdraw
        instance.trader.save()


# Make trader transaction, order cancelled, office will take trader_merchant_cost from trader
@receiver(post_save, sender=Order)
def cancelled_order_withdraw_transaction_from_trader(sender, instance, created, **kwargs):
    if not created and instance.status == Order.OrderStatus.CANCELLED and instance.trader:
        total_withdraw = instance.trader_merchant_cost

        already_exists = UserAccountTransaction.objects.filter(
            notes__contains=instance.tracking_number
        ).exists()
        if already_exists:
            return

        UserAccountTransaction.objects.create(
            user_account=instance.trader,
            amount=total_withdraw,
            transaction_type=TransactionType.WITHDRAW,
        )

        instance.trader.balance += total_withdraw
        instance.trader.save()


# Make trader transaction, order COD, office will transfer product cost to trader
@receiver(post_save, sender=Order)
def delivered_order_deposit_and_withdraw_transaction_to_trader(sender, instance, created, **kwargs):
    if (not created and instance.status == Order.OrderStatus.DELIVERED and
            instance.product_payment_status == Order.ProductPaymentStatus.COD and instance.trader):
        total_deposit = instance.product_cost

        already_exists = UserAccountTransaction.objects.filter(
            notes__contains=instance.tracking_number
        ).exists()
        if already_exists:
            return

        UserAccountTransaction.objects.create(
            user_account=instance.trader,
            amount=total_deposit,
            transaction_type=TransactionType.DEPOSIT,
        )

        instance.trader.balance -= total_deposit
        instance.trader.save()

        total_withdraw = instance.trader_merchant_cost
        already_exists = UserAccountTransaction.objects.filter(
            notes__contains=instance.tracking_number
        ).exists()
        if already_exists:
            return

        UserAccountTransaction.objects.create(
            user_account=instance.trader,
            amount=total_withdraw,
            transaction_type=TransactionType.WITHDRAW,
        )

        instance.trader.balance -= total_withdraw
        instance.trader.save()


# Make driver transaction, order COD, office will transfer balance to driver
@receiver(post_save, sender=Order)
def delivered_order_deposit_and_withdraw_transaction_to_driver(sender, instance, created, **kwargs):
    if (not created and instance.status == Order.OrderStatus.DELIVERED and
            instance.product_payment_status == Order.ProductPaymentStatus.COD and instance.driver):
        total_deposit = instance.product_cost + instance.trader_merchant_cost

        already_exists = UserAccountTransaction.objects.filter(
            notes__contains=instance.tracking_number
        ).exists()
        if already_exists:
            return

        UserAccountTransaction.objects.create(
            user_account=instance.driver,
            amount=total_deposit,
            transaction_type=TransactionType.DEPOSIT,
        )

        instance.driver.balance += total_deposit
        instance.driver.save()

        total_withdraw = instance.delivery_cost + instance.extra_cost
        already_exists = UserAccountTransaction.objects.filter(
            notes__contains=instance.tracking_number
        ).exists()
        if already_exists:
            return

        UserAccountTransaction.objects.create(
            user_account=instance.driver,
            amount=total_withdraw,
            transaction_type=TransactionType.WITHDRAW,
        )

        instance.driver.balance -= total_withdraw
        instance.driver.save()


# Make driver transaction, order paid, office will transfer balance to driver
@receiver(post_save, sender=Order)
def delivered_order_deposit_transaction_to_driver(sender, instance, created, **kwargs):
    if (not created and instance.status == Order.OrderStatus.DELIVERED and
            instance.product_payment_status == Order.ProductPaymentStatus.PAID and instance.driver):
        total_deposit = instance.delivery_cost + instance.extra_cost

        already_exists = UserAccountTransaction.objects.filter(
            notes__contains=instance.tracking_number
        ).exists()
        if already_exists:
            return

        UserAccountTransaction.objects.create(
            user_account=instance.driver,
            amount=total_deposit,
            transaction_type=TransactionType.DEPOSIT,
        )

        instance.driver.balance += total_deposit
        instance.driver.save()
