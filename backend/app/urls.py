from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, UserViewSet, ProjectViewSet, ProposalViewSet
from . import views

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'users', UserViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'proposals', ProposalViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('upload/', views.upload_file, name='upload_file'),
]