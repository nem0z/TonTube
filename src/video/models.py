from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import slugify
import hashlib

from channel.models import Channel


def short_str(string, hash_length=8):
    if hash_length > 128:
        raise ValueError("hash_length {} dépasse 128".format(hash_length))
    hash_object = hashlib.sha512(string.encode())
    hash_hex = hash_object.hexdigest()
    return hash_hex[0:hash_length]



class Video(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(null=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, null=True)
    source = models.URLField()
    thumbnail = models.URLField()
    desc = models.TextField()
    date_upload = models.DateTimeField(default=datetime.now)
    date_published = models.DateTimeField()
    published = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        slug = slugify(short_str(str(self.pk), 10));

        while Video.objects.filter(slug=slug).exists():
            slug = slugify(short_str(slug, 10));

        self.slug = slug
        super(Video, self).save(*args, **kwargs)

    def __str__(self):
        return self.slug;



class Like(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.PROTECT)



class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(default="")
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    date = models.DateTimeField(default=datetime.now, blank=False)



class Tag(models.Model):
    value = models.TextField(max_length=255)



class VideoTag(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)



class Watch(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(default=datetime.now)
