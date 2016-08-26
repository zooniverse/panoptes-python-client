# Contributing

We welcome pull requests from anyone, so if you have something you'd like to
contribute or an idea for improving this project, that's great! Changes should
generally fit into one of the following categories:

- Bug fixes
- Implementing additional Panoptes API functionality (there's still a lot to do
  here!)
- Improvements/enhancements which will be generally useful to many people who
  use the API client.

If you're unsure about whether your changes would be suitable, please feel free
to open an issue to discuss them _before_ spending too much time implementing
them. It's best to start talking about how (or if) you should do something
early, before a lot of work goes into it.

## Getting started

The first thing you should do is fork this repo and clone your fork to your
local computer. Then create a feature branch for your changes (create a separate
branch for each separate contribution, don't lump unrelated changes together).

I'd **strongly** recommend using
[virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) to
install your development version of the client:

```
$ mkvirtualenv panoptes-dev
(panoptes-dev)$ pip install -U .
```

When you're ready, push your changes to a branch in your fork and open a pull
request. After opening the PR, you may get some comments from Hound, which is an
automated service which checks coding style and highlights common mistakes.
Please take note of what it says and make any changes to your code as needed.

## Releasing new packages

If you have access to publish new releases on PyPI, this is a general outline of
the process:

- Bump the version number in setup.py
- Update CHANGELOG.md
- Update README.md if needed
- Build and upload a new package:

```
python setup.py sdist
twine upload -s dist/panoptes_client-<version>*
git tag <version>
git push --tags
```

Note that you'll need to have a GPG key set up so that `twine` can sign the
package. You should also make sure that your public key is published in the key
servers so that people can verify the signature.
