import os
import sys

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

if sys.platform == 'win32':
    try:
        import PySide6
        pyside_dir = os.path.dirname(PySide6.__file__)
        plugins_path = os.path.join(pyside_dir, 'plugins')
        if os.path.exists(plugins_path):
            os.environ['QT_PLUGIN_PATH'] = plugins_path
    except ImportError:
        pass

if __name__ == '__main__':
    import src.__main__
    src.__main__.main()
