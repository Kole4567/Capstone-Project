from rest_framework import generics
from MonsterHunterWorld.models import Monster
from MonsterHunterWorld.serializers import (
    MonsterListSerializer,
    MonsterDetailSerializer,
)


class MonsterListView(generics.ListAPIView):
    queryset = Monster.objects.all().order_by("id")
    serializer_class = MonsterListSerializer


class MonsterDetailView(generics.RetrieveAPIView):
    queryset = Monster.objects.all()
    serializer_class = MonsterDetailSerializer