from django.conf.urls import patterns, url
from media import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^activities/$', views.list_activities, name="list_activities"),
    url(r'^activities/reports/$', views.list_reports, name="list_reports"),
)