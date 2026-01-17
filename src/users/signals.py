from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from utilities.exceptions import CustomValidationError
from users.models import Trader, Driver


@receiver(pre_delete, sender=Trader)
def prevent_trader_deletion_with_balance(sender, instance, **kwargs):
    """Prevent deletion of traders with non-zero balance."""
    if instance.balance != 0:
        raise CustomValidationError(
            _(
                "لا يمكن حذف التاجر لأنه لديه رصيد غير صفري. الرصيد الحالي: {}"
            ).format(instance.balance)
        )


@receiver(pre_delete, sender=Driver)
def prevent_driver_deletion_with_balance(sender, instance, **kwargs):
    """Prevent deletion of drivers with non-zero balance."""
    if instance.balance != 0:
        raise CustomValidationError(
            _(
                "لا يمكن حذف السائق لأنه لديه رصيد غير صفري. الرصيد الحالي: {}"
            ).format(instance.balance)
        )
