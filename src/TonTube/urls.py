"""TonTube URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib import auth
from django.template.defaulttags import url
from django.urls import path, include

from TonTube import settings
from app import views
from channel.views import *
from video.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path("accounts/register/", views.register_request, name="register"),
    path('', VideoIndexView.as_view(), name="videos_index_url"),
    path('channels/', ChannelIndexView.as_view(), name="channel_index_url"),
    path('channel/subscribe/<slug:slug>', ChannelSubscribeView.as_view(), name="channel_subscribe_url"),
    path('video/<slug:slug>', VideoWatchView.as_view(), name="video_watch_url"),
    path('channel/<slug:slug>', ChannelWatchView.as_view(), name="channel_watch_url"),
    path('channel/', ChannelMyView.as_view(), name="channel_my_url"),
    path('video/create/', VideoCreateView.as_view(), name="video_create_url"),
    path('video/like/<int:pk>', LikeView.as_view(), name="video_like_url"),
    path('video/comment/<int:pk>', CommentView.as_view(), name="video_comment_url"),
    path('video/comment/delete/<int:pk>', CommentDeleteView.as_view(), name="comment_delete_url"),
    path('video/import/', ImportVideoView.as_view(), name="video_import_url"),
    path('channel/create/', CreateChannelView.as_view(), name="channel_create_url"),
    path('channel/<slug:slug>/stats/',  ChannelStatsView.as_view(), name="channel_stats_url"),
    path('videos/', VideoSearchView.as_view(), name="video_search_url"),
    path('videos/subs/', VideoSubsView.as_view(), name="video_subs_url"),
    path('videos/history/', VideoHistoryView.as_view(), name="video_history_url"),
    path('videos/trends/', VideoTrendsView.as_view(), name="video_trends_url"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
