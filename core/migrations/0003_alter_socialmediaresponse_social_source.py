# Generated by Django 5.1.7 on 2025-06-01 13:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_initial'),
        ('surveys', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socialmediaresponse',
            name='social_source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='surveys.socialmediasource'),
        ),
    ]
