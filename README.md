# definitions-lib

This is an extension library for
[alembic](https://alembic.sqlalchemy.org/en/latest/), a database migration tool
for usage with SQLAlchemy.

# Features

Note that currently, all of the features are postgres-exclusive, and
making them database-agnostic is **not** the main focus.

- access group management (regular/sensitive read/write groups for each schema
  for fine-grained access control)
- seamless encryption (column-based encryption & decryption routines, key
  generation, integration with access groups) \[work in progress\]
- autogeneration support for each feature
- mirrored alembic interface (suitable as a drop-in replacement)

# Requirements

- alembic `>=1.17.2`
- python (exact versions to be determined)
- sqlalchemy that works with required alembic version

# Installation & usage

First of all, you need an alembic configuration, see
[alembic docs](https://alembic.sqlalchemy.org/en/latest/tutorial.html) for setup
steps.

After you have a working alembic setup, run `pip install definitions-lib`, and
you are done.

To use definitions-lib, simply replace `alembic` command with `python -m
definitions` in your usual workflow. For example:

- initialize database state: `python -m definitions init`
- generate revision: `python -m definitions revision --autogenerate -m message`
- e.t.c.

Note: You can still use `alembic` for some commands, like
`upgrade`/`downgrade`. But there has not been enough experimentation to know for
sure which commands do and which do not require running `python -m definitions`

# Notes for the user

- Just like alembic, definitions-lib needs to generate and manage a table to
  store metadata. Unlike alembic, this table contains records for
  each table in your database. Additionally, definitions-lib may shadow-manage
  some tables (key tables, for instance). For a detailed explaination, see API
  section.
- This table will be placed in the same schema as `alembic_version` (default
  schema is `public`).

# API

All of the magic happenes when you define additional fields in the `info`
dict for your table (`__table_args__.info` in case of declarative definition).

## sensitive

To mark table as sensitive, set `info["sensitive"] = True`. This will tell
definitions-lib that an additional set of read/write groups must be created for
the current schema. There are no additional arguments.

If `info["sensitive"]` is set to `False` or removed after the sensitive groups
are created, these groups will be dropped (unless other tables require
them).

## encrypted

To mark table as encrypted, set `info["encrypted"] = True`. In addition to that,
you must set `info["encryption"] = param_dict`, where `param_dict` has following
parameters:

- `id: str` - identiry column name for encryption. Used to retrieve and generate
  encryption keys (they are unique accross id columns)
- `keys: str` - table name that stores encryption keys, in format "{schema}.{table}"
  OR "{table}".
- `keys_schema: str` (optional) - if `keys` does not specify schema, this parameter
  may be used to specify it.
- `columns: list[str]`: array of column names to be encrypted. Should never
  contain `id`.

Currently, `keys` table must exist before encryption operation is ran, and it
must follow a defined structure. However, it is planned to make key table
automatically managed, keeping an option to manage it manually, so that the user
does not have to pollute their definitions.

# Current TODOs:

## Encryption

- [ ] Create custom CreateTableOp/DropTableOp to support shadow tables and info
  table inserts.
- [ ] Create render functions for encryption operations
- [ ] Finish encryption comparators (use info table)

## Tests

- [ ] Write tests (using sqlalchemy.testing) ### Documentation
- [ ] info dict API
- [ ] docs.profcomff.com

## Historical tables

This feature is to be discussed, but the basic idea is to implement TTLs for
historic tables.

# Contribution

Until testing suite is added, there are no guidelines.

TODO: review this section.
