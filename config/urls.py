from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts.forms import StyledAuthenticationForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'accounts/login/', 
        auth_views.LoginView.as_view(form_class=StyledAuthenticationForm), 
        name='login'
    ),
    # 1. Custom authentication app (Handles Sign Up)
    path("accounts/", include("accounts.urls")),
    
    # 2. Built-in Django auth system (Handles Log In, Log Out, Passwords)
    path("accounts/", include("django.contrib.auth.urls")),
    
    # 3. Core application homepage
    path('', include('finance.urls'))
]
