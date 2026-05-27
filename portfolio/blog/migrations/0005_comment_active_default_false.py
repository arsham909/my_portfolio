from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_postimage_alter_post_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='active',
            field=models.BooleanField(
                default=False,
                help_text='Comment is shown publicly only after an admin approves it.',
            ),
        ),
    ]
