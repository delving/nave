Upgrading Postgresql from 9.1 to 9.2
====================================


    echo "deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main" | sudo tee /etc/apt/sources.list.d/postgis.list
    wget --quiet -O - http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc | sudo apt-key add -
    sudo apt-get update
    sudo apt-get install postgresql-9.3 postgresql-9.3-postgis-2.1 postgresql-client-9.3

    sudo su -l postgres
    psql -d template1 -p 5433
    CREATE EXTENSION IF NOT EXISTS hstore;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    service postgresql stop
    /usr/lib/postgresql/9.2/bin/pg_upgrade -b /usr/lib/postgresql/9.1/bin -B /usr/lib/postgresql/9.2/bin -d /var/lib/postgresql/9.1/main/ -D /var/lib/postgresql/9.2/main/ -O "-c config_file=/etc/postgresql/9.2/main/postgresql.conf" -o "-c config_file=/etc/postgresql/9.1/main/postgresql.conf"

    logout # logout postgresql back to previous user

    sudo apt-get remove postgresql-9.1
    sudo vim /etc/postgresql/9.2/main/postgresql.conf # change port to 5432
    sudo service postgresql restart