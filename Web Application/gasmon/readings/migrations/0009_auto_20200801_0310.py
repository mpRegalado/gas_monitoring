# Generated by Django 3.0.8 on 2020-08-01 01:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('readings', '0008_auto_20200726_1904'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='measurement',
            name='count',
        ),
        migrations.AlterField(
            model_name='session',
            name='name',
            field=models.CharField(default='2020-08-01 01:10:53.829006+00:00', max_length=200),
        ),
    ]
