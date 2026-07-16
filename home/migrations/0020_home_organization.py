
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0019_alter_homestatushistory_changed_at_and_more'),
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='home',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='homes', to='organization.organization'),
        ),
    ]
