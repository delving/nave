import os
import re
import sys
from contextlib import contextmanager
from functools import wraps
from getpass import getpass, getuser
from glob import glob
from posixpath import join

import time
from django.utils import importlib
from fabric.api import env, cd, prefix, sudo as _sudo, run as _run, hide, task
from fabric.colors import yellow, green, blue, red
from fabric.contrib.files import exists, upload_template
from fabric.operations import put
from fabric.context_managers import settings as fab_settings

################
# Config setup #
################

conf = {}
if sys.argv[0].split(os.sep)[-1] in ("fab",  # POSIX
                                     "fab-script.py"):  # Windows
    # Ensure we import settings from the current dir
    try:
        settings = os.environ.get("DJANGO_SETTINGS_MODULE")
        conf = importlib.import_module(settings).FABRIC
        try:
            conf["ACC_HOSTS"][0]
        except (KeyError, ValueError):
            raise ImportError
    except (ImportError, AttributeError):
        print("Aborting, no hosts defined.")
        exit()

env.db_pass = conf.get("DB_PASS", None)
env.admin_pass = conf.get("ADMIN_PASS", None)
env.user = conf.get("SSH_USER", getuser())
env.password = conf.get("SSH_PASS", None)
env.key_filename = conf.get("SSH_KEY_PATH", None)
env.hosts = conf.get("ACC_HOSTS", [])

env.proj_name = conf.get("PROJECT_NAME", os.getcwd().split(os.sep)[-1])
env.venv_home = conf.get("VIRTUALENV_HOME", "/home/%s" % env.user)
env.org_id = conf.get("ORG_ID", None)
env.hub_node = conf.get("HUB_NODE", None)
env.email_host = conf.get("EMAIL_HOST", None)
env.file_watch_base_folder = conf.get("FILE_WATCH_BASE_FOLDER", "/mnt")
env.venv_path = "%s/%s" % (env.venv_home, env.proj_name)
env.proj_dirname = "project"
env.django_dirname = "%s/%s" % (env.proj_dirname, 'nave')
env.proj_path = "%s/%s" % (env.venv_path, env.proj_dirname)
env.django_path = "%s/%s/%s" % (env.venv_path, env.proj_dirname, 'nave')
env.process_num = 1
env.manage = "%s/bin/python %s/project/%s/manage.py" % (env.venv_path,
                                                        env.venv_path, 'nave')

env.live_host = conf.get("ACC_HOSTNAME", env.hosts[0] if env.hosts else None)
env.preferred_live_host = env.live_host.split(' ')[0]
env.repo_url = conf.get("REPO_URL", "")
env.project_repo_url = conf.get("PROJECT_REPO_URL", "")
env.git_branch = conf.get("GIT_BRANCH", "master")
env.git = env.repo_url.startswith("git") or env.repo_url.endswith(".git")
env.reqs_path = conf.get("REQUIREMENTS_PATH", None)
env.settings_path = conf.get("SETTINGS_PATH", None)
env.gunicorn_port = conf.get("GUNICORN_PORT", 8000)
env.narthex_port = conf.get("NARTHEX_PORT", 9000)
env.narthex_version = conf.get("NARTHEX_VERSION", '1.0.0-SNAPSHOT')
env.narthex_versions_dir = "%s/%s" % (env.venv_home, "NarthexVersions")
env.narthex_files = "%s/%s" % (env.venv_home, "NarthexFiles")
env.rdf_store_port = conf.get("RDF_STORE_PORT", 3030)
env.rdf_store_host = conf.get("RDF_STORE_HOST", "localhost")
env.oauth_id = conf.get("OAUTH_ID", None)
env.oauth_secret = conf.get("OAUTH_SECRET", None)
env.sentry_dsn = conf.get("SENTRY_DSN", None)
env.es_clustername = conf.get("ACC_ES_CLUSTERNAME")
env.rdf_base_url = "{}".format(conf.get("RDF_BASE_URL", 'localhost:8000'))
if "://" not in env.rdf_base_url:
    env.rdf_base_url = "http://{}".format(env.rdf_base_url)
env.locale = conf.get("LOCALE", "en_US.UTF-8")
env.nave_auth_token = conf['ACC_NAVE_AUTH_TOKEN']

env.secret_key = conf.get("SECRET_KEY", "")

