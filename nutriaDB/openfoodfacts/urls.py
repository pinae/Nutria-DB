from django.urls import path
from . import views

urlpatterns = [
    path('ean/<str:ean>', views.ask_openfoodfacts_org, name="openfoodfacts_ean"),
    path('search', views.search_openfoodfacts_org_nopath, name="openfoodfacts_search_no_path"),
    path('search/<str:query_str>', views.search_openfoodfacts_org, name="openfoodfacts_search")
]
