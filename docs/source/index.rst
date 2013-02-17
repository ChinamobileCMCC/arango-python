ArangoDB Driver for Python
==========================

.. warning::
    This is **PRE ALPHA** release, so several required features
    **are not supported**!


Features support
----------------

Driver for Python is incomplete. It supports at the moment:
**Connections to ArangoDB with custom options**,
**Collections**, **Documents**, **Indexes** **Cursors**
and have partial support of **Edges**


Getting started
---------------

Installation
~~~~~~~~~~~~~

Library is in early alpha so it's not on PyPi yet. To install use `pip`::

  pip install -e git+https://github.com/joymax/arango-python.git#egg=arango


Usage example
~~~~~~~~~~~~~

It's quite simple to start work with **ArangoDB**::

    from arango import create

    # create connection to database
    voca = create()

    # create collection with name `test_collection`
    voca.test_collection.create()

    # create document
    voca.test_collection.documents.create({
        "sample_key": "sample_value"
    })

    # get first document
    voca.test_collection.documents().first

    # get document body
    voca.test_collection.documents().first.body

    # get value of key `sample_key`
    voca.test_collection.documents().first.get("sample_key")


Contents
---------
.. toctree::
   :maxdepth: 2

   collections
   documents
   queries
   indexes
   edges
   exceptions
   glossary
   guidelines


Platforms and Python versions
-----------------------------

This release support *Python 2.7*, *PyPy 1.9*.

Next in chain is *Python 3.3*



Indices and tables
-------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