OS_DEPENDENCIES = [
    'gcc',
    'build-essential',
    'autoconf',
    'libtool',
    'pkg-config',
    'git-core',
    'libjpeg-dev',
    'libpq-dev',
    'libxml2-dev',
    'zlib1g-dev',
    'libxslt1-dev',
    'memcached',
    'nginx',
    'iipimage-server',
    'postgresql-9.3-postgis-2.1',
    'python3',
    'python3-dev',
    'python3-pip',
    'python3-numpy',
    'python-dev',
    'python-pip',
    'python-setuptools',
    'rabbitmq-server',
    'oracle-java8-installer',
    'oracle-java7-installer',
    'oracle-java7-set-default',
    'libvips-tools',
    'imagemagick',
    'htop',
    'vim',
    'zip',
    'unzip',
    'supervisor',
    'gettext',
]

##################
# Template setup #
##################
os_dependencies_templates = {
    # "supervisor_init": {
    #     "local_path": "../deploy/supervisor_init.sh",
    #     "remote_path": "/etc/init.d/supervisord",
    #     "reload_command": "update-rc.d supervisord default; service supervisord restart",
    # },
    # "supervisord": {
    #     "local_path": "../deploy/supervisord.conf",
    #     "remote_path": "/etc/supervisor/supervisord.conf",
    #     # "reload_command": "supervisorctl reload",
    # },
    "fuseki_init": {
        "local_path": "../deploy/fuseki_init.sh",
        "remote_path": "/etc/init.d/fuseki",
        # "reload_command": "update-rc.d fuseki default; service supervisord restart",
    },
    "fuseki_test": {
        "local_path": "../deploy/fuseki_test.ttl",
        "remote_path": "/opt/fuseki/run/configuration/test.ttl",
        "reload_command": "update-rc.d fuseki default; service fuseki restart",
    },

}


# Each template gets uploaded at deploy time, only if their
# contents has changed, in which case, the reload command is
# also run.

templates = {
    "nginx": {
        "local_path": "../deploy/nginx.conf",
        "remote_path": "/etc/nginx/sites-enabled/%(proj_name)s.conf",
        # "reload_command": "service nginx restart",
    },
    "supervisor": {
        "local_path": "../deploy/supervisor.conf",
        "remote_path": "/etc/supervisor/conf.d/%(proj_name)s.conf",
        # "reload_command": "supervisorctl reload",
    },
    "fuseki-acceptance": {
        "local_path": "../deploy/fuseki_acceptance.ttl",
        "remote_path": "/opt/fuseki/run/configuration/%(proj_name)s_acceptance.ttl",
        "reload_command": "service fuseki restart",
    },
    "fuseki-production": {
        "local_path": "../deploy/fuseki_production.ttl",
        "remote_path": "/opt/fuseki/run/configuration/%(proj_name)s_production.ttl",
        "reload_command": "service fuseki restart",
    },
    "narthex_conf": {
       "local_path": "../deploy/narthex.conf",
       "remote_path": "%(narthex_files)s/narthex.conf",
       #"reload_command": "supervisorctl reload",
    },
    "narthex_logger": {
        "local_path": "../deploy/narthex_logger.xml",
        "remote_path": "%(narthex_files)s/logger.xml",
    },
    "wsgi": {
        "local_path": "../deploy/wsgi.py",
        "remote_path": "%(django_path)s/wsgi.py",
    },
    "gunicorn": {
        "local_path": "../deploy/gunicorn.conf.py",
        "remote_path": "%(django_path)s/gunicorn.conf.py",
    },
    "settings": {
        "local_path": "../deploy/live_settings.py",
        "remote_path": "%(django_path)s/projects/%(proj_name)s/local_settings.py",
    },
    "elastic_search": {
        "local_path": "../deploy/elasticsearch.yml",
        "remote_path": "/etc/elasticsearch/elasticsearch.yml",
        "reload_command": "service elasticsearch restart"
    },
}


######################################
# Context for virtualenv and project #
######################################

@contextmanager
def virtualenv():
    """
    Runs commands within the project's virtualenv.
    """
    with cd(env.venv_path):
        with prefix("source %s/bin/activate" % env.venv_path):
            yield


@contextmanager
def project():
    """
    Runs commands within the project's directory.
    """
    with virtualenv():
        with cd(env.django_dirname):
            yield


