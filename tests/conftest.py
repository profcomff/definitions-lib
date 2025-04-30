import os
from pathlib import Path
from typing import Generator

import pytest
from alembic.command import downgrade, revision, upgrade, init
from definitions.config import Config
from alembic.script import Script, ScriptDirectory
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


@pytest.fixture
def generator_alembic_config():
    alembic_cfg = Config()
    alembic_cfg.config_file_name = 'definitions'
    alembic_cfg.file_ = 'definitions/templates/alembic.ini'
    alembic_cfg.set_main_option('sqlalchemy.url', os.getenv("DB_DSN") or "postgresql://postgres:postgres@localhost:5432/postgres")  # db for migration tests
    return alembic_cfg


@pytest.fixture
def test_do_generate_migration(generator_alembic_config: Config) -> Generator[None, None, None]:
    upgrade(generator_alembic_config, 'head')
    revision(generator_alembic_config, autogenerate=True, message="tests")
    upgrade(generator_alembic_config, 'head')
    yield
    downgrade(generator_alembic_config, 'head-1')

