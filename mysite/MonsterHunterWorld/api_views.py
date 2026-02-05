from rest_framework import generics
from django.db.models import Q

from .models import Monster
from .serializers import MonsterListSerializer, MonsterDetailSerializer


class MonsterListView(generics.ListAPIView):
    serializer_class = MonsterListSerializer

    def get_queryset(self):
        queryset = Monster.objects.all().order_by("id")
        params = self.request.query_params

        # --------------------------------------------------
        # is_elder_dragon filter
        # --------------------------------------------------
        is_elder = params.get("is_elder_dragon")
        if is_elder is not None:
            value = is_elder.strip().lower()
            if value in ("true", "1", "yes"):
                queryset = queryset.filter(is_elder_dragon=True)
            elif value in ("false", "0", "no"):
                queryset = queryset.filter(is_elder_dragon=False)

        # --------------------------------------------------
        # element + min_stars filter
        # --------------------------------------------------
        element = params.get("element")
        if element:
            element = element.strip()

            queryset = queryset.filter(
                weaknesses__kind="element",
                weaknesses__name__iexact=element,
            )

            min_stars = params.get("min_stars")
            if min_stars is not None:
                try:
                    min_stars = int(min_stars)
                    queryset = queryset.filter(
                        weaknesses__stars__gte=min_stars
                    )
                except ValueError:
                    pass  # ignore invalid min_stars

            queryset = queryset.distinct()

        return queryset


class MonsterDetailView(generics.RetrieveAPIView):
    queryset = Monster.objects.all()
    serializer_class = MonsterDetailSerializer
    lookup_field = "id"