@contextmanager
def update_changed_requirements():
    """
    Checks for changes in the requirements file across an update,
    and gets new requirements if changes have occurred.
    """
    reqs_path = join(env.proj_path, env.reqs_path)
    get_reqs = lambda: run("cat %s" % reqs_path, show=False)
    old_reqs = get_reqs() if env.reqs_path else ""
    yield
    if old_reqs:
        new_reqs = get_reqs()
        if old_reqs == new_reqs:
            # Unpinned requirements should always be checked.
            for req in new_reqs.split("\n"):
                if req.startswith("-e"):
                    if "@" not in req:
                        # Editable requirement without pinned commit.
                        break
                elif req.strip() and not req.startswith("#"):
                    if not set(">=<") & set(req):
                        # PyPI requirement without version.
                        break
            else:
                # All requirements are pinned.
                return
        pip("-r %s/%s" % (env.proj_path, env.reqs_path))


###########################################
# Utils and wrappers for various commands #
###########################################

def _print(output):
    print()
    print(output)
    print()


def print_command(command):
    _print(blue("$ ", bold=True) +
           yellow(command, bold=True) +
           red(" ->", bold=True))


@task
def run(command, show=True):
    """
    Runs a shell comand on the remote server.
    """
    if show:
        print_command(command)
    with hide("running"):
        return _run(command)


@task
def sudo(command, show=True):
    """
    Runs a command as sudo.
    """
    if show:
        print_command(command)
    with hide("running"):
        return _sudo(command)


def log_call(func):
    @wraps(func)
    def logged(*args, **kawrgs):
        header = "-" * len(func.__name__)
        _print(green("\n".join([header, func.__name__, header]), bold=True))
        return func(*args, **kawrgs)
    return logged


def get_templates(templates_dict=templates):
    """
    Returns each of the templates with env vars injected.
    """
    injected = {}
    for name, data in templates_dict.items():
        injected[name] = dict([(k, v % env) for k, v in data.items()])
    return injected

@task
def upload_template_and_reload(name, templates_dict=templates):
    """
    Uploads a template only if it has changed, and if so, reload a
    related service.
    """
    template = get_templates(templates_dict=templates_dict)[name]
    local_path = template["local_path"]
    if not os.path.exists(local_path):
        project_root = os.path.dirname(os.path.abspath(__file__))
        local_path = os.path.join(project_root, local_path)
    remote_path = template["remote_path"]
    reload_command = template.get("reload_command")
    owner = template.get("owner")
    mode = template.get("mode")
    remote_data = ""
    if exists(remote_path):
        with hide("stdout"):
            remote_data = sudo("cat %s" % remote_path, show=False)
    with open(local_path, "r") as f:
        local_data = f.read()
        # Escape all non-string-formatting-placeholder occurrences of '%':
        local_data = re.sub(r"%(?!\(\w+\)s)", "%%", local_data)
        if "%(db_pass)s" in local_data:
            env.db_pass = db_pass()
        local_data %= env
    clean = lambda s: s.replace("\n", "").replace("\r", "").strip()
    if clean(remote_data) == clean(local_data):
        return
    # print(local_path)
    # print(remote_path)
    # print(env)
    upload_template(local_path, remote_path, env, use_sudo=True, backup=False)
    if owner:
        sudo("chown %s %s" % (owner, remote_path))
    if mode:
        sudo("chmod %s %s" % (mode, remote_path))
    if reload_command:
        sudo(reload_command)


def db_pass():
    """
    Prompts for the database password if unknown.
    """
    if not env.db_pass:
        env.db_pass = getpass("Enter the database password: ")
    return env.db_pass


@task
def apt(packages, remove=False):
    """
    Installs one or more system packages via apt.
    """
    verb = "install" if not remove else "remove"
    return sudo("apt-get {verb} -y -q ".format(verb=verb) + packages)


@task
def pip(packages):
    """
    Installs one or more Python packages within the virtual environment.
    """
    with virtualenv():
        return sudo("pip3 install %s" % packages)


def postgres(command):
    """
    Runs the given command as the postgres user.
    """
    show = not command.startswith("psql")
    return run("sudo -u postgres %s" % command, show=show)


@task
def psql(sql, show=True):
    """
    Runs SQL against the project's database.
    """
    out = postgres('psql -c "%s"' % sql)
    if show:
        print_command(sql)
    return out


@task
def backup(filename):
    """
    Backs up the database.
    """
    return postgres("pg_dump -Fc %s > %s" % (env.proj_name, filename))


