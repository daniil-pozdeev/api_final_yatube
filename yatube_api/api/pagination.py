from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class PostPagination(LimitOffsetPagination):
    """
    Класс для пагинации постов с использованием лимита и смещения.
    Наследуется от LimitOffsetPagination для настройки ответа.
    """
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.count,  # Общее количество объектов
            'next': self.get_next_link(),  # Ссылка на следующую страницу, если она есть
            'previous': self.get_previous_link(),  # Ссылка на предыдущую страницу, если она есть
            'results': data  # Данные текущей страницы
        })
