# Generated by Django 2.2.13 on 2020-09-03 09:12

from django.db import migrations


def add_dummy_data(apps, schema_editor):
    Building = apps.get_model('main', 'Building')
    Floor = apps.get_model('main', 'Floor')

    b3 = Building.objects.create(name="3 Whitehall")
    b55 = Building.objects.create(name="55 Whitehall")

    Floor.objects.create(building=b3, name="1F", desks="\n".join(f"A{x}" for x in range(75)))
    Floor.objects.create(building=b3, name="2F", desks="\n".join(f"B{x}" for x in range(50)))
    Floor.objects.create(building=b3, name="3F", desks="\n".join(f"C{x}" for x in range(40)))

    Floor.objects.create(building=b55, name="1F", desks="\n".join(f"A{x}" for x in range(300)))
    Floor.objects.create(building=b55, name="2F", desks="\n".join(f"B{x}" for x in range(250)))
    Floor.objects.create(building=b55, name="3F", desks="\n".join(f"C{x}" for x in range(200)))
    Floor.objects.create(building=b55, name="4F", desks="\n".join(f"D{x}" for x in range(150)))


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_dummy_data),
    ]
