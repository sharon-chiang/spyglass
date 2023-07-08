#!/usr/bin/env python

import os
import warnings

import numpy as np

# import tables so that we can call them easily
from spyglass.common import AnalysisNwbfile
from spyglass.decoding.clusterless import (
    MarkParameters,
    UnitMarkParameters,
    UnitMarks,
)
from spyglass.spikesorting import SpikeSorting

# ignore datajoint+jupyter async warnings
warnings.simplefilter("ignore", category=DeprecationWarning)
warnings.simplefilter("ignore", category=ResourceWarning)
os.environ["SPIKE_SORTING_STORAGE_DIR"] = "/stelmo/nwb/spikesorting"


def main():
    """Execute nightly cleanup methods for AnalysisNwbfile and SpikeSorting."""
    AnalysisNwbfile().nightly_cleanup()
    SpikeSorting().nightly_cleanup()


if __name__ == "__main__":
    main()
