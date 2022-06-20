import re
from datetime import datetime, timedelta, timezone

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, DeleteView, FormView, RedirectView

from pytube import YouTube
from difflib import SequenceMatcher

from TonTube import settings
from channel.forms.create_channel_form import ChannelForm
from video.models import Video, Like, Comment, VideoTag, Tag, Watch
from channel.models import Channel, Subscribe


def sort_video(video):
    return -(video['like'] * 3 + video['watch'])


def sort_video_recommended(video):
    return -video['note']


def sort_video_query(video):
    return -(video['matching_ratio'] + 4 * video['tags_ratio'])


def sort_video_like_rate(video):
    return -(3 * video['matching_ratio'] + video['likes_ratio'])


def getRecommendedVideos(video_source, videos):
    tag_source = [videoTag.tag.value for videoTag in VideoTag.objects.filter(video=video_source)]
    res = []
    for video in videos:
        common_tag = 0
        tags = [videoTag.tag.value for videoTag in VideoTag.objects.filter(video=video)]
        for tag in tags:
            if tag in tag_source:
                common_tag += 1
        if video_source.channel == video.channel:
            common_tag *= 1.25
        res.append({'video': video, 'note': common_tag})

    return res


def calcTagRatio(video, query, tags):
    ratios = []
    for w in query.split(' '):
        for t in tags:
            r = SequenceMatcher(None, w, t).ratio()
            ratios.append(r if r > 0.37 else 0)
    b = -5 if len(ratios) >= 5 else -len(ratios)
    ratios.sort()
    ratios = ratios[b:]
    print(video.title + ' : ', ratios)
    return sum(ratios) / len(ratios) if len(ratios) > 0 else 0


class VideoIndexView(ListView):
    template_name = "videos_index.html"
    model = Video
    context_object_name = "videos"


class VideoWatchView(LoginRequiredMixin, DetailView):
    template_name = "video_watch.html"
    model = Video

    def get(self, request, *args, **kwargs):
        video = Video.objects.get(slug=kwargs.get('slug'))
        if not Watch.objects.filter(video=video, user=request.user, date__day=datetime.now().day).exists():
            watch = Watch()
            watch.user = request.user
            watch.video = video
            watch.save()

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['video'] = self.object
        context['comments'] = [{"comment": comment, "currentUser": comment.user == self.request.user} for comment in
                               Comment.objects.filter(video=self.object)]
        context['tags'] = [tag.tag.value for tag in VideoTag.objects.filter(video=self.object)]
        context['likes'] = Like.objects.filter(video=self.object).count()
        context['liked'] = Like.objects.filter(user=self.request.user, video=self.object).exists()
        context['channel'] = self.object.channel
        context['recommended_videos'] = sorted(
            getRecommendedVideos(self.object, Video.objects.exclude(pk=self.object.pk)), key=sort_video_recommended)[
                                        -5:]

        return context


class VideoCreateView(LoginRequiredMixin, CreateView):
    template_name = "video_create.html"
    model = Video
    context_object_name = "form"
    fields = ('title', 'desc', 'source', 'thumbnail', 'published')


class LikeView(LoginRequiredMixin, View):
    def get_success_url(self):
        return reverse("video_watch_url", kwargs={"slug": Video.objects.get(pk=self.kwargs.get("pk"))})

    def get(self, request, *args, **kwargs):
        like = Like.objects.filter(user=self.request.user, video=Video.objects.get(pk=self.kwargs.get("pk")))
        if like.exists():
            like.delete()
        else:
            like = Like()
            like.video = get_object_or_404(Video, pk=self.kwargs.get("pk"))
            like.user = request.user
            like.save()

        return redirect(self.get_success_url())


class CommentView(LoginRequiredMixin, View):
    def get_success_url(self):
        return reverse("video_watch_url", kwargs={"slug": Video.objects.get(pk=self.kwargs.get("pk"))})

    def post(self, request, *args, **kwargs):
        comment = Comment()
        comment.video = get_object_or_404(Video, pk=self.kwargs.get("pk"))
        comment.user = self.request.user
        comment.content = request.POST.get("comment")
        comment.save()

        return redirect(self.get_success_url())


