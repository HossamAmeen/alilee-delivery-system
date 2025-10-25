from rest_framework.permissions import IsAuthenticated

from utilities.api import BaseViewSet

from .models import City
from .serializers import CitySerializer


class CityViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated]
    queryset = City.objects.all()
    serializer_class = CitySerializer
