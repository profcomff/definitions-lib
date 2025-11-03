import os

from alembic.autogenerate import comparators
from sqlalchemy import text

from .operations_groups import (
    CreateGroupOp,
    DeleteGroupOp,
    GrantOnSchemaOp,
    RevokeOnSchemaOp,
)
from .operations_schemas import CreateTableSchemaOp, DropTableSchemaOp
from .operations_tables import GrantRightsOp, RevokeRightsOp


# this function is exported and not used inside this file, do not delete
def add_table_schema_to_model(table_schema, metadata):
    metadata.info.setdefault("table_schemas", set()).add(table_schema)


@comparators.dispatch_for("schema")
def compare_for_groups(autogen_context, upgrade_ops, schemas):
    environment = "test" if os.getenv("ENVIRONMENT") != "production" else "prod"
    project_prefix = os.getenv("SCHEMA_PREFIX", "dwh")
    all_conn_schemas = set()
    default_pg_schemas = ["pg_toast", "information_schema", "public", "pg_catalog"]
    query = text("SELECT schema_name FROM information_schema.schemata")
    # all schemas in database
    all_conn_schemas.update(
        [
            sch[0]
            for sch in autogen_context.connection.execute(query)
            if sch[0] not in default_pg_schemas
        ]
    )
    # all schemas in code
    metadata_schemas = autogen_context.metadata.info.setdefault("table_schemas", set())

    # Create/delete new schemas
    for sch in metadata_schemas - all_conn_schemas:
        upgrade_ops.ops.append(CreateTableSchemaOp(sch))
    for sch in all_conn_schemas - metadata_schemas:
        upgrade_ops.ops.append(DropTableSchemaOp(sch))

    all_groups_db = set()
    all_groups_code = set()
    query = text(
        "SELECT grantee,table_schema FROM information_schema.role_table_grants "
        "WHERE grantee LIKE :pattern"
    )
    all_groups_db.update(
        autogen_context.connection.execute(
            query, {"pattern": f"{environment}%{project_prefix}%"}
        )
    )
    for sch in metadata_schemas:
        has_regular = any(
            table.schema == sch and not table.info.get("sensitive", False)
            for table in autogen_context.metadata.tables.values()
        )
        has_sensitive = any(
            table.schema == sch and table.info.get("sensitive", False)
            for table in autogen_context.metadata.tables.values()
        )

        group_name = f"{environment}%s_{project_prefix}_{sch}_%s".lower()
        for render_scope in ["read", "write", "all"]:
            if has_regular:
                all_groups_code.add((group_name % ("", render_scope), sch))
            if has_sensitive:
                all_groups_code.add((group_name % ("_sensitive", render_scope), sch))

    # for all new required groups
    for group, sch in all_groups_code - all_groups_db:
        upgrade_ops.ops.append(CreateGroupOp(group))
        upgrade_ops.ops.append(GrantOnSchemaOp(group, sch))

    # for all groups no longer needed
    for group, sch in all_groups_db - all_groups_code:
        upgrade_ops.ops.append(DeleteGroupOp(group))
        upgrade_ops.ops.append(RevokeOnSchemaOp(group, sch))
