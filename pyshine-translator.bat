@echo off
setlocal
set "KMP_DUPLICATE_LIB_OK=TRUE"
python -m src.__main__
endlocal
