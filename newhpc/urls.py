from django.conf.urls import url, include
from django.http import HttpResponse
from . import views

urlpatterns = [
    #url(r'^riyadh/ar/$', views.riy_ar_index, name="riy_ar_index"),
    #url(r'^riyadh/en/$', views.riy_en_index, name="riy_en_index"),
    url(r'^riyadh/en/research$', views.riy_en_research, name="riy_ar_research"),

]
