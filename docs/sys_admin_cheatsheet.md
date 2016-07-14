# SysAdmin commands Delving Hub3

## Nginx (port: 80)

    $ /etc/init.d/nginx restart

## ElasticSearch (port: 9200)

    $ /etc/init.d/elasticsearch restart

## Fuseki (port: 3030)

    $ /etc/init.d/fuseki restart

## RabbitMQ (port: 15672)

    $ /etc/init.d/activemq restart

## Postgresql (port: 5432)

    $ /etc/init.d/postgresql restart

## Supervisorctl 

We use supervisorctl to manage all custom deamonized processes that are not managed throught init.d.

List all processes

    $ sudo supervisorctl status

Manage running processes

    $ sudo supervisorctl restart|start|stop <process_name>

Tail the logs

    $ sudo supervisorctl tail -f <process_name>

Restart all

    $ sudo supervisorctl restart all 

## Configuration locations (based on ansible deployment)

* supervisor: 
    * config: /etc/supervisord/conf.d
    * logs: /var/log/hub3
* elasticsearch: 
    * config: /etc/elasticsearch
    * data: /var/lib/elasticsearch
    * logs: /var/log/elasticsearch
* nginx: 
    * config: /etc/nginx
    * logs: /var/log/nginx
* fuseki: 
    * config: /etc/fuseki, /opt/hub3/fuseki/run
    * data: /opt/hub3/fuseki/run/databases
    * logs: /opt/hub3/fuseki/run/logs 
