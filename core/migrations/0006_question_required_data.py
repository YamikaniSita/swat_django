# Generated by Django 5.1.7 on 2025-04-22 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_response_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='required_data',
            field=models.CharField(choices=[('all', 'All'), ('sentiment', 'Sentiment'), ('topics', 'Entities and Topics')], default='all', max_length=20),
        ),
    ]
