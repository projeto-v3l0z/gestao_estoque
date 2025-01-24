from django.urls import path
from .views import LoginView

urlpatterns = [
    path('login/', LoginView.as_view(template_name='accounts/login.html'), name='account_login'),
]