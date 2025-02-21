from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.user_login, name="user_login"),
    path("create/", views.create_post, name="create_post"),
    path("toggle_like/<int:post_id>/", views.toggle_like, name="toggle_like"),
]
