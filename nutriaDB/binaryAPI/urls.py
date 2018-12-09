from django.urls import path
from . import views

urlpatterns = [
    path('q', views.query_food, name='query')
]
