from django import forms
from django.shortcuts import redirect
from django.urls import reverse

from channel.models import Channel


class ChannelForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['name', 'logo', 'banner']
        labels = {
            'name': 'Channel name',
            'logo': 'Logo (image)',
            'banner': 'Bannner (image)',
        }
