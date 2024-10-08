# Generated by Django 5.1.1 on 2024-10-10 12:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0003_alter_rating_value'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='movie',
            name='ratings_average',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='movie',
            name='ratings_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='rating',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to=settings.AUTH_USER_MODEL),
        ),
    ]
