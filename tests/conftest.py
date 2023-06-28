import os
import pathlib
import shutil
import sys
import tempfile
from contextlib import nullcontext

import datajoint as dj
import pytest
from datajoint.logging import logger

from .datajoint._config import DATAJOINT_SERVER_PORT
from .datajoint._datajoint_server import kill_datajoint_server, run_datajoint_server

# ---------------------- CONSTANTS ---------------------

thisdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(thisdir)
global __PROCESS
__PROCESS = None


def pytest_addoption(parser):
    """Permit constants when calling pytest at command line

    Example
    -------
    > pytest --my-verbose False

    Parameters
    ----------
    --current (bool): Default False. Run only tests marked as current.
    --my-verbose (bool):  Default True. Pass print statements from Elements.
    --my-teardown (bool): Default True. Delete pipeline on close.
    """
    parser.addoption(
        "--current",
        action="store_true",
        dest="current",
        default=False,
        help="Run only tests marked as current",
    )
    parser.addoption(
        "--my-verbose",
        action="store",
        default="True",
        help="Verbose for items: True or False",
        choices=("True", "False"),
    )
    parser.addoption(
        "--my-teardown",
        action="store",
        default="True",
        help="Verbose for items: True or False",
        choices=("True", "False"),
    )


@pytest.fixture(scope="session")
def setup(request):
    """Take passed command line variables, set as global"""
    global verbose, _tear_down, verbose_context, test_data_dir

    verbose = str_to_bool(request.config.getoption("--my-verbose"))
    _tear_down = str_to_bool(request.config.getoption("--my-teardown"))

    if not verbose:
        logger.setLevel(50)

    verbose_context = nullcontext() if verbose else QuietStdOut()

    yield verbose_context, _tear_down


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "current: for convenience -- mark one test as current"
    )

    markexpr_list = []

    if config.option.current:
        markexpr_list.append("current")

    if len(markexpr_list) > 0:
        markexpr = " and ".join(markexpr_list)
        setattr(config.option, "markexpr", markexpr)

    _set_env()

    # note that in this configuration, every test will use the same datajoint
    # server this may create conflicts and dependencies between tests it may be
    # better but significantly slower to start a new server for every test but
    # the server needs to be started before tests are collected because
    # datajoint runs when the source files are loaded, not when the tests are
    # run. one solution might be to restart the server after every test

    global __PROCESS
    __PROCESS = run_datajoint_server()


def pytest_unconfigure(config):
    if __PROCESS:
        logger.info("Terminating datajoint compute resource process")
        __PROCESS.terminate()

        # TODO handle ResourceWarning: subprocess X is still running __PROCESS.join()

    kill_datajoint_server()
    shutil.rmtree(os.environ["SPYGLASS_BASE_DIR"])


# ------------------ GENERAL FUNCTION ------------------


def str_to_bool(value) -> bool:
    """Return whether the provided string represents true. Otherwise false.
    Args:
        value (any): Any input
    Returns:
        bool (bool): True if value in ("y", "yes", "t", "true", "on", "1")
    """
    # Due to distutils equivalent depreciation in 3.10
    # Adopted from github.com/PostHog/posthog/blob/master/posthog/utils.py
    if not value:
        return False
    return str(value).lower() in ("y", "yes", "t", "true", "on", "1")


class QuietStdOut:
    """If verbose set to false, used to quiet tear_down table.delete prints"""

    def __enter__(self):
        # os.environ["LOG_LEVEL"] = "WARNING"
        logger.setLevel("CRITICAL")
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

    def __exit__(self, exc_type, exc_val, exc_tb):
        # os.environ["LOG_LEVEL"] = "INFO"
        logger.setLevel("INFO")
        sys.stdout.close()
        sys.stdout = self._original_stdout


# ------------------- FIXTURES -------------------


@pytest.fixture(scope="session")
def _set_env():
    """Set environment variables."""
    logger.info("Setting datajoint and kachery environment variables.")

    spyglass_base_dir = pathlib.Path(tempfile.mkdtemp())

    spike_sorting_storage_dir = spyglass_base_dir / "spikesorting"
    tmp_dir = spyglass_base_dir / "tmp"

    os.environ["SPYGLASS_BASE_DIR"] = str(spyglass_base_dir)
    logger.info("SPYGLASS_BASE_DIR set to", spyglass_base_dir)
    os.environ["DJ_SUPPORT_FILEPATH_MANAGEMENT"] = "TRUE"
    os.environ["SPIKE_SORTING_STORAGE_DIR"] = str(spike_sorting_storage_dir)
    os.environ["SPYGLASS_TEMP_DIR"] = str(tmp_dir)
    os.environ["KACHERY_CLOUD_EPHEMERAL"] = "TRUE"

    os.mkdir(spike_sorting_storage_dir)
    os.mkdir(tmp_dir)

    raw_dir = spyglass_base_dir / "raw"
    analysis_dir = spyglass_base_dir / "analysis"

    os.mkdir(raw_dir)
    os.mkdir(analysis_dir)

    dj.config["database.host"] = "localhost"
    dj.config["database.port"] = DATAJOINT_SERVER_PORT
    dj.config["database.user"] = "root"
    dj.config["database.password"] = "tutorial"

    dj.config["stores"] = {
        "raw": {
            "protocol": "file",
            "location": str(raw_dir),
            "stage": str(raw_dir),
        },
        "analysis": {
            "protocol": "file",
            "location": str(analysis_dir),
            "stage": str(analysis_dir),
        },
    }