class ImportVideoView(LoginRequiredMixin, View):

    def get_success_url(self, slug):
        return reverse("video_watch_url", kwargs={"slug": slug})

    def get_error_url(self):
        return reverse("videos_index_url", kwargs={})

    def get(self, request, *args, **kwargs):
        if Channel.objects.filter(user=request.user).exists():
            return render(request, 'video_create.html')
        else:
            return redirect(reverse("channel_create_url"))

    def post(self, request, *args, **kwargs):
        if not Channel.objects.filter(user=self.request.user).exists():
            return redirect(self.get_error_url())

        yt_url_pattern = (
            r'(https?://)?(www\.)?'
            '(youtube|youtu|youtube-nocookie)\.(com|be)/'
            '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )

        url = request.POST.get('url')
        if re.match(yt_url_pattern, url) and YouTube(url):
            hashYT = url.split('v=')[-1]

            yt_video = YouTube(url)
            title = yt_video.title
            desc = yt_video.description
            thumbnail = yt_video.thumbnail_url
            tags = yt_video.keywords

            video = Video()
            video.title = title
            video.desc = desc
            video.thumbnail = thumbnail
            video.channel = Channel.objects.get(user=request.user)
            video.source = "https://www.youtube.com/embed/" + hashYT
            video.date_published = datetime.now()

            video.save()
            slug = video.slug

            for tag in tags:
                if not Tag.objects.filter(value=tag).exists():
                    newTag = Tag()
                    newTag.value = tag
                    newTag.save()

                newTag = Tag.objects.get(value=tag)
                videoTag = VideoTag()
                videoTag.video = video
                videoTag.tag = newTag
                videoTag.save()

            return redirect(self.get_success_url(slug))
        else:
            # Pour les ptits malins
            return redirect(url)

class CommentDeleteView(LoginRequiredMixin, DeleteView):

    def get_success_url(self, slug):
        return reverse("video_watch_url", kwargs={"slug": slug})

    def get(self, request, *args, **kwargs):
        comment = Comment.objects.get(pk=kwargs.get('pk'))
        video = comment.video

        if comment.user == self.request.user:
            comment.delete()

        return redirect(self.get_success_url(video.slug))

class VideoSubsView(LoginRequiredMixin, ListView):
    template_name = "videos_index.html"
    model = Video

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        channel_subed = [channel for channel in
                         [sub.channel for sub in Subscribe.objects.filter(sub=self.request.user)]]
        context['videos'] = Video.objects.filter(channel__in=channel_subed).order_by('-date_published')
        return context

class VideoHistoryView(LoginRequiredMixin, ListView):
    template_name = "videos_index.html"
    model = Video

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['videos'] = [watch.video for watch in Watch.objects.filter(user=self.request.user).order_by('-date')]
        return context

class VideoTrendsView(LoginRequiredMixin, ListView):
    template_name = "videos_index.html"
    model = Video

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Selectionner toutes les vidéos
        # Compter chaque vue et chque like par vidéo sur la deniere semaine
        # faire un score
        videos = Video.objects.filter(date_published__gt=datetime.today() - timedelta(days=7))
        videos = [
            {'video': video,
             'like': Like.objects.filter(video=video).count() / (
                         (datetime.now(timezone.utc) - video.date_published).days + 1),
             'watch': Watch.objects.filter(video=video).count() / (
                         (datetime.now(timezone.utc) - video.date_published).days + 1)
             }
            for video in videos
        ]

        videos = sorted(videos, key=sort_video)

        context['videos'] = [video['video'] for video in videos]
        return context

class VideoSearchView(LoginRequiredMixin, ListView):
    template_name = "videos_index.html"
    model = Video

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q') if 'q' in self.request.GET.keys() else ""
        print(self.request.GET.get('q'))

        if query == "":
            context['videos'] = Video.objects.all()
            return context

        videos = [
            {
                'video': video,
                'matching_ratio': SequenceMatcher(None, video.title.lower(), query.lower()).ratio(),
                'likes_ratio': Like.objects.filter(video=video).count() / Watch.objects.filter(video=video).count(),
                'tags_ratio': calcTagRatio(video, query,
                                           [tag.tag.value for tag in VideoTag.objects.filter(video=video)]),
            }
            for video in Video.objects.all()
        ]

        videos = sorted(videos, key=sort_video_query)[:10]
        videos = sorted(videos, key=sort_video_like_rate)
        context['videos'] = [video['video'] for video in videos]

        for video in videos:
            print(video['video'].title + ' : ')
            print(video['matching_ratio'])
            print(video['tags_ratio'])
            print(video['likes_ratio'])

        return context
