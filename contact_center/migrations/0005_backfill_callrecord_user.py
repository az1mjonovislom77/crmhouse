import re

from django.db import migrations


def normalize_phone(value):
    # Same rule as common.utils.normalize_phone (kept inline so the migration stays self-contained).
    if not value:
        return ''
    digits = re.sub(r'\D', '', str(value))
    return digits[-9:] if len(digits) >= 9 else digits


def backfill_users(apps, schema_editor):
    CallRecord = apps.get_model('contact_center', 'CallRecord')
    User = apps.get_model('user', 'User')

    phone_map = {}
    for user_id, phone in User.objects.exclude(phone_number__isnull=True).exclude(
            phone_number='').values_list('id', 'phone_number'):
        digits = normalize_phone(phone)
        if digits:
            phone_map[digits] = user_id

    if not phone_map:
        return

    to_update = []
    for record in CallRecord.objects.filter(user__isnull=True).only('id', 'src', 'dst').iterator():
        user_id = phone_map.get(normalize_phone(record.src)) or phone_map.get(normalize_phone(record.dst))
        if user_id:
            record.user_id = user_id
            to_update.append(record)
        if len(to_update) >= 500:
            CallRecord.objects.bulk_update(to_update, ['user'])
            to_update = []
    if to_update:
        CallRecord.objects.bulk_update(to_update, ['user'])


class Migration(migrations.Migration):

    dependencies = [
        ('contact_center', '0004_callrecord_user'),
        ('user', '0008_alter_user_full_name_alter_user_phone_number'),
    ]

    operations = [
        migrations.RunPython(backfill_users, migrations.RunPython.noop),
    ]
