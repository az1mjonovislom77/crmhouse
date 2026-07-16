from django.db import migrations


REQUIRED = {
    'booking_booking': {'home_id', 'organization_id'},
    'home_home': {'blocks_id'},
    'projects_blocks': {'projects_id'},
    'projects_projects': {'user_id'},
    'users': {'organization_id'},
}

SQL = """
UPDATE booking_booking
SET organization_id = (
    SELECT u.organization_id
    FROM home_home h
    JOIN projects_blocks b ON b.id = h.blocks_id
    JOIN projects_projects p ON p.id = b.projects_id
    JOIN users u ON u.id = p.user_id
    WHERE h.id = booking_booking.home_id
)
WHERE home_id IS NOT NULL
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
        ('booking', '0026_booking_organization'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
