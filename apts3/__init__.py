#   Copyright 2016 Jamie Cressey
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os.path
import boto3
import botocore.exceptions
import logging
import sys
import json
import pwd
import os
import apt.resources
from datetime import datetime, timedelta
from time import sleep


__author__ = 'Jamie Cressey'
__version__ = '0.9.0'


class AptS3(object):

    def __init__(self, args):
        self.log = self._logger()
        self.args = args
        self.debs = args.files.split()

        if args.action == 'upload':
            self.upload_debs()
        elif args.action == 'delete':
            self.delete_debs()
        else:
            self.log.error('Unknown command: {}'.format(args.action))

    def _logger(self):
        log = logging.getLogger('apt-s3')
        log.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s %(levelname)-8s %(name)s: %(message)s',
                '%Y-%m-%d %H:%M:%S'))
        log.addHandler(handler)

        return log

    def _s3_conn(self):
        boto3.setup_default_session(
            profile_name=self.args.profile,
            region_name=self.args.region)

        self.s3 = boto3.client('s3')

    def _check_debs_exist(self, deb):
        if not os.path.isfile(deb):
            self.log.error('File {0} doesn\'t exist'.format(deb))
            exit(1)

    def _check_lock(self, arch):
        if self.args.lock:
            lockfile = 'dists/{0}/{1}/binary-{2}/apts3_lockfile'.format(
                self.args.codename, self.args.component, arch)

            ts_now = datetime.utcnow()
            ts_stop = ts_now + timedelta(seconds=self.args.lock_timeout)

            while ts_now < ts_stop:
                try:
                    lock = self.s3.get_object(
                        Bucket=self.args.bucket,
                        Key=lockfile)

                    lock_body = json.loads(lock['Body'].read())
                    self.log.info(
                        "Repository is locked by another user: {0}@{1}".format(
                            lock_body['user'], lock_body['host']))

                    ts_now = datetime.utcnow()
                    ts_lock = lock['LastModified'].replace(tzinfo=None)
                    ts_diff = ts_now - ts_lock
                    if ts_diff.seconds > self.args.lock_timeout:
                        self.log.error(
                            'Repository lock is too old: {}. Please investigate.'.format(ts_diff))
                        exit(1)

                    sleep(10)

                except botocore.exceptions.ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchKey':
                        break
                    else:
                        raise

            self.log.info("Attempting to obtain a lock")
            lock_body = json.dumps({
                "user": pwd.getpwuid(os.getuid()).pw_name,
                "host": os.uname()[1]
            })

            self.s3.put_object(
                Body=lock_body,
                Bucket=self.args.bucket,
                Key=lockfile)
            self.log.info("Locked repository for updates")

    def _delete_lock(self, arch):
        if self.args.lock:
            self.log.info('Removing lockfile')
            lockfile = 'dists/{0}/{1}/binary-{2}/apts3_lockfile'.format(
                self.args.codename, self.args.component, arch)
            self.s3.delete_object(
                Bucket=self.args.bucket,
                Key=lockfile)

    def _parse_manifest(self, arch):
        self.manifests[arch] = apt.resources.Manifest(
            bucket=self.args.bucket,
            codename=self.args.codename,
            component=self.args.component,
            architecture=arch,
            visibility=self.args.visibility,
            s3=self.s3)

    def _parse_package(self, deb):
        self.log.info("Examining package file {}".format(deb))
        pkg = apt.resources.Package(deb)
        if self.args.arch:
            arch = self.args.arch
        elif pkg.architecture:
            arch = pkg.architecture
        else:
            self.log.error(
                "No architcture given and unable to determine one for {0}. Please specify one with --arch [i386|amd64].".format(deb))
            exit(1)

        if arch == 'all' and len(self.manifests) == 0:
            self.log.error(
                'Package {0} had architecture "all" however noexisting package lists exist. This can often happen if the first package you are add to a new repository is an "all" architecture file. Please use --arch [i386|amd64] or another platform type to upload the file.'.format(deb))
            exit(1)

        if arch not in self.manifests:
            self._parse_manifest(arch)

        self.manifests[arch].add(pkg)

        if arch == 'all':
            self.packages_arch_all.append(pkg)

    def _update_manifests(self):

        for arch, manifest in self.manifests.iteritems():
            if arch == 'all':
                continue

            for pkg in self.packages_arch_all:
                manifest.add(pkg)

    def _upload_manifests(self):

        self.log.info('Uploading packages and new manifests to S3')

        for arch, manifest in self.manifests.iteritems():
            self._check_lock(arch)
            manifest.write_to_s3()
            self.release.update_manifest(manifest)
            self.log.info('Update complete.')
            self._delete_lock(arch)

    def upload_debs(self):
        if not self.debs:
            self.log.error('You must specify at least one file to upload')
            exit(1)

        map(self._check_debs_exist, self.debs)

        self._s3_conn()

        self.log.info("Retrieving existing manifests")

        self.release = apt.resources.Release(self.args)
        self.manifests = {}

        map(self._parse_manifest, self.release['architectures'])

        self.packages_arch_all = []

        map(self._parse_package, self.debs)
