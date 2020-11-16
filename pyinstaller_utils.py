import sys
import os

def resource_path(relative_path):
    # Get absolute path to resource, works for dev and for PyInstalle
    # https://stackoverflow.com/a/44352931/13780890
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def executable_dir():
    if hasattr(sys, '_MEIPASS'):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(__file__)