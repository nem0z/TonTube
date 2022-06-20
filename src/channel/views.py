import re
from datetime import datetime, timedelta, timezone

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, DetailView, FormView, RedirectView


from TonTube import settings
from channel.forms.create_channel_form import ChannelForm
from video.models import Video, Watch, Comment, Like
from channel.models import Channel, Subscribe


class ChannelIndexView(ListView):
    template_name = "channel_index.html"
    model = Channel
    context_object_name = "channels"

class ChannelWatchView(DetailView):
    template_name = "channel_watch.html"
    model = Channel

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['channel'] = self.object
        context['videos'] = Video.objects.filter(channel=self.object)
        context['subs'] = Subscribe.objects.filter(channel=self.object).count()
        context['subed'] = Subscribe.objects.filter(channel=self.object, sub=self.request.user).exists()
        context['media_url'] = settings.MEDIA_URL

        return context

class ChannelSubscribeView(LoginRequiredMixin, View):

    def get_success_url(self, slug):
        return reverse("channel_watch_url", kwargs={"slug": slug})

    def get(self, request, *args, **kwargs):
        channel = Channel.objects.get(slug=kwargs.get('slug'))
        if Subscribe.objects.filter(sub=request.user, channel=channel).exists():
            Subscribe.objects.get(sub=request.user, channel=channel).delete()
        else:
            sub = Subscribe()
            sub.sub = request.user
            sub.channel = channel
            sub.save()

        return redirect(self.get_success_url(kwargs.get('slug')))

class CreateChannelView(LoginRequiredMixin, FormView):
    template_name = 'channel_create.html'
    form_class = ChannelForm

    def get_channel_url(self):
        return reverse("channel_watch_url", kwargs={"slug": Channel.objects.get(user=self.request.user).slug})

    def get(self, request, *args, **kwargs):
        if not Channel.objects.filter(user=request.user).exists():
            form=self.form_class(None)
            return render(request, self.template_name, {'form': form})
        else:
            return render(self.get_channel_url())

    def post(self, request, *args, **kwargs):
        form = ChannelForm(request.POST, request.FILES)
        if form.is_valid():
            channel = form.save(commit=False)
            channel.user = request.user
            channel.save()
            return redirect(self.get_channel_url())
        else:
            return render(request, self.template_name, {'form':form})

class ChannelMyView(LoginRequiredMixin, RedirectView):

    def get_redirect_url(self, **kwargs):
        if not self.request.user.is_anonymous:
            if Channel.objects.filter(user=self.request.user).exists():
                return reverse("channel_watch_url", kwargs={"slug": Channel.objects.get(user=self.request.user)})
            else:
                return reverse("channel_create_url", kwargs={})
        else:
            return reverse("videos_index_url", kwargs={})

class ChannelStatsView(LoginRequiredMixin, DetailView):
    template_name = "channel_stats.html"
    model = Channel

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['channel'] = self.object
        context['subs'] = self.object.count_subs()
        context['watchs'] = sum([1 for w in Watch.objects.filter(video__in=[video for video in Video.objects.filter(channel=self.object)])])
        context['likes'] = sum([1 for l in Like.objects.filter(video__in=[video for video in Video.objects.filter(channel=self.object)])])
        context['comments'] = sum([1 for c in Comment.objects.filter(video__in=[video for video in Video.objects.filter(channel=self.object)])])

        return context