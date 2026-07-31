from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("login/", views.DashboardLoginView.as_view(), name="login"),
    path("logout/", views.dashboard_logout, name="logout"),
    path("", views.index, name="index"),

    path("enquiries/", views.message_list, name="messages"),
    path("enquiries/<int:pk>/", views.message_detail, name="message_detail"),
    path("enquiries/<int:pk>/delete/", views.message_delete, name="message_delete"),

    path("projects/<int:pk>/edit/", views.project_edit, name="project_edit"),

    path("email/send-test/", views.send_test_email, name="send_test_email"),

    path("section/<slug:key>/", views.singleton, name="singleton"),

    path("content/<slug:key>/", views.collection_list, name="collection_list"),
    path("content/<slug:key>/new/", views.collection_create, name="collection_create"),
    path("content/<slug:key>/<int:pk>/", views.collection_edit, name="collection_edit"),
    path("content/<slug:key>/<int:pk>/delete/", views.collection_delete, name="collection_delete"),
    path("content/<slug:key>/<int:pk>/toggle/", views.collection_toggle, name="collection_toggle"),
]