@task
def restore(filename):
    """
    Restores the database.
    """
    return postgres("pg_restore -c -d %s %s" % (env.proj_name, filename))


@task
def python(code, show=True):
    """
    Runs Python code in the project's virtual environment, with Django loaded.
    """
    setup = "import os; os.environ[\'DJANGO_SETTINGS_MODULE\']=\'{}\';".format(settings)
    full_code = 'python -c "%s%s"' % (setup, code.replace("`", "\\\`"))
    with project():
        result = run(full_code, show=False)
        if show:
            print_command(code)
    return result


def static():
    """
    Returns the live STATIC_ROOT directory.
    """
    return python("from django.conf import settings;"
                  "print(settings.STATIC_ROOT)", show=False).split("\n")[-1]


@task
def manage(command):
    """
    Runs a Django management command.
    """
    return run("%s %s" % (env.manage, command))


#########################
# Install and configure #
#########################

env.no_keys = True

@task
@log_call
def install():
    """
    Installs the base system and Python requirements for the entire server.
    """
    locale = "LC_ALL=%s" % env.locale
    with hide("stdout"):
        if not exists("/etc/default/locale"):  # or locale not in sudo("cat /etc/default/locale"):
            sudo("locale-gen %s" % locale)
            sudo("update-locale %s" % locale)
            sudo("dpkg-reconfigure locales")
            run("exit")
    apt('software-properties-common')
    sudo("add-apt-repository ppa:webupd8team/java -y")
    # sudo("add-apt-repository ppa:fkrull/deadsnakes -y")
    sudo("apt-get update -y -q")
    sudo("apt-get install -y python-software-properties debconf-utils")
    sudo('echo "oracle-java8-installer shared/accepted-oracle-license-v1-1 select true" | sudo debconf-set-selections')
    sudo('echo "oracle-java7-installer shared/accepted-oracle-license-v1-1 select true" | sudo debconf-set-selections')
    apt(" ".join(OS_DEPENDENCIES))
    sudo("pip2 install virtualenv virtualenvwrapper mercurial")  # supervisor when not installed via apt-get
    sudo("pip3 install virtualenv virtualenvwrapper")
    sudo("mkdir -p /etc/supervisor/conf.d")
    sudo('mkdir -p /opt/fuseki/run/configuration')
    sudo('mkdir -p /var/log/celery')
    run('mkdir -p {}'.format(os.path.join(env.venv_home, "NarthexFiles")))
    for name, items in get_templates(templates_dict=os_dependencies_templates).items():
        put(local_path=items['local_path'], remote_path=items['remote_path'], use_sudo=True,  mode=0o755)
    install_fuseki()
    install_elasticsearch()
    upload_template(
        "../deploy/supervisor_iipimageserver.conf",
        "/etc/supervisor/conf.d/iip_image_server.conf",
        env,
        use_sudo=True,
        backup=False
    )


@task
@log_call
def reload_supervisor():
    sudo("supervisorctl reload")


@task
@log_call
def install_fuseki():
    """
    Install Apache fuseki with its base configuration.
    """
    fuseki_version = "2.3.0"
    with cd("/tmp"):
        if not exists('/opt/fuseki/fuseki-server.jar'):
            sudo('wget -q http://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-{}.zip'.format(fuseki_version))
            sudo('tar xvzf apache-jena-fuseki-{}.tar.gz'.format(fuseki_version))
            sudo('mkdir -p /opt/fuseki/run/configuration/')
            sudo('mv apache-jena-fuseki-{}/* /opt/fuseki/'.format(fuseki_version))
            for name, items in get_templates(templates_dict=os_dependencies_templates).items():
                put(local_path=items['local_path'], remote_path=items['remote_path'], use_sudo=True,  mode=0o755)
            sudo('rm -rf /etc/default/fuseki')
            sudo('echo "FUSEKI_HOME=/opt/fuseki" >> /etc/default/fuseki')
            sudo('echo "FUSEKI_BASE=/opt/fuseki/run" >> /etc/default/fuseki')
            sudo('echo "JAVA=/usr/lib/jvm/java-8-oracle/jre/bin/java" >> /etc/default/fuseki')
            #sudo('echo "JAVA_OPTIONS="-Xmx2400M" >> /etc/default/fuseki')
            sudo("update-rc.d fuseki defaults 95 10")
            sudo("/etc/init.d/fuseki restart")


