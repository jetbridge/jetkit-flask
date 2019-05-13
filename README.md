[![CircleCI](https://circleci.com/gh/jetbridge/backend-core.svg?style=svg&circle-token=82f320fde8f21fa71931ce9776daaefa580be4f8)](https://circleci.com/gh/jetbridge/backend-core)

JetBridge Python Core Library
-----------------------------

## What is it?
Bits and pieces of useful code, base classes, models, utilities
that we have assembled to reuse for our projects.

## Hacking
To use it in another project and hack on it, install it [editable](https://pipenv.readthedocs.io/en/latest/basics/#editable-dependencies-e-g-e):

To link your working copy to a project's virtual environment:
```
cd ~/.virtualenvs/myapp-8LV4K5cs/src
mv jb jb-orig
ln -s ~/dev/jb/backend-core jb
```

```
pipenv install --dev
```
