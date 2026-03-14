import os
import sys

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

if __name__ == '__main__':
    import src.__main__
    src.__main__.main()
