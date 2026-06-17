from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0010_showroom'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RenameModel('Projects', 'Project'),
                migrations.AlterModelTable('Project', 'projects_projects'),
                migrations.RenameModel('Blocks', 'Block'),
                migrations.AlterModelTable('Block', 'projects_blocks'),
            ],
            database_operations=[],
        ),
    ]
