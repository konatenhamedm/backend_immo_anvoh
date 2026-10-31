from typing import Protocol, List, Optional
from apps.properties.infrastructure.models import Property, PropertyStatus

class PropertyRepositoryInterface(Protocol):
    """Interface / Port du Repository pour l'accès aux biens immobiliers."""
    def get_by_id(self, property_id: str) -> Optional[Property]:
        ...
    def search(self, commune: Optional[str] = None, property_type: Optional[str] = None, max_price: Optional[float] = None) -> List[Property]:
        ...

class DjangoPropertyRepository:
    """Implémentation concrète du Repository via l'ORM Django (PostgreSQL)."""
    
    def get_by_id(self, property_id: str) -> Optional[Property]:
        try:
            return Property.objects.select_related('assigned_agent', 'owner').prefetch_related('images').get(id=property_id)
        except Property.DoesNotExist:
            return None

    def search(self, commune: Optional[str] = None, property_type: Optional[str] = None, max_price: Optional[float] = None) -> List[Property]:
        qs = Property.objects.filter(status=PropertyStatus.DISPONIBLE).prefetch_related('images')
        if commune:
            qs = qs.filter(commune__iexact=commune)
        if property_type:
            qs = qs.filter(property_type=property_type)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        return list(qs)
