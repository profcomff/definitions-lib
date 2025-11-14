import os

from alembic.autogenerate import comparators
from sqlalchemy import text

from .operations_encrypt import DecryptTableOp, EncryptTableOp
from .operations_tables import GrantRightsOp, RevokeRightsOp


# @comparators.dispatch_for("table")
def compare_for_encrypted(
    autogen_context, modify_table_ops, sch, tname, table_db, table_code
):
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
                f"{sch}.{table_code.name}",
                code_info.encryption["keys"],
                code_info.encryption["id"],
                code_info.encryption["columns"],
            )
        )
    if encrypted_db and not encrypted_code:
        modify_table_ops.append(
            DecryptTableOp(
                f"{sch}.{table_code.name}",
                code_info.encryption["keys"],
                code_info.encryption["id"],
                code_info.encryption["columns"],
            )
        )


# TODO: check for all existing rights, don't assume that they come from render_scope_map
# query = text("SELECT grantee, privilege_type FROM information_schema.role_table_grants "
#              "WHERE table_schema=:schema AND table_name=:tablename AND grantee ILIKE :pattern")
# params = { "schema": sch, "tablename": metadata_table_db.name, "pattern": f"{environment}%{project_prefix}_{sch}_%"}
# for role, scope in autogen_context.connection.execute(query, params):
#     current_rights.setdefault(role, []).append(scope)
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
    required_rights = set()
    current_rights = set()

    # extract rights from database
    if metadata_table_db is not None:
        query = text(
            "SELECT DISTINCT grantee FROM information_schema.role_table_grants "
            "WHERE table_schema=:schema AND table_name=:tablename AND grantee ILIKE :pattern"
        )
        params = {
            "schema": sch,
            "tablename": metadata_table_db.name,
            "pattern": f"{environment}%{project_prefix}_{sch}_%",
        }
        current_rights.update(
            row.grantee for row in autogen_context.connection.execute(query, params)
        )

    # get required rights
    if metadata_table_code is not None:
        sensitive = (
            "_sensitive" if metadata_table_code.info.get("sensitive", False) else ""
        )
        group_name = f"{environment}%s_{project_prefix}_{sch}_%s".lower()
        required_rights.update(
            group_name % (sensitive, render_scope)
            for render_scope in render_scope_map.keys()
        )

    for group in required_rights - current_rights:
        scope = group[group.rfind("_") + 1 :]
        modify_table_ops.ops.append(
            GrantRightsOp(
                table_name=f"{sch}.{tname}",
                scopes=render_scope_map[scope],
                group_name=group,
            )
        )
    for group in current_rights - required_rights:
        scope = group[group.rfind("_") + 1 :]
        modify_table_ops.ops.append(
            RevokeRightsOp(
                table_name=f"{sch}.{tname}",
                scopes=render_scope_map[scope],
                group_name=group,
            )
        )
