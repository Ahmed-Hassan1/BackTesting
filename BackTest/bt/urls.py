from django.urls import path
from .views import *

urlpatterns = [
    path('',homePage,name="home"),
    path('profitpal',profitPal,name="profitpal"),
    path('dkmacloud',dkMACloud,name="dkmacloud"),
    path('test',testing,name="testing"),
]