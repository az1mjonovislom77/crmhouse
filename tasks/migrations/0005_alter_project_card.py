
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_historicalproject_description_project_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='card',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cards', to='tasks.card'),
        ),
    ]
