import os
import subprocess

from datetime import datetime

from fabric import task, Config, Connection

suffix = datetime.now().strftime("_%Y_%m_%d-%H_%M")
stages = {
    'production': {
        'stage_name': 'production',
        'host': 'ubuntu@app.zookeep.com',
        'app_name': 'talentai',
        'branch_name': 'master',
        'swagger_api_url': 'https://app.zookeep.com/api',
        'dashboard_zip': 'talentai_dashboard' + suffix,
        'backend_zip': 'talentai_backend' + suffix,
        'project_root': '/home/ubuntu/talentai',
    },
    'staging': {
        'stage_name': 'staging',
        'host': 'ubuntu@staging.zookeep.com',
        'app_name': 'staging_talentai',
        'branch_name': 'develop',
        'swagger_api_url': 'https://staging.zookeep.com/api',
        'dashboard_zip': 'staging_talentai_dashboard' + suffix,
        'backend_zip': 'staging_talentai_backend' + suffix,
        'project_root': '/home/ubuntu/staging_talentai',
    },
    'dev': {
        'stage_name': 'dev',
        'host': 'ubuntu@dev.zookeep.com',
        'app_name': 'talentai',
        'swagger_api_url': 'https://dev.zookeep.com/api',
        'dashboard_zip': 'talentai_dashboard' + suffix,
        'backend_zip': 'talentai_backend' + suffix,
        'project_root': '/home/ubuntu/talentai',
    },
}

deployments_archive_foolder = '/home/ubuntu/deployments_archive/'
db_dump_archive_folder = '/home/ubuntu/db_dumps/'


class cd:
    """Context manager for changing the current working directory"""

    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


config = Config(overrides={'run': {'echo': True, 'pty': True}})


