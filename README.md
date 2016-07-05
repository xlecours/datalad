# DataLad

DataLad aims to make data management and data distribution more accessible.  To
do that it stands on the shoulders of Git and Git-annex to deliver a
decentralized system for data exchange. This includes automated ingestion of
data from online portals, and exposing it in readily usable form as Git(-annex)
repositories, so-called datasets. The actual data storage and permission
management, however, remains with the original data providers.

# Status

DataLad is under rapid development to establish core functionality.  The while
the code base is still growing the focus is increasingly shifting towards
robust and safe operation with a sensible API. There has been no major public
release yet, as organization and configuration are still subject of
considerable reorganization and standardization. However, DataLad is, in fact,
usable today and user feedback is always welcome.


See [CONTRIBUTING.md](CONTRIBUTING.md) if you are interested in
internals and/or contributing to the project.

## Code status:

* [![Travis tests status](https://secure.travis-ci.org/datalad/datalad.png?branch=master)](https://travis-ci.org/datalad/datalad) travis-ci.org (master branch)

* [![Coverage Status](https://coveralls.io/repos/datalad/datalad/badge.png?branch=master)](https://coveralls.io/r/datalad/datalad)

* [![codecov.io](https://codecov.io/github/datalad/datalad/coverage.svg?branch=master)](https://codecov.io/github/datalad/datalad?branch=master)

* [![Documentation](https://readthedocs.org/projects/datalad/badge/?version=latest)](http://datalad.rtfd.org)

# Installation

## Debian-based systems

On Debian-based systems we recommend to enable [NeuroDebian](http://neuro.debian.net)
from which we provide recent releases of DataLad.

**TODO**: describe few flavors of packages we would provide (I guess
datalad-core, datalad-crawler, datalad; primary difference is dependencies)

## Other Linux'es, OSX (Windows yet TODO) via pip

**TODO**: upload to PyPi and describe installation 'schemes' (crawler,
tests, full).  Ideally we should unify the schemes with Debian packages

For installation through `pip` you would need some external dependencies
not shipped from it (e.g. `git-annex`, etc.) for which please refer to
the next section.

## Dependencies

Although we now support Python 3 (>= 3.3), primarily we still use Python 2.7
and thus instructions below are for python 2.7 deployments.  Replace `python-{` 
with `python{,3}-{` to also install dependencies for Python 3 (e.g., if you would
like to develop and test through tox).

On Debian-based systems we recommend to enable [NeuroDebian](http://neuro.debian.net)
since we use it to provide backports of recent fixed external modules we depend upon:

```sh
apt-get install -y -q git git-annex-standalone
apt-get install -y -q patool python-scrapy python-{appdirs,argcomplete,git,humanize,keyring,lxml,msgpack,mock,progressbar,requests,setuptools,six}
```

or additionally, if you would like to develop and run our tests battery as
described in [CONTRIBUTING.md](CONTRIBUTING.md) and possibly use tox and new
versions of dependencies from pypy:

```sh
apt-get install -y -q python-{dev,httpretty,testtools,nose,pip,vcr,virtualenv} python-tox
# Some libraries which might be needed for installing via pip
apt-get install -y -q lib{ffi,ssl,curl4-openssl,xml2,xslt1}-dev
```

or use pip to install Python modules (prior installation of those libraries listed above
might be necessary)

```sh
pip install -r requirements.txt
```

and will need to install recent git-annex using appropriate for your
OS means (for Debian/Ubuntu, once again, just use NeuroDebian).  We
later will provide bundled installations of DataLad across popular
platforms.


# License

MIT/Expat


# Disclaimer

It is in a prototype stage -- **nothing** is set in stone yet -- but
already usable in a limited scope.

[Git-annex]: http://git-annex.branchable.com
