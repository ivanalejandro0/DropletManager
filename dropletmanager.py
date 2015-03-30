#!/usr/bin/env python
# encoding: utf-8

import os
import logging

import digitalocean


def create_logger():
    """Create logger and formatter"""
    global logger
    LOG_FORMAT = ('%(asctime)s - %(levelname)-8s - '
                  'L#%(lineno)-4s : %(name)s:%(funcName)s() - %(message)s')
    logger = logging.getLogger(name='DropletManager')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(LOG_FORMAT)

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)

    logger.addHandler(console)
    logger.debug('Console handler plugged!')

logger = None


class DropletManager(object):
    """Droplet manager for DigitalOcean."""

    def __init__(self, token):
        """
        Create the DropletManager object using the `token` given as parameter.
        If there is no token or is not a valid one this will raise KeyError.
        """
        # TODO: check for valid token?
        self._manager = digitalocean.Manager(token=token)

        if logger is None:
            create_logger()

    def _get_snapshots(self):
        """
        Return the available snapshots.
        NOTE: snapshots are images and we can filter them since they are not
        public.

        :rtype: list
        """
        images = self._manager.get_my_images()
        private_images = filter(lambda i: not i.public, images)

        return private_images

    def _get_droplet(self, name):
        droplet = None

        for d in self._manager.get_all_droplets():
            if d.name == name:
                droplet = d
                break

        return droplet

    def _get_image(self, name):
        image = None

        for i in self._manager.get_all_images():
            if i.name == name:
                image = i
                break

        return image

    def backup(self, droplet_name, snapshot_name=None):
        """
        Create a snapshot for `droplet_name` named `snapshot_name` or
        `droplet_name`_snapshot in case you don't specify a snapshot name to
        use.

        :param droplet_name: the name of the droplet to backup.
        :type droplet_name: str
        :param snapshot_name: the name of the snapshot that will be created.
        :type snapshot_name: str
        """
        if snapshot_name is None:
            snapshot_name = droplet_name + '_snapshot'

        droplet = self._get_droplet(droplet_name)

        if droplet is None:
            logger.error('There is no such droplet.')
            return

        snapshot = self._get_image(snapshot_name)

        if snapshot is not None:
            snapshot.destroy()  # TODO: check if this method exists
            logger.debug('Previous snapshot destroyed.')

        try:
            droplet.shutdown()
            logger.debug('Shutting down droplet.')
            droplet.wait_till_done()  # This may not exist on 'python-digitalocean'
            logger.debug('Droplet powered off.')
        except:
            pass  # already powered off

        droplet.take_snapshot(snapshot_name)
        logger.debug('Creating snapshot.')
        droplet.wait_till_done()  # This may not exist on 'python-digitalocean'
        logger.debug('Snapshot created.')

    def restore(self, droplet_name, snapshot_name=None):
        """
        Restore a snapshot for `droplet_name` named `snapshot_name` or
        `droplet_name`_snapshot in case you don't specify a snapshot name to
        use.

        :param droplet_name: the name of the droplet to backup.
        :type droplet_name: str
        :param snapshot_name: the name of the snapshot that will be created.
        :type snapshot_name: str
        """
        if snapshot_name is None:
            snapshot_name = droplet_name + '_snapshot'

        snapshot = self._get_image(snapshot_name)

        if snapshot is None:
            raise Exception("No existing snapshots found with the given name.")

        # NOTE: this assumes that we hay just one key and/or we want to use the
        # first one
        keys = self._manager.get_all_sshkeys()
        key = keys[0]

        # TODO: test this code
        droplet = digitalocean.Droplet(token=self._token,
                                       name=droplet_name,
                                       region='nyc3',
                                       image=snapshot_name,
                                       size_slug='512mb')
        droplet.create()

        droplet = self._skiff.Droplet.create(name=droplet_name,
                                             region='nyc3',
                                             size='512mb',
                                             image=thesnapshot.id,
                                             ssh_keys=[key])

        # wait until droplet is created
        droplet.wait_till_done()  # This may not exist on 'python-digitalocean'
        # refresh network information
        droplet = droplet.refresh()
        droplet = droplet.reload()

        logger.debug("New droplet ip: {0}".format(droplet.v4[0].ip_address))

    def destroy(self, droplet_name):
        """
        Destroy a droplet named `droplet_name`.

        :param droplet_name: the name of the droplet to backup.
        :type droplet_name: str
        """
        droplet = self._get_droplet(droplet_name)
        droplet.destroy()
        droplet.wait_till_done()  # This may not exist on 'python-digitalocean'

    def test(self):
        droplet_name = 'coreos-01'
        print self._manager.get_all_sshkeys()
        print self._manager.get_my_images()
        ip = self._get_droplet(droplet_name).ip_address
        logger.debug("Droplet 'coreos-01' ip: {0}".format(ip))


def main():

    token = os.environ.get('DO_KEY', None)

    if token is None:
        try:
            with open('digitalocean.token', 'r') as f:
                token = f.read()
        except:
            pass

    if token is None:
        print('Environment variable DO_KEY is not defined. '
              'You can get your DigitalOcean token on '
              'https://cloud.digitalocean.com/settings/applications '
              'and to Pesonal Access Tokens.')
        exit(1)

    create_logger()
    dm = DropletManager(token)
    # dm.test()
    # dm.backup('coreos-01')
    # dm.destroy('workstation')

if __name__ == '__main__':
    main()
