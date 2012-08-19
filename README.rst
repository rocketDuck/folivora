Folivora
========

.. image:: https://secure.travis-ci.org/rocketDuck/folivora.png?branch=master
    :alt: Build Status
    :target: http://travis-ci.org/rocketDuck/folivora

Folivora is your new tool which never lets you forget about package updates.
You define your projects and dependencies and once a new release hits PyPi
Folivora will notify you.

A hosted version is available on `heroku`_ (username/password is demo/demo,
although to get notifications you should register on your own) and you
can try it our yourself (in a venv)::

    git clone git://github.com/rocketDuck/folivora.git
    cd folivora
    pip install -r requirements.txt
    python manage.py syncdb

The default settings expect a postgres server on localhost with a database
named folivora (postgres is a requirement due to the usage of hstore). You
also need to run an initial sync with PyPi to fetch the package names::

    PYTHONPATH=. DJANGO_SETTINGS_MODULE=example.settings ./extra/sync.py

After that changes are fetched via celery. To run the project use::

    foreman start -f Procfile.development

.. _`heroku`: http://folivora.herokuapp.com

