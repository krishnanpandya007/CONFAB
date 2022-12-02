from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('signin', views.simple_signin, name='signin'),
    path('signup/verify_email/', views.verify_email, name='verify_email'),
    path("logout/", LogoutView.as_view(), name="logout"),

    # Miantain proorities of the following two lines: (Can fall in Regex)
    path('signup/final/<str:email_hash>/', views.simple_signup2, name='signup'),
    path('signup_submit', views.simple_signup2_submit, name='signup_submit'),
    path('forgot_password', views.forgot_password, name='forgot_password'),
    path('whatisconfab', views.whatisconfab, name='whatisconfab'),

]