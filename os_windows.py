import os
import signal
import subprocess
from ctypes.util import find_library
from ctypes import windll

import winreg


def os_exec_extension():
    return '.exe'

def os_exec_dirname():
    return 'win'

def os_engine_creation_flags():
    return subprocess.CREATE_NEW_PROCESS_GROUP

def os_cancel_sig():
    return signal.CTRL_BREAK_EVENT
