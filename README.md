![CI](https://github.com/HCCRTokyo/talentai/workflows/CI/badge.svg?branch=develop)

# ZooKeep.io

ZooKeep.io is a recruiting app that allows recruiting agencies to match candidates to jobs.

The backend has been developed in Django while the frontend is React.

Stack:

- Docker
- Django
- Postgres
- RabbitMQ
- Celery
- React

## Backend

### Development Environment

Requirements:
- Python 3, pip, pipenv
- docker, docker-compose
- The transifex client if you need to push translations to the Transifex API (which is sone in CI): `sudo -H pip install transifex-client`
  
You will need an up to-date .env file to run the backend.

```
$ pipenv install
$ docker-compose up -d
$ pipenv shell
$ python manage.py migrate
$ python manage.py runserver 9009
```

Running Celery tasks:
```
$ celery -A talentai worker -l info
```

### Running tests

Testing using built-in Django unittest module

```
$ python manage.py test
```

Running tests with coverage

```
$ coverage run manage.py test
$ coverage html
$ open htmlcov/index.html
```

## Frontend

Requirements:

- Node v15.4.0

```
cd dashboard && yarn install
yarn run compile
yarn run start
```

### Code style
The frontend project uses ESLint to enforce code style and perform static analysis. Checks are performed with pre-commit hooks. Commit will fail if errors are detected. You can perform lint checking with `yarn run lint` command and apply automatic fixes with `yarn run lint-fix`.

You can skip pre-commit hooks by using `--no-verify` flag on commit, however this is not recommended. You should either fix your code or disable the rule, if undesired.

- To disable a rule, you cadd it in the `rules` field in `.eslintrc.js` like so: `'sonarjs/no-duplicated-branches': 0`
- Here are checked rules: [SonarJs](https://rules.sonarsource.com/javascript), [React rules](https://www.npmjs.com/package/eslint-plugin-react#list-of-supported-rules), [Eslint rules](https://eslint.org/docs/2.0.0/rules/)

There is a bunch of integrations to live-check code style on the most popular IDEs. You can find them [in here](https://eslint.org/docs/user-guide/integrations), we encourage to use them.


## Usage

Fixtures do not include user data, so you should create it yourself the first time you run the app.

Start creating a new Django superuser:

`python manage.py createsuperuser`

You can now login at `http://127.0.0.1:9009/admin`

Go ahead and send a signup requests as a "Company" (Client) and as an "Agency" at `http://localhost:3000/sign-up`.
To approve the requests, visit `http://127.0.0.1:9009/admin/core/agencyregistrationrequest/` and `http://127.0.0.1:9009/admin/core/clientregistrationrequest/`, select the requests' check-boxes and from the "action" menu set "Create selected client/agencies" and hit "Go".

Now you are ready to populate the dashboard.

From the "Client" dashboard you can create "Jobs", assign "Agencies" the them, create "Managers" and handle the candidate and job status.
- The first thing to do is to a create a contract with an Agency (Agencies tab -> Agency Directory).
- Now create a Job and assign the agency to it

From the "Agency" account you can create "Candidates" from the dedicated tab.
- Create a candidate in the relevant tab
- Assign it to a job at `http://localhost:3000/job/1`

## Translation

We use "lingui" to manage translations in React, while we use DjangoTranslations on the Backend.
Translations are stored in PO files, which are uploaded to Transifex at https://www.transifex.com/reustle-llc/zookeep/dashboard/ for translators to contribute. The push to Transifex happens at each deployment on CI.

Below you will find how to add translatable text in code and the commands to update translation files.
Once in a while, you will need to get updated translation files. Use `tx pull` command for that.

### Strategy

On Transifex, we make use of branches to allow features to be translated before deployment. We set it up so Transifex branches are tied to environments (i.e., not git branches). Below is the mapping:

Environment | Transifex branch
----------- | ----------------
dev.zookeep.com | dev
staging.zookeep.com | staging
app.zookeep.com | (default branch)

The usual flow is for the client to translate on the staging branch. Translation on the dev branch is mainly by request.

#### Example Flows

Translation not urgent

1. Developer merges feature (untranslated) into git `develop` branch. CI will trigger deployment to staging.zookeep.com and at the same time upload the untranslated source files to Transifex's staging branch. From here, it can already be deployed to app.zookeep.com if translation is not crucial to the feature.
2. Client translates the staging resources on Transifex.
3. Developer pulls the translation (`tx pull -b staging`) and commits to a new PR.
4. After merging and deploying to staging.zookeep.com, client can QA translations on site.
5. `develop` branch is merged into `master` and deployed to app.zookeep.com. At the same time, the Transifex default branch is updated by automatically with translations from staging.

Translation urgent

1. Developer deploys the feature branch to dev.zookeep.com via manual trigger. Option to push translation files is selected.
2. Client translates the dev resources on Transifex.
3. Developer pulls the translation (`tx pull -b dev`) and commits them in the feature branch (before merging to `develop`)

#### A few notes:

- Deployments to dev are manually triggered and translation files are *not* pushed by default. To push translation files, please refer to the settings on the Github UI while running the workflow.
- If there are translations to dev, it is the developer's task to pull the translations before merging 

### General

When making translatable strings, try _not_ to split them in parts, so
it can be properly translated.
```jsx
// bad
<div><Trans>To update it,</Trans><div>
<div><Trans>please go to this page</Trans></div>

// good
<Trans>
  <div>To update it,<div>
  <div>please go to this page</div>
</Trans>
```

For plurals (`no notifications`, `a new notification`, `10 new notifications`)
there are special ways to translate it:

LinguiJS: https://lingui.js.org/tutorials/react.html#plurals

Django: https://docs.djangoproject.com/en/2.2/topics/i18n/translation/#pluralization

### Frontend

[LinguiJS](https://lingui.js.org/) library is used for translation

To make component translatable:

in JSX code use `<Trans>` component like:
```jsx
import {Trans, t} from '@lingui/macro';

function MyComponent({x}) {
  return (
    <div>
      {/* JSX and variables can be used inside Trans: */}
      <Trans>My translatable title <b>{x}</b></Trans>
    </div>
  );
}

export default MyComponent;
```
in attributes or strings
```jsx
import {t} from '@lingui/macro';
import {withI18n} from '@lingui/react';

function MyComponent({i18n}) {
  return (
    <img
      src='...'
      alt={i18n._(t`Fun cat meme`)}
    />
  );
}

export default withI18n()(MyComponent);
```

When new translatable strings are added,
run `yarn run extract` to extract them into PO file.

When PO file is updated, you need to run `yarn run compile` to compile PO into JS.
If this step is skipped, you might see unformatted strings like `Candidate: {candidateName}`
in rendered components.

### Backend

```python
from django.utils.translation import ugettext_lazy as _

label = _('Agency accepted invitation')
```

When new translatable strings are added,
run `./django_makemessages.sh` to extract them into PO file.

Also PO file can be compiled into MO to speed up translation:
`python manage.py compilemessages` (automatically executed on deploy)

### PO -> CSV -> PO

https://github.com/marek-saji/po-csv

TODO: fork & fix adding `\n#, \n` (seems like empty comment, should be just `\n`)

to CSV:
```bash
$ node index.js messages.po > messages.csv
```

to PO:
```bash
$ node index.js messages.po messages.csv > messages1.po
$ rm -f messages.po
# replace `\n#, \n` with `\n` in the file
$ mv messages1.po messages.po
```

## Contributing

### Branching

| Environment | Branch    | URL                         |
| ----------- | --------- | --------------------------- |
| staging     | `develop` | https://staging.zookeep.com/|
| production  | `master`  | https://zookeep.com/        |

#### `develop`

New features and fixes are to be developed in new branches based from `develop` branch.
PRs need to be created to merge into `develop`, squashing all commits from the feature branch. Make sure to deploy `develop` into staging as soon as it's merged for accurate Sentry tracking.

#### `master`

As much as possible, only merge `develop` into `master` via a PR. If you're doing a hotfix to prod, remember to create a PR to both `develop` and `master`.

### Sentry

Merges to `develop` (for staging) and `master` (for prod) branches will automatically tag them on Sentry:

- staging: https://sentry.io/organizations/reustle-co/issues/?project=1456857
- production: https://sentry.io/organizations/reustle-co/issues/?project=1364802


### Deployment

Deployment is done via `fabfile.py`, locally and on CI. The codebase is built locally and then delivered as zip file to the server, unzipped and copied in the served folders.

A `.env` file is needed to deploy the project. The .env file must be present at the time of running `pipenv run` or `pipenv shell`. If you make changes after running `pipenv shell`, you will need to `deactivate` and re-activate the Pipenv venv in order to pick new values.


**Before running deploy**, you need to revert current branch DB migrations
to first common migration with branch you want to deploy
and switch git repo to this branch.
If you want to redeploy current branch with the latest changes,
no actions are needed in most of the cases. But if migrations were updated,
you need to revert current branch migrations first.

#### Production server
```
$ pipenv run fab deploy-production
```

#### Staging server
```
$ pipenv run fab deploy-staging
```

### First Deploy

TODO: make more verbose

Requirements: python3, pipenv, supervisord, nginx, rabbitmq

1. Copy configs from `./etc/` to `/etc/`
2. Create `settings.py` from `settings_prod_example.py`
3. Create `.env` file from `.evn.example`
4. `$ pipenv install`
5. Generate certs for `zookeep.com` via LetsEncrypt
6. Reread configs for supervisord, nginx

```
$ sudo supervisorctl reread
$ sudo supervisorctl update
$ sudo service nginx reload
```
=======
## Swagger API specification
Swagger API are not only used to provide the Swagger UI with API documentation, but also to provide definitions
for tables, validation and more. The specifications of the current version are at `./dashboard/src/swagger_specs.json`.
Whenever Django models changes, this document has to be recreated. 

To do so, run from the root:

`pipenv run python manage.py gen_swagger_react_env --mock-request --url http://127.0.0.1:9009/api --overwrite ./dashboard/src/swagger_specs.json`
