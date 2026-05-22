from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("security", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="captchachallenge",
            name="image_data",
            field=models.BinaryField(blank=True, null=True),
        ),
    ]
