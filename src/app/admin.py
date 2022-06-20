from django.contrib import admin

from video.models import Video
from channel.models import Channel

admin.site.register(Video)
admin.site.register(Channel)
