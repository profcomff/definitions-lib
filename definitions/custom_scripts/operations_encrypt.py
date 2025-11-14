from alembic.operations import MigrateOperation, Operations
from sqlalchemy import text
from enum import IntEnum


def _get_column_names(schema, table, id_column):
    return [
        i.column_name
        for i in operations.get_bind().execute(
            text(
                f"SELECT column_name FROM information_schema.columns "
                f"WHERE table_schema='{schema}' AND table_name='{name}';"
            )
        )
        if i != id_column
    ]


class op_type(IntEnum):
    ENCRYPT = 0x00
    DECRYPT = 0x01


def _common_constructor(self, table_name, key_table_name, id_column, columns, **kw):
    _name = table_name.split(".")
    if len(_name) != 2:
        self.table_name = table_name
    else:
        self.table_schema, self.table_name = _name
    if (sch := kw.get("schema", None)) is not None:
        self.table_schema = sch

    _key_name = key_table_name.split(".")
    if len(_key_name) < 2:
        self.key_table_name = key_table_name
    else:
        self.key_table_schema, self.key_table_name = _key_name
    if (sch := kw.get("key_schema", None)) is not None:
        self.key_table_schema = sch

    self.id_column = id_column
    self.columns = columns


@Operations.register_operation("encrypt_table")
class EncryptTableOp(MigrateOperation):
    """fields:
    self.table_name: str
    self.table_schema: str
    self.key_table_name: str
    self.key_table_schema: str
    self.id_column: str
    self.columns: list[str]
    """

    def __init__(self, table_name, key_table_name, id_column, columns, **kw):
        _name = table_name.split(".")
        if len(_name) != 2:
            self.table_name = table_name
        else:
            self.table_schema, self.table_name = _name
        if (sch := kw.get("schema", None)) is not None:
            self.table_schema = sch

        _key_name = key_table_name.split(".")
        if len(_key_name) < 2:
            self.key_table_name = key_table_name
        else:
            self.key_table_schema, self.key_table_name = _key_name
        if (sch := kw.get("key_schema", None)) is not None:
            self.key_table_schema = sch

        self.id_column = id_column
        self.columns = columns

    @classmethod
    def encrypt_table(
        cls,
        operations,
        table_name,
        key_table_name=None,
        id_column="id",
        columns=None,
        **kw,
    ):
        if columns is None:
            columns = _get_column_names(*table_name.split("."), id_column)
        if key_table_name is None:
            key_table_name = table_name + "_ekeys"
        op = EncryptTableOp(table_name, key_table_name, id_column, columns, **kw)
        return operations.invoke(op)

    def reverse(self):
        return DecryptTableOp(
            self.table_name, self.key_table_name, self.id_column, self.columns
        )


@Operations.register_operation("decrypt_table")
class DecryptTableOp(MigrateOperation):
    "same fields as in EncryptTableOp"

    __init__ = _common_constructor

    @classmethod
    def decrypt_table(
        cls, operations, table_name, key_table_name, id_column, columns, **kw
    ):
        op = DecryptTableOp(table_name, key_table_name, id_column, columns, **kw)
        return operations.invoke(op)

    def reverse(self):
        return EncryptTableOp(
            self.table_name, self.key_table_name, self.id_column, self.columns
        )


@Operations.register_operation("encrypt_column")
class EncryptColumnOp(MigrateOperation):
    def __init__(self, column_name, key_table_name, id_column):
        self.column_name = column_name
        self.key_table_name = key_table_name
        self.id_column = id_column

    @classmethod
    def encrypt_column(cls, operations, column_name, key_table_name, id_column):
        op = EncryptColumnOp(column_name, key_table_name, id_column)
        return operations.invoke(op)

    def reverse(self):
        return DecryptColumnOp(self.column_name, self.key_table_name, self.id_column)


@Operations.register_operation("decrypt_column")
class DecryptColumnOp(MigrateOperation):
    def __init__(self, column_name, key_table_name, id_column):
        self.column_name = column_name
        self.key_table_name = key_table_name
        self.id_column = id_column

    @classmethod
    def decrypt_column(cls, operations, column_name, key_table_name, id_column):
        op = DecryptColumnOp(column_name, key_table_name, id_column)
        return operations.invoke(op)

    def reverse(self):
        return EncryptColumnOp(self.column_name, self.key_table_name, self.id_column)


def _generate_keygen_query(operation) -> str:
    return (
        f'INSERT INTO "{operation.key_table_schema}".{operation.key_table_name} '
        f"SELECT src.{operation.id_column}, encode(gen_random_bytes(32), 'base64'), NOW() "
        f'FROM "{operation.table_schema}".{operation.table_name} '
        f'AS src LEFT JOIN "{operation.key_table_schema}".{operation.key_table_name} AS dest '
        f"ON dest.id = src.{operation.id_column} WHERE dest.id IS NULL;"
    )


def _generate_encryption_query(operation, func: op_type) -> str:
    set_cols = []
    encrypt_cols = []
    for colname in operation.columns:
        set_cols.append(f"{colname} = sub.enc_{colname}")
        encrypt_cols.append(
            f"pgp_sym_{func.name}_bytea(dst.{colname}, keys.key) enc_{colname}"
        )
    return (
        f'UPDATE "{operation.table_schema}".{operation.table_name} dst '
        f'SET {",".join(set_cols)} FROM (SELECT '
        f'dst.{operation.id_column} id,{",".join(encrypt_cols)}'
        f'  FROM "{operation.table_schema}".{operation.table_name} dst '
        f'  LEFT JOIN "{operation.key_table_schema}".{operation.key_table_name} keys'
        f"  ON keys.id=dst.{operation.id_column}) sub "
        f"WHERE dst.{operation.id_column}=sub.id;"
    )


@Operations.implementation_for(EncryptTableOp)
def encrypt_table(operations, operation):
    operations.execute(_generate_keygen_query(operation))
    operations.execute(_generate_encryption_query(operation, op_type.ENCRYPT))


@Operations.implementation_for(DecryptTableOp)
def decrypt_table(operations, operation):
    operations.execute(_generate_encryption_query(operation, op_type.DECRYPT))


@Operations.implementation_for(EncryptColumnOp)
def encrypt_column(operations, operation): ...


@Operations.implementation_for(DecryptColumnOp)
def decrypt_column(operations, operation): ...
