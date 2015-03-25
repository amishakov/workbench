from fabric.api import cd, env, local, run, task


env.forward_agent = True
env.hosts = ['deploy@workbench.feinheit.ch']


@task
def deploy():
    local('flake8 .')
    local('git push origin master')

    with cd('www/workbench/'):
        run('git checkout master')
        run('git fetch origin')
        run('git merge --ff-only origin/master')
        run('find . -name "*.pyc" -delete')
        run('venv/bin/pip install -r requirements/production.txt')
        run('venv/bin/python manage.py migrate')
        run('venv/bin/python manage.py collectstatic --noinput')
        run('sudo service www-workbench restart')


@task
def pull_database():
    local('dropdb --if-exists workbench')
    local('createdb --encoding UTF8 workbench')
    local(
        'ssh root@workbench.feinheit.ch "sudo -u postgres pg_dump workbench'
        ' --no-privileges --no-owner --no-reconnect"'
        ' | psql workbench')


@task(alias='mm')
def makemessages():
    local('venv/bin/python manage.py makemessages -a -i venv -i htmlcov')
