import os

from alembic.autogenerate import comparators

from .operations_encrypt import DecryptTableOp, EncryptTableOp
from .operations_tables import GrantRightsOp, RevokeRightsOp


def compare_for_encrypted(table_db, table_code):
    db_info = dict() if table_db is None else table_db.info
    code_info = dict() if table_code is None else table_code.info
    encrypted_db = db_info.get("encrypted", False)
    encrypted_code = code_info.get("encrypted", False)
    if encrypted_code and encrypted_db:
        if db_info != code_info:
            print(
                "Error: changing encryption parameters is not supported.\n"
                "Please edit migration file manually, using EncryptTableOp and DecryptTableOp",
                file=stderr,
            )
            exit(1)
    if encrypted_code and not encrypted_db:
        modify_table_ops.append(
            EncryptTableOp(
                table_code.name,
                code_info.encryption["keys"],
                code_info.encryption["id"],
                code_info.encryption["columns"],
            )
        )
    if encrypted_db and not encrypted_code:
        modify_table_ops.append(
            DecryptTableOp(
                table_code.name,
                code_info.encryption["keys"],
                code_info.encryption["id"],
                code_info.encryption["columns"],
            )
        )


@comparators.dispatch_for("table")
def compare_for_sensitive(
    autogen_context,
    modify_table_ops,
    sch,
    tname,
    metadata_table_db,
    metadata_table_code,
):
    environment = "test" if os.getenv("ENVIRONMENT") != "production" else "prod"
    project_prefix = os.getenv("SCHEMA_PREFIX", "dwh")
    render_scope_map = {
        "read": ["SELECT"],
        "write": ["SELECT", "UPDATE", "DELETE", "TRUNCATE", "INSERT"],
        "all": ["ALL"],
    }

    # опять неправильный подход от миши, который не учитывает изменяющиеся таблицы
    if metadata_table_db is None:
        sensitive = (
            "_sensitive" if metadata_table_code.info.get("sensitive", False) else ""
        )
        for render_scope, scopes in render_scope_map.items():
            group_name = f"{environment}{sensitive}_{project_prefix}_{sch}_{render_scope}".lower()
            modify_table_ops.ops.append(
                GrantRightsOp(
                    table_name=str(metadata_table_code),
                    scopes=scopes,
                    group_name=group_name,
                )
            )

    if metadata_table_code is None:
        sensitive = (
            "_sensitive" if metadata_table_db.info.get("sensitive", False) else ""
        )
        for render_scope, scopes in render_scope_map.items():
            group_name = f"{environment}{sensitive}_{project_prefix}_{sch}_{render_scope}".lower()
            modify_table_ops.ops.append(
                RevokeRightsOp(
                    table_name=str(metadata_table_db),
                    scopes=scopes,
                    group_name=group_name,
                )
            )
