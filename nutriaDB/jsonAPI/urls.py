from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('find', views.query_food, name='query')
]
