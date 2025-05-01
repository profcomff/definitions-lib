import logging
import os

import pytest
from alembic.command import init

from .conftest import alembic_config

log = logging.getLogger(__name__)


# TODO@mixx3 idk how to implement this yet
# @pytest.fixture
# def init_migrations_dir(alembic_config):
# directory_path = "tests/migrations_test"
# init(alembic_config, directory_path, template='definitions')
# yield
# try:
#     os.rmdir(directory_path)
#     log.info("Directory removed successfully")
# except FileNotFoundError:
#     log.error("The directory does not exist")
# except OSError as e:
#     log.error(f"Error: {e.strerror}")
