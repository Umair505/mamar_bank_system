from django.contrib import admin
from django.urls import path,include
from core.views import  HomeView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/',include('accounts.urls')),
    path('transactions/',include('transactions.urls')),
    path('',HomeView.as_view(),name='home')
    
    
]