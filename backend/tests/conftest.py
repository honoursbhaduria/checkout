import os
import pytest

# Ensure test mode is flagged before application imports
os.environ["TESTING"] = "1"
os.environ["ENVIRONMENT"] = "test"
