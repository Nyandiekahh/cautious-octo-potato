from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'readings', views.EnergyReadingViewSet, basename='reading')
router.register(r'summaries', views.UsageSummaryViewSet, basename='summary')

urlpatterns = [
    path('', include(router.urls)),
]