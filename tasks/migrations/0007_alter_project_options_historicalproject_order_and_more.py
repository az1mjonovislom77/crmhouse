
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0006_alter_project_users'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='project',
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='historicalproject',
            name='order',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='project',
            name='order',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='comment',
            name='project',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='tasks.project'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='project',
            name='card',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='tasks.card'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='project',
            name='users',
            field=models.ManyToManyField(blank=True, related_name='task_projects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['card', 'order'], name='card_order_idx'),
        ),
        migrations.AddConstraint(
            model_name='project',
            constraint=models.UniqueConstraint(fields=('card', 'order'), name='unique_order_per_card'),
        ),
    ]
