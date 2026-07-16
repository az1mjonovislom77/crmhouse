from django.db import migrations


REQUIRED = {
    'tasks_card': {'created_by_id', 'organization_id'},
    'users': {'organization_id'},
}

SQL = """
UPDATE tasks_card
SET organization_id = (
    SELECT u.organization_id
    FROM users u
    WHERE u.id = tasks_card.created_by_id
)
WHERE created_by_id IS NOT NULL
  AND organization_id IS NULL;
"""


def _schema_ready(conn, cursor):
    tables = set(conn.introspection.table_names(cursor))
    for table, cols in REQUIRED.items():
        if table not in tables:
            return False
        have = {c.name for c in conn.introspection.get_table_description(cursor, table)}
        if not cols.issubset(have):
            return False
    return True


def forwards(apps, schema_editor):
    conn = schema_editor.connection
    with conn.cursor() as cursor:
        if not _schema_ready(conn, cursor):
            return
        cursor.execute(SQL)


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0013_card_organization_historicalcard_organization'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
