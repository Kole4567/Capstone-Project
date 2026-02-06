from rest_framework import generics
from rest_framework.pagination import LimitOffsetPagination

from .models import Monster
from .serializers import MonsterListSerializer, MonsterDetailSerializer


class MonsterListView(generics.ListAPIView):
    """
    GET /api/v1/mhw/monsters/

    Optional query parameters:
    - is_elder_dragon (boolean)
    - element (string, case-insensitive)
    - min_stars (integer, 1–3, requires element)
    - order_by (string)
    """

    serializer_class = MonsterListSerializer

    ALLOWED_ORDER_FIELDS = {
        "id",
        "name",
        "monster_type",
        "is_elder_dragon",
    }

    def get_queryset(self):
        queryset = Monster.objects.all()
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

            queryset = queryset.filter(
                weaknesses__kind="element",
                weaknesses__name__iexact=element,
            )

            min_stars = params.get("min_stars")
            if min_stars is not None:
                try:
                    min_stars_int = int(min_stars)
                    if 1 <= min_stars_int <= 3:
                        queryset = queryset.filter(
                            weaknesses__stars__gte=min_stars_int
                        )
                except ValueError:
                    pass

            queryset = queryset.distinct()

        # --------------------------------------------------
        # Ordering
        # --------------------------------------------------
        order_by = params.get("order_by")
        if order_by:
            field = order_by.lstrip("-")
            if field in self.ALLOWED_ORDER_FIELDS:
                queryset = queryset.order_by(order_by)
            else:
                # If invalid, fall back to a stable default order
                queryset = queryset.order_by("id")
        else:
            # Default order when no order_by is provided
            queryset = queryset.order_by("id")

        return queryset


class MonsterLimitOffsetPagination(LimitOffsetPagination):
    """
    Pagination settings for /monsters/paged/

    default_limit: items returned when limit is not specified
    max_limit: cap to prevent huge responses
    """
    default_limit = 50
    max_limit = 200


class MonsterListPagedView(MonsterListView):
    """
    GET /api/v1/mhw/monsters/paged/

    Same filters/order_by as /monsters/ but returns a paginated response:
    {
      "count": ...,
      "next": "...",
      "previous": "...",
      "results": [...]
    }
    """
    pagination_class = MonsterLimitOffsetPagination


class MonsterDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/mhw/monsters/{id}/
    """
    queryset = Monster.objects.all()
    serializer_class = MonsterDetailSerializer
    lookup_field = "id"