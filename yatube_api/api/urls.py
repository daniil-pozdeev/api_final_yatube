from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, FollowViewSet, CommentViewSet, GroupViewSet
from rest_framework_simplejwt import views

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')
router.register(
    r'posts/(?P<post_id>\d+)/comments',
    CommentViewSet,
    basename='comment'
)
router.register(r'groups', GroupViewSet, basename='group')
router.register(r'follow', FollowViewSet, basename='follow')

urlpatterns = [
    path('', include(router.urls)),
    path(
        'jwt/create/',
        views.TokenObtainPairView.as_view(),
        name='token_obtain_pair'
    ),
    path(
        'jwt/refresh/',
        views.TokenRefreshView.as_view(),
        name='token_refresh'
    ),
    path('jwt/verify/', views.TokenVerifyView.as_view(), name='token_verify'),
]