def get_git_revision_hash():
    try:
        out = subprocess.Popen(
            ['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE
        ).communicate()[0]
        return out.strip().decode('ascii')
    except:
        return 'unknown'


def compress_upload(c, stage, frontend, backend):
    dashboard_build_folder = './dashboard/build/'

    print('Creating deployments_archive folder')
    c.run('mkdir -p {}'.format(deployments_archive_foolder))

    if frontend:
        print('Compressing frontend files')
        with cd(dashboard_build_folder):
            c.local(
                'zip -9 -r {} ./*'.format('../../' + stage['dashboard_zip'] + '.zip')
            )

        print('Pushing frontend files')
        c.put(stage['dashboard_zip'] + '.zip', deployments_archive_foolder)

    if backend:
        print('Compressing backend files')
        c.local(
            'zip -9 -r {} ./* -x "*.zip" "*.pyc" "*linkedin-scraping-ext*" "*dashboard*" "*.git*" "*docs*"'.format(
                stage['backend_zip'] + '.zip'
            )
        )
        print('Pushing backend files')
        c.put(stage['backend_zip'] + '.zip', deployments_archive_foolder)


def get_local_branch_name():

    local_branch = (
        subprocess.run(
            ['git', 'name-rev', '--name-only', 'HEAD'], stdout=subprocess.PIPE
        )
        .stdout.decode('utf-8')
        .replace('\n', '')
    )

    remote = subprocess.run(
        ['git', 'config', 'branch.{}.remote'.format(local_branch)],
        stdout=subprocess.PIPE,
    ).stdout.decode('utf-8')

    if remote:
        print('### Current local branch is: {}'.format(local_branch))
        return local_branch

    return None


def print_current_branch(c):
    print('### Current branch is:')
    c.local(
        'git rev-parse --abbrev-ref HEAD && git rev-parse --short HEAD',
        replace_env=False,
    )


def git_clean_checkout(c, branch_name):
    print('### Executing clean checkout:')
    c.run('git checkout {} -f'.format(branch_name))
    c.run('git clean -df')


def stop_services(c, stage):
    print('### Stopping app:')
    c.run(
        'sudo supervisorctl stop {}'.format(
            ' '.join(get_supervisord_services_config(stage))
        ),
        warn=True,
    )


def build_dashboard(c):
    with cd('./dashboard'):

        print('### Installing React dependencies:')
        c.local('yarn install --frozen-lockfile', replace_env=False)

        print('### Compiling translations for React:')
        c.local('yarn run compile', replace_env=False)

        print('### Building React:')
        c.local(
            'export REACT_APP_SENTRY_PUBLIC_DSN={} && '
            'export REACT_APP_ZENDESK_WIDGET_KEY={} && '
            'export REACT_APP_GA_MEASUREMENT_ID={} && '
            'export REACT_APP_HCAPTCHA_SITE_KEY={} && '
            'yarn run build'.format(
                os.getenv('REACT_APP_SENTRY_PUBLIC_DSN'),
                os.getenv('REACT_APP_ZENDESK_WIDGET_KEY'),
                os.getenv('REACT_APP_GA_MEASUREMENT_ID'),
                os.getenv('REACT_APP_HCAPTCHA_SITE_KEY'),
            ),
            replace_env=False,
        )


def release_backend_code(c, stage):

    be_deployment_folder = stage['project_root'] + '/backend'

    print('### Creating backend dist folder:')
    c.run('mkdir -p {}'.format(be_deployment_folder))

    print('### Removing previous dist:')
    c.run('rm -rf {}'.format(be_deployment_folder))
    c.run('mkdir -p {}'.format(be_deployment_folder))

    be_logs_folder = stage['project_root'] + '/logs/nginx'
    print('### Creating logs folders:')
    c.run('mkdir -p {}'.format(be_logs_folder))

    print('### Moving files to dist folder:')
    c.run(
        'unzip {} -d {}'.format(
            deployments_archive_foolder + stage['backend_zip'] + '.zip',
            be_deployment_folder,
        )
    )

    print("### Creating virtual env")
    with c.cd(be_deployment_folder):
        c.run("pipenv install")

        print("### Getting .env file")
        c.run("cp {}/../configs/default.env .env".format(stage['project_root']))


def release_dashboard_code(c, stage):

    fe_deployment_folder = stage['project_root'] + '/dashboard'

    print('### Creating backend dist folder:')
    c.run('mkdir -p {}'.format(fe_deployment_folder))

    print('### Removing previous dist:')
    c.run('rm -rf {}'.format(fe_deployment_folder))
    c.run('mkdir -p {}'.format(fe_deployment_folder))

    print('### Moving files to dist folder:')
    c.run(
        'unzip {} -d {}'.format(
            deployments_archive_foolder + stage['dashboard_zip'] + '.zip',
            fe_deployment_folder,
        )
    )


def pipenv_sync(c):
    print('### Pipenv sync:')
    c.local('pipenv sync', replace_env=False)


def run_collectstatic(c):
    print('### Collecting static files:')
    c.local(
        'pipenv run python manage.py collectstatic --noinput --clear', replace_env=False
    )


def run_compilemessages(c):
    print('### Compiling translations for Django:')
    # We want to ignore ".venv" folder bu the ignore option was added to "compilemessages"
    # only in Django 3.0. So we run it form within the locales folder.
    with cd('locale'):
        c.local('pipenv run python ../manage.py compilemessages', replace_env=False)


def gen_swagger_react_env(c, stage):
    """
    Swagger Specifications are used in various places in the dashboard.
    They need to be re-generated ever time there are changes in the API.
    If this step is not done in development, the frontend will get the specs
    from the `swagger.json` view on Django.
    In production ans staging this step is necessary to provide React
    with the API base url.
    """
    swagger_specs_file = "./dashboard/src/swagger_specs.json"
    print('### Generating Swagger spec for React env:')
    c.local(
        'pipenv run python manage.py gen_swagger_react_env --mock-request --url {} --overwrite {}'.format(
            stage['swagger_api_url'], swagger_specs_file
        ),
        replace_env=False,
    )


def migrate_db(c):
    print('### Migrating DB:')
    c.run('pipenv run python manage.py migrate')


def dump_db(c):
    print('### Creating db archive folder:')
    c.run('mkdir -p {}'.format(db_dump_archive_folder))

    print('### Dumping Remote DB:')
    dump_path = db_dump_archive_folder + 'remote_db' + suffix + '.dump'

    c.run(
        'pg_dump --clean --no-owner --format custom {} > {}'.format(
            os.getenv('DUMP_SOURCE_DB_URI'), dump_path
        )
    )

    return dump_path


def restore_db(c, dump_path):
    print('### Restoring from DB dump:')
    c.run(
        "pg_restore --no-owner --no-privileges --clean -d '{}' {}".format(
            os.getenv('DUMP_TARGET_DB_URI'), dump_path
        )
    )


def inject_configurations(c, stage):

    print('### Injecting NGINX settings:')
    c.run(
        'cp -a ./backend/configs/{}/etc/nginx/sites-available/. /etc/nginx/sites-available/'.format(
            stage['stage_name']
        )
    )

    print('### Injecting supervisord settings:')
    c.run(
        'cp -a ./backend/configs/{}/etc/supervisord/conf.d/. /etc/supervisor/conf.d/'.format(
            stage['stage_name']
        )
    )

    print('### Re-reading supervisorctl configs:')
    c.run('sudo supervisorctl reread')
    c.run('sudo supervisorctl update')


def start_services(c, stage):
    print('### Starting app:')
    c.run(
        'sudo supervisorctl start {}'.format(
            ' '.join(get_supervisord_services_config(stage))
        )
    )
    print('### Reloading NGINX')
    c.run('sudo service nginx reload')


def get_supervisord_services_config(stage):
    return [
        stage['app_name'],
        '{}_celery'.format(stage['app_name']),
        '{}_celery_beat'.format(stage['app_name']),
    ]


def deploy_fn(c, stage, frontend=True, backend=True, pre_migration=None):

    env_prefix = 'export ENVIRONMENT={} && export RELEASE={}'.format(
        stage['stage_name'], get_git_revision_hash()
    )
    with c.prefix(env_prefix):
        print('### Starting deployment of release {}'.format(env_prefix))

        if backend:
            pipenv_sync(c)

        if frontend:
            gen_swagger_react_env(c, stage)
            build_dashboard(c)

        run_collectstatic(c)
        run_compilemessages(c)
        compress_upload(c, stage, frontend, backend)

        c.run('mkdir -p {}'.format(stage['project_root']))

        with c.cd(stage['project_root']):
            if frontend:
                release_dashboard_code(c, stage)
            if backend:
                if pre_migration:
                    with c.cd('backend'):
                        print('### Running pre-migration:')
                        c.run(
                            'pipenv run python manage.py migrate {}'.format(
                                pre_migration
                            )
                        )
                release_backend_code(c, stage)
                stop_services(c, stage)
                inject_configurations(c, stage)

                with c.cd('backend'):
                    migrate_db(c)

        start_services(c, stage)


@task
def get_version(context, stage_name='production'):
    stage = stages[stage_name]

    dist_root = '/home/ubuntu/{}/dist'.format(stage['app_name'])
    connection = Connection(
        stage['host'], config=config, connect_kwargs=context['connect_kwargs']
    )
    with connection, connection.cd(dist_root):
        print_current_branch(connection)


@task
def deploy_production(context, exclude_backend=False, exclude_frontend=False):
    stage = stages['production']
    app_connection = Connection(
        stage['host'],
        config=config,
        connect_kwargs=context['connect_kwargs'],  # Required if ssh has a passphrase
    )

    return deploy_fn(
        app_connection,
        stage,
        backend=(not exclude_backend),
        frontend=(not exclude_frontend),
    )


@task
def deploy_staging(context, exclude_backend=False, exclude_frontend=False):
    stage = stages['staging']
    app_connection = Connection(
        stage['host'],
        config=config,
        connect_kwargs=context['connect_kwargs'],  # Required if ssh has a passphrase
    )
    return deploy_fn(
        app_connection,
        stage,
        backend=(not exclude_backend),
        frontend=(not exclude_frontend),
    )


@task
def deploy_dev(
    context, exclude_backend=False, exclude_frontend=False, pre_migration=None
):
    stage = stages['dev']
    app_connection = Connection(
        stage['host'],
        config=config,
        connect_kwargs=context['connect_kwargs'],  # Required if ssh has a passphrase
    )
    return deploy_fn(
        app_connection,
        stage,
        backend=(not exclude_backend),
        frontend=(not exclude_frontend),
        pre_migration=pre_migration,
    )


@task
def dev_backup_then_restore_db(context):
    """
    Requires env variables
    - DUMP_SOURCE_DB_URI - db to dump/backup
    - DUMP_TARGET_DB_URI - db to restore the dump to
    Note that the dev db data prior to restoring gets overwritten.
    """
    stage = stages['dev']
    app_connection = Connection(
        stage['host'],
        config=config,
        connect_kwargs=context['connect_kwargs'],  # Required if ssh has a passphrase
    )
    dump_path = dump_db(app_connection)
    restore_db(app_connection, dump_path)


def parse_migrations(text):
    lines = text.splitlines()
    migrations = []
    for line in lines:
        if line.startswith('['):
            print('-> {}'.format(line))
            migrated = True if '[X]' in line else False
            migrations.append(
                (migrated, line.replace('[X]', '').replace('[ ]', '').replace(' ', ''))
            )
    return migrations


# TODO: helpers for checking difference between local and remote migrations
def show_migrations(c, stage):

    print('### show migrations...')
    with c.cd(stage['project_root']):
        result = c.run('pipenv run python manage.py showmigrations -p').stdout
        remote_migrations = parse_migrations(result)

    local_result = subprocess.run(
        ['pipenv', 'run', 'python', 'manage.py', 'showmigrations', '-p'],
        stdout=subprocess.PIPE,
    ).stdout.decode('utf-8')
    local_migrations = parse_migrations(local_result)

    print('Remote migrations: {}'.format(remote_migrations))
    print('Local migrations: {}'.format(local_migrations))

    print([item for item in local_migrations if item not in remote_migrations])


@task
def migrations(context, stage_name='production', branch_name=None):
    app_connection = Connection(
        'ubuntu@13.114.193.71',
        config=config,
        connect_kwargs=context['connect_kwargs'],  # Required if ssh has a passphrase
    )
    return show_migrations(app_connection, stages['stage_name'])
