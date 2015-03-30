#!/usr/bin/env python
# encoding: utf-8

import os
import logging

import skiff


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
        self._skiff = skiff.rig(token)

        if logger is None:
            create_logger()

    def _get_snapshots(self):
        """
        Return the available snapshots.
        NOTE: snapshots are images and we can filter them since they are not
        public.

        :rtype: list
        """
        images = self._skiff.Image.all()
        private_images = filter(lambda i: not i.public, images)

        return private_images

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

        droplet = self._skiff.Droplet.get(droplet_name)

        if not droplet:
            logger.error('There is no such droplet.')
            return

        snapshots = self._get_snapshots()

        try:
            thesnapshot = next((s for s in snapshots if s.name == snapshot_name))
            thesnapshot.delete()
            logger.debug('Previous snapshot destroyed.')
        except:
            # TODO: specify the exception to catch here when there's no
            # snapshot do destroy.
            pass  # There is no image to destroy

        try:
            droplet.shutdown()
            logger.debug('Shutting down droplet.')
            droplet.wait_till_done()
            logger.debug('Droplet powered off.')
        except:
            pass  # already powered off

        droplet.snapshot(snapshot_name)
        logger.debug('Creating snapshot.')
        droplet.wait_till_done()
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

        snapshots = self._get_snapshots()

        # NOTE: this assumes that we hay just one key and/or we want to use the
        # first one
        keys = self._skiff.Key.all()
        key = keys[0]

        try:
            thesnapshot = next((s for s in snapshots if s.name == snapshot_name))
        except StopIteration:
            logger.warning('Using default snapshot')
            thesnapshot = snapshots[0]
            # Q: do we use the first one no matter which one it is?

        droplet = self._skiff.Droplet.create(name=droplet_name,
                                             region='nyc3',
                                             size='512mb',
                                             image=thesnapshot.id,
                                             ssh_keys=[key])

        # wait until droplet is created
        droplet.wait_till_done()
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
        droplet = self._skiff.Droplet.get(droplet_name)
        droplet.destroy()
        droplet.wait_till_done()

    def test(self):
        droplet_name = 'coreos-01'
        print self._skiff.Key.all()
        print self._skiff.Image.all()
        print self._get_snapshots()
        droplet = self._skiff.Droplet.get(droplet_name)
        ip = droplet.v4[0].ip_address
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
    dm.test()
    # dm.backup('coreos-01')
    # dm.destroy('workstation')

if __name__ == '__main__':
    main()
