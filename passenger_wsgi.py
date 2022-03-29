"""
Phusion passenger interface
"""

import sys
import os

# Allow overriding python interpreter for locked-down server environments
INTERP = os.environ.get('SYLLABITS_PYTHON')
if INTERP and sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

from application import create_app
application = create_app()