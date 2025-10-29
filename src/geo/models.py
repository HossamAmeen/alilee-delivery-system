from django.db import models

from utilities.models.abstract_base_model import AbstractBaseModel


class City(AbstractBaseModel):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class DeliveryZone(AbstractBaseModel):
    name = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, related_name="delivery_zones")

    def __str__(self):
        return f"{self.name} - {self.city.name if self.city else ''}"
