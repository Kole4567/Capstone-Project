from rest_framework import generics
from django.db.models import Q

from .models import Monster
from .serializers import MonsterListSerializer, MonsterDetailSerializer


class MonsterListView(generics.ListAPIView):
    """
    GET /api/v1/mhw/monsters/

    Optional query parameters:
    - is_elder_dragon (boolean)
    - element (string, case-insensitive)
    - min_stars (integer, 1–3, requires element)
    """

    serializer_class = MonsterListSerializer

    def get_queryset(self):
        queryset = Monster.objects.all().order_by("id")
        params = self.request.query_params

        # --------------------------------------------------
        # Filter: is_elder_dragon
        # --------------------------------------------------
        is_elder = params.get("is_elder_dragon")
        if is_elder is not None:
            value = is_elder.strip().lower()
            if value in ("true", "1", "yes"):
                queryset = queryset.filter(is_elder_dragon=True)
            elif value in ("false", "0", "no"):
                queryset = queryset.filter(is_elder_dragon=False)

        # --------------------------------------------------
        # Filter: element + min_stars
        # --------------------------------------------------
        element = params.get("element")
        if element:
            element = element.strip()

            # Filter by elemental weaknesses only
            queryset = queryset.filter(
                weaknesses__kind="element",
                weaknesses__name__iexact=element,
            )

            min_stars = params.get("min_stars")
            if min_stars is not None:
                try:
                    min_stars_int = int(min_stars)

                    # stars are defined as 1–3 in the API contract
                    if 1 <= min_stars_int <= 3:
                        queryset = queryset.filter(
                            weaknesses__stars__gte=min_stars_int
                        )
                except ValueError:
                    # Ignore invalid min_stars values
                    pass

            queryset = queryset.distinct()

        return queryset


class MonsterDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/mhw/monsters/{id}/

    {id} refers to Monster.id (internal database ID)
    """

    queryset = Monster.objects.all()
    serializer_class = MonsterDetailSerializer
    lookup_field = "id"