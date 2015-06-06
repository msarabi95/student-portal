from django.conf.urls import patterns, url
from django.views.generic import TemplateView

urlpatterns = patterns('',
    url(r'^$', 'core.views.portal_home', name='home'),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'), name='about'),
    url(r'^aboutsc/$', 'core.views.about_sc', name='about_sc'),
    url(r'^copy/$', TemplateView.as_view(template_name='copy.html'), name='copy'),
    url(r'^launch/$', TemplateView.as_view(template_name='launch.html'), name='copy'),
    url(r'^visit/(?P<pk>\d+)/$', "core.views.visit_announcement", name='visit_announcement'),
)