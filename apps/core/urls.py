from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("projects/", views.projects, name="projects"),
    path("services/", views.services, name="services"),
    path("services/<slug:slug>/", views.service_detail, name="service_detail"),
    path("blog/", views.blog, name="blog"),
    path("blog/<slug:slug>/", views.blog_post, name="blog_post"),
    path("faq/", views.faq, name="faq"),
    path("terms/", views.content_page, {"slug": "terms"}, name="terms"),
    path("privacy/", views.content_page, {"slug": "privacy"}, name="privacy"),
    path("contact/submit/", views.contact_submit, name="contact_submit"),
]
