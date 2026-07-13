from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0016_learningvideo_school_designated_teacher_mobile_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='school',
            name='is_tata_classedge',
            field=models.BooleanField(default=False),
        ),
    ]
