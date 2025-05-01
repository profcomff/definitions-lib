import os
from pathlib import Path
from typing import Generator

import pytest
from alembic.command import downgrade, revision, upgrade
from alembic.config import Config


def test_walk_migrations(alembic_config: Config) -> None:
    upgrade(alembic_config, 'head')
    revision(alembic_config, autogenerate=True, message="tests")
    upgrade(alembic_config, 'head')
    downgrade(alembic_config, 'base')
