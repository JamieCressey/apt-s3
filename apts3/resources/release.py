import gnupg
import os
import re
import botocore.exceptions


class Release(object):

    def __init__(
            self,
            codename=None,
            origin=None,
            suite=None,
            architectures=[],
            components=[],
            files={},
            policy='public_read',
            s3=None):
        self.codename = codename
        self.origin = origin
        self.suite = suite
        self.architectures = architectures
        self.components = components
        self.files = files
        self.policy = policy

        self.s3 = s3

    def get_release(self):
        try:
            resp = self.s3.get_object(
                Key='dists/{0}/Release'.format(self.codename),
                Bucket=self.bucket
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchKey':
                raise()

        self.parse(resp['Body'].read())

    def parse(self, release):
        regex = re.compile(r'''
            [\S]+:                # a key (any word followed by a colon)
            (?:
            \s                    # then a space in between
                (?!\S+:)\S+       # then a value (any word not followed by a colon)
            )+                    # match multiple values if present
            ''', re.VERBOSE)

        matches = regex.findall(release)
        parse = dict([match.split(':', 1) for match in matches])

        # grab basic fields
        self.codename = parse['Codename']
        self.origin = parse['origin']
        self.suite = parse['Suite']
        self.architectures = parse["Architectures"].split()
        self.components = parse["Components"].split()

        regex = re.compile(r'''
            /^\s+([^\s]+)\s+(\d+)\s+(.+)$/
            ''', re.VERBOSE)

        matches = regex.findall(release)

        for match in matches:
            hash, size, name = match.split()
            self.files[name]

            if len(hash) == 32:
                self.files[name]['md5'] = hash
            elif len(hash) == 40:
                self.files[name]['sha1'] = hash
            elif len(hash) == 64:
                self.files[name]['sha256'] = hash

        def generate
            return template("release.erb").result(binding)

        def filename(self):
            return "dists/{}/Release".format(self.codename)

        def write_to_s3(self):
            gpg = gnupg.GPG(gnupghome=os.path.expanduser('~'))
            self.validate_others()

            # generate the Packages file
            with tempfile.TemporaryFile(mode='w+b') as f:
                f.write(self.generate())
                f.flush()
                f.seek(0)
                f_body = f.read()
                self.s3.put_object(
                    Body=f_body,
                    Key=self.filename(),
                    Bucket=self.bucket,
                    ACL=self.visibility,
                    ContentType='text/plain; charset=UTF-8'
                )

                if self.sign:
                    local_file = gpg.sign_file(f_body, keyid=self.sign)
                    self.s3.put_object(
                        Body=localfile,
                        Key='{}.gpg'.format(self.filename),
                        Bucket=self.bucket,
                        ACL=self.visibility,
                        ContentType='text/plain; charset=UTF-8'
                    )
                else:
                    self.s3.delete_object(
                        Key='{}.gpg'.format(self.filename),
                        Bucket=self.bucket
                    )

        def update_manifest(self, manifest):
            if manifest.component not in self.components:
                self.components.append(manifest.component)

            if manifest.architecture not in self.architectures:
                self.architectures.append(manifest.architecture)

            self.files = self.files + \
                list(set(manifest.files) - set(self.files))

        def validate_others(self):
            to_apply = []
            for comp in self.components:
                for arch in ['amd64', 'i386']:
                    if "{0}/binary-{1}/Packages".format(comp,
                                                        arch) in self.files:
                        m = Manifest(
                            bucket=self.bucket,
                            codename=self.codename,
                            component=comp,
                            architecture=arch,
                            s3=self.s3)
                        m.get_packages()
                        m.write_to_s3()

                        to_apply.append(m)

            for m in to_apply:
                self.update_manifest(m)
