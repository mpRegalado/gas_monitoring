from django.urls import path

from . import views

app_name='readings'
urlpatterns = [
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:pk>/download', views.download, name='download'),
    path('post/', views.post, name='post'),
]
