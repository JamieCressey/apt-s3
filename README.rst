apt-s3
======

``apt-s3`` is a Python fork of ``deb-s3`` a simple utility to make
creating and managing APT repositories on S3.

Most existing guides on using S3 to host an APT repository have you
using something like `reprepro <http://mirrorer.alioth.debian.org/>`__
to generate the repository file structure, and then
`s3cmd <http://s3tools.org/s3cmd>`__ to sync the files to S3.

The annoying thing about this process is it requires you to maintain a
local copy of the file tree for regenerating and syncing the next time.

With ``apt-s3``, there is no need for this. ``apt-s3`` features:

-  Downloads the existing package manifest and parses it.
-  Updates it with the new package, replacing the existing entry if
   already there or adding a new one if not.
-  Uploads the package itself, the Packages manifest, and the
   Packages.gz manifest. It will skip the uploading if the package is
   already there.
-  Updates the Release file with the new hashes and file sizes.

Packages within your new S3 repository can then be accessed using
`apt-transport-s3 <https://github.com/JamieCressey/apt-transport-s3>`__

Getting Started
---------------

You can simply install it from PyPi:

.. code:: console

    $ pip install apt-s3

Or to run the code directly, just check out the repo and run
``python setup develop`` to ensure all dependencies are installed:

.. code:: console

    $ git clone https://github.com/JamieCressey/apt-s3.git
    $ cd apt-s3
    $ python setup.py develop

Now to upload a package, simply use:

.. code:: console

    $ apt-s3 upload --bucket my-bucket my-deb-package-1.0.0_amd64.deb
    ...snip...

::

    usage: apt-s3 [-h] [-a ARCH] [-b BUCKET] [-c CODENAME] [-l] [-m COMPONENT]
                  [-p] [-r PREFIX] [-s SIGN] [-t LOCK_TIMEOUT] [-v VISIBILITY]
                  [--profile PROFILE] [--region REGION]
                  action files

    Uploads the given files to a S3 bucket as an APT repository.

Credits
-------

`krobertson <https://github.com/krobertson>`__ for his awesome work on
``deb-s3``
