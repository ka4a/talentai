# Generated by Django 2.2.2 on 2019-07-14 11:32

# from django.contrib.contenttypes.models import ContentType
from django.db import migrations


def migrate_agencyteam_to_team(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    ContentType = apps.get_model('contenttypes', 'ContentType')
    Team = apps.get_model('core', 'Team')

    AgencyTeam = apps.get_model('core', 'AgencyTeam')
    AgencyAdministrator = apps.get_model('core', 'AgencyAdministrator')
    AgencyManager = apps.get_model('core', 'AgencyManager')
    Recruiter = apps.get_model('core', 'Recruiter')

    agency_content_type = ContentType.objects.get(
        app_label='core', model='agency'
    )

    for at in AgencyTeam.objects.using(db_alias).all():
        t = Team.objects.create(
            name=at.name,
            org_content_type=agency_content_type,
            org_id=at.agency_id,
        )

        profiles = AgencyAdministrator.objects.using(db_alias).filter(teams=at).all()
        for p in profiles:
            print(at.id, t.id, type(p), p.id)
            p.new_teams.add(t)

        profiles = AgencyManager.objects.using(db_alias).filter(teams=at).all()
        for p in profiles:
            print(at.id, t.id, type(p), p.id)
            p.new_teams.add(t)

        profiles = Recruiter.objects.using(db_alias).filter(teams=at).all()
        for p in profiles:
            print(at.id, t.id, type(p), p.id)
            p.new_teams.add(t)

    AgencyTeam.objects.using(db_alias).delete()


def migrate_team_to_agencyteam(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    ContentType = apps.get_model('contenttypes', 'ContentType')
    Team = apps.get_model('core', 'Team')

    AgencyTeam = apps.get_model('core', 'AgencyTeam')
    AgencyAdministrator = apps.get_model('core', 'AgencyAdministrator')
    AgencyManager = apps.get_model('core', 'AgencyManager')
    Recruiter = apps.get_model('core', 'Recruiter')

    agency_content_type = ContentType.objects.get(
        app_label='core', model='agency'
    )

    for t in Team.objects.using(db_alias).filter(org_content_type=agency_content_type).all():
        at = AgencyTeam.objects.create(
            name=t.name,
            agency_id=t.org_id
        )

        profiles = AgencyAdministrator.objects.using(db_alias).filter(new_teams=t).all()
        for p in profiles:
            print(at.id, t.id, type(p), p.id)
            p.teams.add(at)

        profiles = AgencyManager.objects.using(db_alias).filter(new_teams=t).all()
        for p in profiles:
            print(at.id, t.id, type(p), p.id)
            p.teams.add(at)

        profiles = Recruiter.objects.using(db_alias).filter(new_teams=t).all()
        for p in profiles:
            print(at.id, t.id, type(p), p.id)
            p.teams.add(at)

    Team.objects.using(db_alias).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0088_org_teams'),
    ]

    operations = [
        migrations.RunPython(
            migrate_agencyteam_to_team, migrate_team_to_agencyteam
        ),
    ]
