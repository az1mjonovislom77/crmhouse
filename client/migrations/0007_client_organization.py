import django.db.models.deletion
from django.db import migrations, models


def set_organization_from_user(apps, schema_editor):
    Client = apps.get_model('client', 'Client')
    for client in Client.objects.filter(organization__isnull=True, user__isnull=False).select_related('user'):
        if client.user.organization_id:
            client.organization_id = client.user.organization_id
            client.save(update_fields=['organization'])


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0001_initial'),
        ('client', '0006_client_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clients', to='organization.organization'),
        ),
        migrations.RunPython(set_organization_from_user, migrations.RunPython.noop),
    ]
