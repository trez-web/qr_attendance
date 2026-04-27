import uuid
from django.db import migrations, models


def populate_tokens(apps, schema_editor):
    Meeting = apps.get_model('attendance', 'Meeting')
    for m in Meeting.objects.all():
        m.qr_token = uuid.uuid4()
        m.save(update_fields=['qr_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0007_scannedattendance'),
    ]

    operations = [
        # Step 1: add nullable (so existing rows don't conflict)
        migrations.AddField(
            model_name='meeting',
            name='qr_token',
            field=models.UUIDField(null=True, blank=True),
        ),
        # Step 2: fill existing rows
        migrations.RunPython(populate_tokens, migrations.RunPython.noop),
        # Step 3: make unique + non-null
        migrations.AlterField(
            model_name='meeting',
            name='qr_token',
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
    ]
