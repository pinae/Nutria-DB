from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('find', views.query_food, name='query'),
    path('food', views.details_nopath, name='details_nopath'),
    path('food/<str:id_str>', views.details, name='details'),
    path('food/<str:id_str>/<str:amount>', views.details, name='details_amount'),
    path('login', views.log_in, name='login'),
    path('register', views.register, name='register'),
    path('save', views.save_food, name='save'),
    path('delete', views.delete_food, name='delete')
]
