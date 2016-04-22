from django.conf.urls import url
from django.contrib.auth import views as auth
from django.conf.urls import include

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^dates/$', views.dates, name='dates'),
    url(r'^users/$', views.users, name='users'),
    url(r'^settings/$', views.settings, name='settings'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^dates/edit/(?P<id>[0-9]+)/$', views.viewEdit, name='viewEdit'),
    url(r'^password_reset/$', auth.password_reset, {'template_name':'pw/reset.html', 'email_template_name':'pw/email.html', 'subject_template_name':'pw/subject.html'}, name='password_reset'),
    url(r'^password_reset/done/$', auth.password_reset_done, {'template_name':'pw/done.html'},name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',auth.password_reset_confirm, {'template_name':'pw/confirm.html'}, name='password_reset_confirm'),
    url(r'^reset/done/$', auth.password_reset_complete, {'template_name':'pw/complete.html'}, name='password_reset_complete'),
    url(r'^update/$', views.forumUpdate, name='forumUpdate')
]
