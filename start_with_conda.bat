@echo off
call conda activate qwen
set KMP_DUPLICATE_LIB_OK=TRUE
python -m src.__main__
call conda deactivate
