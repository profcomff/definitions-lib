import os
from pathlib import Path

import pytest
from alembic.script import Script, ScriptDirectory

from definitions.config import Config

REPO_ROOT = Path(os.path.abspath(os.path.dirname(__file__))).parent.resolve()


@pytest.fixture
def alembic_config():
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", str(REPO_ROOT / "test_migrations"))
    alembic_cfg.set_main_option(
        "sqlalchemy.url",
        os.getenv("DB_DSN") or "postgresql://postgres:postgres@localhost:5432/postgres",
    )  # db for migration tests
    return alembic_cfg


@pytest.fixture
def revisions(alembic_config: Config) -> list[Script]:
    revisions_dir = ScriptDirectory.from_config(alembic_config)
    revisions = list(revisions_dir.walk_revisions("base", "heads"))
    revisions.reverse()
    return revisions