@task
@log_call
def install_elasticsearch():
    """Install elastic search."""
    __version__ = "1.7.4"
    sudo("wget -q https://download.elastic.co/elasticsearch/elasticsearch/elasticsearch-{}.deb".format(__version__))
    sudo("dpkg -i elasticsearch-{}.deb".format(__version__))
    sudo("update-rc.d elasticsearch defaults 95 10")
    link = "https://github.com/triforkams/geohash-facet/releases/download/geohash-facet-0.0.19/geohash-facet-0.0.19.jar"
    sudo("/usr/share/elasticsearch/bin/plugin --url {} --install geohash-facet".format(link))
    sudo("service elasticsearch start")
    sudo("rm elasticsearch-{}.deb".format(__version__))


@task
@log_call
def install_blazegraph():
    """Install elastic search."""
    __version__ = "2.0.0"
    sudo("http://sourceforge.net/projects/bigdata/files/bigdata/{}/blazegraph.deb/download blazegraph.deb".format(__version__))
    sudo("dpkg -i blazegraph.deb")
    sudo("rm blazegraph.deb".format(__version__))


@task
@log_call
def remove_os_dependencies():
    apt(" ".join(OS_DEPENDENCIES), remove=True)


@task
@log_call
def install_os_dependencies():
    apt(" ".join(OS_DEPENDENCIES), remove=False)


@task
@log_call
def deploy_narthex():
    """
    First installation of Narthex
    """
    narthex_factory = os.path.join(env.venv_home, "NarthexFiles", env.org_id, "factory", "edm")
    if not exists(env.narthex_versions_dir):
        run("mkdir %s" % env.narthex_versions_dir)
    if not exists(os.path.join(env.venv_home, "NarthexFiles")):
        run("mkdir -p {}".format(narthex_factory))
    if not exists(narthex_factory):
        run("mkdir -p {}".format(narthex_factory))
    with cd(env.narthex_versions_dir):
        run("rm -rf *")
        run("wget 'http://artifactory.delving.org/artifactory/simple/delving/narthex/narthex-{}.zip'".format(
            env.narthex_version
        ))
        run("unzip narthex-{version}.zip".format(version=env.narthex_version))
    with cd(narthex_factory):
        run('rm -rf *.xml *.xsd')
        run("wget https://raw.githubusercontent.com/delving/schemas.delving.eu/master/edm/edm_5.2.6_record-definition.xml")
        run("wget https://raw.githubusercontent.com/delving/schemas.delving.eu/master/edm/edm_5.2.6_validation.xsd")
    sudo("supervisorctl restart %s:narthex" % env.proj_name)
    return True


@task
@log_call
def create_nginx_certificates():
    """
    Create the NGINX certificates
    """
    # Set up SSL certificate.
    conf_path = "/etc/nginx/conf"
    if not exists(conf_path):
        sudo("mkdir -p %s" % conf_path)
    with cd(conf_path):
        crt_file = env.proj_name + ".crt"
        key_file = env.proj_name + ".key"
        if not exists(crt_file) and not exists(key_file):
            try:
                crt_local, = glob(join("deploy", "*.crt"))
                key_local, = glob(join("deploy", "*.key"))
            except ValueError:
                parts = (crt_file, key_file, env.live_host)
                sudo("openssl req -new -x509 -nodes -out %s -keyout %s "
                     "-subj '/CN=%s' -days 3650" % parts)
            else:
                upload_template(crt_local, crt_file, use_sudo=True)
                upload_template(key_local, key_file, use_sudo=True)
    return True


@task
@log_call
def refresh_templates():
    print('starting ...')
    for name in get_templates():
        upload_template_and_reload(name)


