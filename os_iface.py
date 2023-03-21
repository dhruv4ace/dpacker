
import platform

if platform.system() == 'Windows':
    from .os_windows import *
    