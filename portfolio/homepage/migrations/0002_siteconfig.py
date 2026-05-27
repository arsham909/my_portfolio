from django.core.validators import FileExtensionValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('resume_file', models.FileField(
                    blank=True,
                    help_text='Upload your latest resume PDF. Replaces the previous file.',
                    null=True,
                    upload_to='resume/',
                    validators=[FileExtensionValidator(['pdf'])],
                )),
                ('resume_label', models.CharField(default='Download Resume', max_length=80)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Site configuration',
                'verbose_name_plural': 'Site configuration',
            },
        ),
    ]
