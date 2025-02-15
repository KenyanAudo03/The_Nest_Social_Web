from django.urls import path
from . import views

urlpatterns = [
    path("", views.user_login, name="user_login"),
    path("signup/", views.signup, name="signup"),
    path("verify-email/<uuid:token>/", views.verify_email, name="verify_email"),
    path("email-sent/<str:email>/", views.email_sent, name="email_sent"),
    path("resend-email/<str:email>/", views.resend_email, name="resend_email"),
    path("home/", views.home, name="home"),
]
