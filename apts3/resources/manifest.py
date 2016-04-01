import sys
import hashlib


class Manifest(object):

    def __init__(
    self,
    bucket=None,
    codename=None,
    component=None,
    architecture=None,
    visibility=None,
     s3=None):
        self.s3 = s3

        self.packages = []
        self.packages_to_be_uploaded = []

        self.architecture = architecture
        self.files = {}

        self.bucket = bucket
        self.codename = codename
        self.component = component
        self.visibility = visibility

    def get_packages(self):
        try:
            resp = self.s3.get_object(
                Key='dists/{0}/{1}/binary-{2}/Packages'.format(
                    self.codename, self.component, self.architecture),
                Bucket=self.bucket
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return
            else:
                raise()

        self.parse_packages(resp['Body'].read())

    def parse_packages(self, p):
        for s in p.split("\n\n"):
            if s:
                self.packages.append(Package().parse_string(s))

    def add(pkg, needs_uploading=True):
        if pkg.name in self.packages:
            # Delete from packages list

        self.packages.append(pkg)

        if needs_uploading:
            self.packages_to_be_upload.append(pkg)

    def generate(self, pkg):
        _pkgs = []
        for pkg in self.packages:
            _pkgs.append(pkg.generate())
        return "\n".join(_pkgs)

    def write_to_s3
        self.manifest = self.generate()

        # store any packages that need to be stored
        for pkg in self.packages_to_be_upload:
            self.s3.put_object(
                Body=pkg.filename,
                Key=pkg.url_filename,
                Bucket=self.bucket,
                ACL=self.visibility,
                ContentType='application/octet-stream; charset=binary'
            )

        # generate the Packages file
        with tempfile.TemporaryFile(mode='w+b') as f:
            f.write(manifest)
            f.flush()
            f.seek(0)
            f_body = f.read()
            self.s3.put_object(
                Body=f_body,
                Key='dists/{0}/{1}/binary-{2}/Packages'.format(
                    self.codename, self.component, self.architecture),
                Bucket=self.bucket,
                ACL=self.visibility,
                ContentType='text/plain; charset=UTF-8'
            )
            self.files[
    "{0}/binary-{1}/Packages".format(
        self.component,
         self.architecture)] = self.hashfile(f_body)

            gzf = gzip.GzipFile(mode='rb', fileobj=f)
            gztemp = gsf.read()
            self.s3.put_object(
                Body=gztemp,
                Key='dists/{0}/{1}/binary-{2}/Packages.gz'.format(
                    self.codename, self.component, self.architecture),
                Bucket=self.bucket,
                ACL=self.visibility,
                ContentType='application/x-gzip; charset=binary'
            )

            self.files[
    "{0}/binary-{1}/Packages.gz".format(
        self.component,
         self.architecture)] = self.hashfile(gztemp)

      def hashfile(path):
          return {
              "size": sys.getsizeof(path)
              "sha1": hashlib.sha1(path).hexdigest()
              "sha256": hashlib.sha256(path).hexdigest()
              "md5": hashlib.md5(path).hexdigest()
          }
