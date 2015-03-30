Droplet Manager
===============

A manager for DigitalOcean doplets (virtual machines).


This work is inspired on https://github.com/nicopace/DO_remote_workstation.git


Usage
-----

To use this manager you need to provide a valid token for your DigitalOcean account.

You can get your it on https://cloud.digitalocean.com/settings/applications

Save your toke into the `digitalocean.token` file or set the `DO_KEY`
environment variable with your token as the value. The `DO_KEY` setting has
priority over the file.


Dependencies
------------

The dependencies are listed on the `requirements.txt` file.

NOTE: to avoid requests warnings for ssl see
http://stackoverflow.com/a/29099439/687989
