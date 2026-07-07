
import common.services.image_service
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0001_initial'),
        ('tasks', '0010_remove_card_organization_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cards', to='organization.organization'),
        ),
        migrations.AddField(
            model_name='historicalcard',
            name='organization',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='organization.organization'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='comments/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'webp']), common.services.image_service.check_image_size]),
        ),
        migrations.AlterField(
            model_name='historicalcomment',
            name='file',
            field=models.TextField(blank=True, max_length=100, null=True, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'webp']), common.services.image_service.check_image_size]),
        ),
    ]
