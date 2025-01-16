
from django.urls import path
from . import views
urlpatterns = [

  path('register/',views.UserRegistrationView.as_view(),name='register'),
  path('login/',views.UserLoginView.as_view(),name='login'),
  path('logout/',views.LogoutView.as_view(),name='user_logout'),
  path('profile/',views.UserBankAccountUpdateView.as_view(),name='profile'),
  path('changePassword/',views.UserPasswordChangeView.as_view(),name='change_password'),
]