@task
@log_call
def setup_project(local=False):
    upload_template_and_reload("elastic_search")
    if not local:
        upload_template_and_reload("settings")
    upload_template_and_reload("fuseki-acceptance")
    upload_template_and_reload("fuseki-production")
    with project():
        if env.reqs_path:
            with fab_settings(warn_only=False):
                pip("-r %s/%s" % (env.proj_path, env.reqs_path))
        pip("gunicorn setproctitle psycopg2 django-compressor python3-memcached")
        manage("syncdb --noinput")
        python("import django;"
               "django.setup();"
               "from django.conf import settings;"
               "from django.contrib.sites.models import Site;"
               "site, _ = Site.objects.get_or_create(id=settings.SITE_ID);"
               "site.domain = '" + env.live_host + "';"
                                                   "site.save();")
        if env.admin_pass:
            pw = env.admin_pass
            user_py = ("import django;"
                       "django.setup();"
                       "from django.contrib.auth.models import User;"
                       "u, _ = User.objects.get_or_create(username='admin');"
                       "u.is_staff = u.is_superuser = True;"
                       "u.set_password('%s');"
                       "u.save();" % pw)
            python(user_py, show=False)
            shadowed = "*" * len(pw)
            print_command(user_py.replace("'%s'" % pw, "'%s'" % shadowed))
        python("import django;"
               "django.setup();"
               "from django.conf import settings;"
               "from rest_framework.authtoken.models import Token;"
               "from django.contrib.auth.models import User;"
               "u, _ = User.objects.get_or_create(username='admin');"
               "Token.objects.get_or_create(user=u, key='{}');".format(env.nave_auth_token)
               )
    return True


@task
@log_call
def create_venv():
    # Create virtualenv
    with cd(env.venv_home):
        print(env.venv_home)
        if exists(env.proj_name):
            prompt = raw_input("\nVirtualenv exists: %s\nWould you like "
                               "to replace it? (yes/no) " % env.proj_name)
            if prompt.lower() != "yes":
                print("\nAborting!")
                return False
            remove()
        run("/usr/local/bin/virtualenv --system-site-packages -p python3 %s --distribute" % env.proj_name)
        vcs = "git" if env.git else "hg"
        run("%s clone %s %s" % (vcs, env.repo_url, env.proj_path))
        # close private project
        run("%s clone %s %s/nave/projects/%s" % (vcs, env.project_repo_url, env.proj_path, env.proj_name))
        with project():
            run("%s fetch" % vcs)
            run("%s checkout %s" % (vcs, env.git_branch))


@task
@log_call
def create_db():
    pw = db_pass()
    user_sql_args = (env.proj_name, pw.replace("'", "\'"))
    user_sql = "CREATE USER %s WITH ENCRYPTED PASSWORD '%s';" % user_sql_args
    psql(user_sql, show=False)
    shadowed = "*" * len(pw)
    print_command(user_sql.replace("'%s'" % pw, "'%s'" % shadowed))
    psql("CREATE DATABASE %s WITH OWNER %s ENCODING = 'UTF8' "
         "LC_CTYPE = '%s' LC_COLLATE = '%s' TEMPLATE template0;" %
         (env.proj_name, env.proj_name, env.locale, env.locale))
    # make the database gis enabled
    postgres('psql -d %s -c "CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology;"' % env.proj_name)


@task
@log_call
def drop_db():
    try:
        psql("DROP DATABASE %s;" % env.proj_name)
        psql("DROP USER %s;" % env.proj_name)
    except Exception as e:
        print(e)


@task
@log_call
def create():
    """
    Create a new virtual environment for a project.
    Pulls the project's repo from version control, adds system-level
    configs for the project, and initialises the database with the
    live host.
    """
    create_venv()
    #
    create_nginx_certificates()
    # Create DB and DB user.
    create_db()
    # Set up project.
    setup_project()
    return True

@task
@log_call
def create_dev():
    """
    Create a new virtual environment for a project.
    Pulls the project's repo from version control, adds system-level
    configs for the project, and initialises the database with the
    live host.
    """
    # link venv
    venv_dirs = ['bin', 'djcelery', 'include', 'lib', 'pip-selfcheck.json', 'share']
    for fname in venv_dirs:
        run("rm -rf /home/vagrant/{}/{}".format(env.proj_name, fname))
    run('ln -s /home/vagrant/.virtualenvs/%s/* /home/vagrant/%s/' % (env.proj_name, env.proj_name))
    #
    create_nginx_certificates()
    # Create DB and DB user.
    create_db()
    # Set up project.
    time.sleep(10)
    setup_project(local=True)
    return True


@task
@log_call
def remove():
    """
    Blow away the current project.
    """
    if exists(env.venv_path):
        sudo("rm -rf %s" % env.venv_path)
    for template in get_templates().values():
        remote_path = template["remote_path"]
        if exists(remote_path):
            sudo("rm %s" % remote_path)
    try:
        psql("DROP DATABASE %s;" % env.proj_name)
        psql("DROP USER %s;" % env.proj_name)
    except Exception as e:
        print(e)


