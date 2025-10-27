from django.db import models

from utilities.models.abstract_base_model import AbstractBaseModel


class City(AbstractBaseModel):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
