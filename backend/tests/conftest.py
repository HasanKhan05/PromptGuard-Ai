import os
import tempfile
from pathlib import Path


_test_db_directory = Path(tempfile.mkdtemp(prefix="promptguard-pytest-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_test_db_directory / 'promptguard-test.db').as_posix()}"
