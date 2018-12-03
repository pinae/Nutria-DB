from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('find', views.query_food, name='query'),
    path('login', views.log_in, name='login'),
    path('register', views.register, name='register'),
    path('save', views.save_food, name='save')
]
