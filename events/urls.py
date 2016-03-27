from django.conf.urls import patterns, url
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from events import views

urlpatterns = patterns('',
    url(r'^(?P<event_code_name>[\d\w_]+)/$', views.redirect_home, name="redirect_home"),
    url(r'^(?P<event_code_name>[\d\w_]+)/sessions/$', views.list_sessions, name="list_sessions"),
    url(r'^(?P<event_code_name>[\d\w_]+)/sessions/(?P<pk>\d+)/$', views.show_session, name="show_session"),
    url(r'^(?P<event_code_name>[\d\w_]+)/registration/$', views.introduce_registration, name="registration_introduction"),
    url(r'^(?P<event_code_name>[\d\w_]+)/registration/user/$', views.user_registration, name="user_registration"),
    url(r'^(?P<event_code_name>[\d\w_]+)/registration/list/$', views.list_registrations, name="list_registrations"),
    url(r'^(?P<event_code_name>[\d\w_]+)/registration/nonuser/$', views.nonuser_registration, name="nonuser_registration"),
    url(r'^(?P<event_code_name>[\d\w_]+)/registration/thanks/$', views.registration_completed, name="registration_completed"),
    url(r'^(?P<event_code_name>[\d\w_]+)/registration/closed/$', views.registration_closed, name="registration_closed"),
    url(r'^(?P<event_code_name>[\d\w_]+)/registration/already/$', views.registration_already, name="registration_already"),
)