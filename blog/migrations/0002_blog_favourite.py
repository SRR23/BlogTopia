# Generated by Django 5.1.1 on 2024-09-24 06:14

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='blog',
            name='favourite',
            field=models.ManyToManyField(blank=True, related_name='favourite_blogs', to=settings.AUTH_USER_MODEL),
        ),
    ]