##############
# Deployment #
##############

@task
@log_call
def restart():
    """
    Restart gunicorn worker processes for the project.
    """
    pid_path = "%s/gunicorn.pid" % env.django_path
    if exists(pid_path):
        sudo("kill -HUP `cat %s`" % pid_path)
    else:
        start_args = (env.proj_name, env.proj_name)
        sudo("supervisorctl reload")
        sudo("service nginx restart")
        start_command = "supervisorctl start %s:gunicorn_%s" % start_args
        # sudo(start_command)
        print("if you see 'out: %s:gunicorn_%s: ERROR (no such process)' you must run `fab reload_supervisor` and then run `fab restart` again." % (env.proj_name, env.proj_name, start_command))


@task
@log_call
def restart_celery():
    """
    Restart celery worker processes for the project.
    """
    sudo("supervisorctl restart %s_celery" % env.proj_name)


@task
@log_call
def deploy_dev():
    """
    Deploy latest version of the project.
    Check out the latest version of the project from version
    control, install new requirements, sync and migrate the database,
    collect any new static assets, and restart gunicorn's work
    processes for the project.
    """
    dev_templates = templates.copy()
    dev_templates["supervisor"] = {
                                  "local_path": "../deploy/supervisor_dev.conf",
                                  "remote_path": "/etc/supervisor/conf.d/%(proj_name)s.conf",
                                  # "reload_command": "supervisorctl reload",
                              }
    del dev_templates['settings']
    for name in get_templates(templates_dict=dev_templates):
        upload_template_and_reload(name, dev_templates)
    time.sleep(10)
    with project():
        # backup("last.db")
        static_dir = static()
        manage("collectstatic -v 0 --noinput")
        manage("compilemessages")
        manage("syncdb --noinput")
        manage("migrate --noinput")
    sudo("supervisorctl reload")
    sudo("service nginx restart")
    return True

@task
@log_call
def deploy():
    """
    Deploy latest version of the project.
    Check out the latest version of the project from version
    control, install new requirements, sync and migrate the database,
    collect any new static assets, and restart gunicorn's work
    processes for the project.
    """
    if not exists(env.venv_path):
        prompt = raw_input("\nVirtualenv doesn't exist: %s\nWould you like "
                           "to create it? (yes/no) " % env.proj_name)
        if prompt.lower() != "yes":
            print("\nAborting!")
            return False
        create()
    for name in get_templates():
        upload_template_and_reload(name)
    with project():
        # backup("last.db")
        static_dir = static()
        if exists(static_dir):
            sudo("tar -cf last.tar %s" % static_dir)
        git = env.git
        last_commit = "git rev-parse HEAD" if git else "hg id -i"
        run("%s > last.commit" % last_commit)
        with update_changed_requirements():
            run("git checkout {}".format(env.git_branch))
            run("git pull origin {} -f".format(env.git_branch) if git else "hg pull && hg up -C")
        manage("collectstatic -v 0 --noinput")
        manage("compilemessages")
        manage("syncdb --noinput")
        manage("migrate --noinput")
    restart()
    return True


@task
@log_call
def rollback():
    """
    Reverts project state to the last deploy.
    When a deploy is performed, the current state of the project is
    backed up. This includes the last commit checked out, the database,
    and all static files. Calling rollback will revert all of these to
    their state prior to the last deploy.
    """
    with project():
        with update_changed_requirements():
            update = "git checkout" if env.git else "hg up -C"
            run("%s `cat last.commit`" % update)
        with cd(join(static(), "..")):
            run("tar -xf %s" % join(env.proj_path, "last.tar"))
        restore("last.db")
    restart()


@task
@log_call
def migrate_db():
    with project():
        restore("last.db")


@task
def prod():
    env.hosts = conf.get("PROD_HOSTS", [])
    env.live_host = conf.get("PROD_HOSTNAME", env.hosts[0] if env.hosts else None)
    env.preferred_live_host = env.live_host.split(' ')[0] if env.live_host else None
    env.es_clustername = conf.get("PROD_ES_CLUSTERNAME")
    env.nave_auth_token = conf['PROD_NAVE_AUTH_TOKEN']


@task
@log_call
def run_all():
    """
    Installs everything required on a new system and deploy.
    From the base software, up to the deployed project.
    """
    install()
    if create():
        deploy()
