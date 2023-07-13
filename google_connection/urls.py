from django.urls import path
from . import views

urlpatterns = [
    path("create", views.create, name="createSheets"),
    path("send/all", views.send, name="send"),
    path("delete/all", views.delete, name="delete"),
    path("auth", views.oauth_redirect, name="auth"),
    path("callback", views.oauth_callback, name="callback"),
    path("send/<str:dre>", views.send_one, name="sendSome"),
    path("delete/<str:dre>", views.delete_one, name="deleteSome"),
]