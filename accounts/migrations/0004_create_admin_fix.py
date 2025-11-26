from django.db import migrations

def create_admin(apps, schema_editor):
    User = apps.get_model("auth", "User")
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            password="Admin123!",
            email="admin@example.com"
        )

class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_passwordresetotp"),  # nếu khác thì sửa theo project của bạn
    ]

    operations = [
        migrations.RunPython(create_admin),
    ]
