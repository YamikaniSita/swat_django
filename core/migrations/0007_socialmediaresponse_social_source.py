# Generated by Django 5.1.7 on 2025-04-28 11:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_question_required_data'),
        ('surveys', '0004_remove_socialmediasource_social_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialmediaresponse',
            name='social_source',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='social_source', to='surveys.socialmediasource'),
        ),
    ]
