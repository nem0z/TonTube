from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import slugify

import hashlib


def short_str(string, hash_length=8):
    if hash_length > 128:
        raise ValueError("hash_length {} dépasse 128".format(hash_length))
    hash_object = hashlib.sha512(string.encode())
    hash_hex = hash_object.hexdigest()
    return hash_hex[0:hash_length]



class Channel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    date_created = models.DateTimeField(default=datetime.now)
    slug = models.SlugField(null=True)
    logo = models.ImageField(upload_to='images', null=True)
    banner = models.ImageField(upload_to='images', null=True)

    def save(self, *args, **kwargs):
        slug = slugify(short_str(str(self.pk), 10));

        while Channel.objects.filter(slug=slug).exists():
            slug = slugify(short_str(slug, 10));

        self.slug = slug
        super(Channel, self).save(*args, **kwargs)

    def __str__(self):
        return self.slug;

    def count_subs(self):
        return Subscribe.objects.filter(channel=self).count()


class Subscribe(models.Model):
    sub = models.ForeignKey(User, on_delete=models.CASCADE)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
