import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_post_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='posts/cover/%Y/%m/',
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif']
                    )
                ],
                help_text='Cover image. For inline photos, use the Images section below.',
            ),
        ),
        migrations.CreateModel(
            name='PostImage',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                )),
                ('image', models.ImageField(
                    upload_to='posts/inline/%Y/%m/',
                    validators=[
                        django.core.validators.FileExtensionValidator(
                            allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif']
                        )
                    ],
                )),
                ('caption', models.CharField(blank=True, max_length=200)),
                ('alt_text', models.CharField(blank=True, max_length=200)),
                ('order', models.PositiveIntegerField(default=0)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name='images',
                    to='blog.post',
                )),
            ],
            options={
                'ordering': ['order', 'created'],
            },
        ),
    ]
