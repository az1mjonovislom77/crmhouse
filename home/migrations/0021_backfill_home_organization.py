from django.db import migrations

# Backfill existing rows so org-scoped querysets keep showing them after the
# switch to a direct `organization` FK.
#
# This migration is intentionally DEPENDENCY-FREE (beyond its own AddField):
# depending on the `projects` app reorders the historical `projects.Basement`
# create/delete lifecycle and breaks from-scratch DB builds. Instead we guard
# on the exact tables/columns the UPDATE needs. On an incremental deploy they
# all exist and the backfill runs automatically; on a from-scratch build they
# may not exist yet (and there is no data anyway), so we skip. The
# `backfill_organizations` management command does the same and can be re-run.

REQUIRED = {
    'home_home': {'blocks_id', 'organization_id'},
    'projects_blocks': {'projects_id'},
    'projects_projects': {'user_id'},
    'users': {'organization_id'},
}

SQL = """
UPDATE home_home
SET organization_id = (
    SELECT u.organization_id
    FROM projects_blocks b
    JOIN projects_projects p ON p.id = b.projects_id
    JOIN users u ON u.id = p.user_id
    WHERE b.id = home_home.blocks_id
)
WHERE blocks_id IS NOT NULL
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
        ('home', '0020_home_organization'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
