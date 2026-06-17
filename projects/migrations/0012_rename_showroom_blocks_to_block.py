from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0011_rename_project_block'),
    ]

    operations = [
        migrations.RenameField(
            model_name='showroom',
            old_name='blocks',
            new_name='block',
        ),
    ]
