from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admins', '0008_halloffameentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='content',
            name='event_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='content',
            name='event_time',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='content',
            name='event_mode',
            field=models.CharField(blank=True, default='Online', max_length=50),
        ),
        migrations.AlterField(
            model_name='content',
            name='content_type',
            field=models.CharField(choices=[('announcement', 'Announcement'), ('faq', 'FAQ'), ('training', 'Upcoming Training Calendar')], max_length=20),
        ),
    ]
