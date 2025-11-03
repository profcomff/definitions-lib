from alembic.operations import MigrateOperation, Operations


@Operations.register_operation("encrypt_table")
class EncryptTableOp(MigrateOperation):
    def __init__(self, table_name, key_table_name, id_column, columns):
        self.table_name = table_name
        self.key_table_name = key_table_name
        self.id_column = id_column
        self.columns = columns

    @classmethod
    def encrypt_table(
        cls, operations, table_name, key_table_name=None, id_column="id", columns=None
    ):
        op = EncryptTableOp(table_name, key_table_name, id_column)
        return operations.invoke(op)

    def reverse(self):
        return DecryptTableOp(
            self.table_name, self.key_table_name, self.id_column, self.columns
        )


@Operations.register_operation("decrypt_table")
class DecryptTableOp(MigrateOperation):
    def __init__(self, table_name, key_table_name, id_column, columns):
        self.table_name = table_name
        self.key_table_name = key_table_name
        self.id_column = id_column
        self.columns = columns

    @classmethod
    def decrypt_table(cls, operations, table_name, key_table_name, id_column, columns):
        op = DecryptTableOp(table_name, key_table_name, id_column, columns)
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


@Operations.implementation_for(EncryptTableOp)
def encrypt_table(operations, operation):
    print(type(operations), type(operation))


@Operations.implementation_for(DecryptTableOp)
def decrypt_table(operations, operation): ...


@Operations.implementation_for(EncryptColumnOp)
def encrypt_column(operations, operation): ...


@Operations.implementation_for(DecryptColumnOp)
def decrypt_column(operations, operation): ...
