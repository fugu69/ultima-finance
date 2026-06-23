from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. Custom authentication app (Handles Sign Up)
    path("accounts/", include("accounts.urls")),
    
    # 2. Built-in Django auth system (Handles Log In, Log Out, Passwords)
    path("accounts/", include("django.contrib.auth.urls")),
    
    # 3. Core application homepage
    path('', include('finance.urls'))
]
