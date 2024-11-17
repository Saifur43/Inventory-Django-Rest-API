from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, DashboardViewSet, ReportViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'reports', ReportViewSet, basename='reports')

urlpatterns = [
    path('', include(router.urls)),
]