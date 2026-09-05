from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0005_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='file_created_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='تاريخ إنشاء الملف'),
        ),
        migrations.AddField(
            model_name='patient',
            name='has_file',
            field=models.BooleanField(default=False, help_text='إذا كان True يظهر في سجل ملف المرضى لدى الدكتور', verbose_name='لديه ملف مريض'),
        ),
    ]
