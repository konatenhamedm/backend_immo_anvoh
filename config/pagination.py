from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Pagination par défaut (12) ; le client peut demander ?page_size= jusqu'à 100."""
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100
