import os
import pytest
import logging
from alembic.command import downgrade, revision, upgrade, init
from .conftest import generator_alembic_config
from definitions.config import Config


log = logging.getLogger(__name__)


@pytest.fixture
def init_migrations_dir(generator_alembic_config):
    directory_path = "tests/migrations_test"
    init(generator_alembic_config, directory_path, template='definitions')
    yield
    try:
        os.rmdir(directory_path)
        log.info("Directory removed successfully")
    except FileNotFoundError:
        log.error("The directory does not exist")
    except OSError as e:
        log.error(f"Error: {e.strerror}")


def test_directory_created(init_migrations_dir):
    assert True