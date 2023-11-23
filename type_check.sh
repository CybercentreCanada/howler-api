#!/bin/bash

if [ -z "$VIRTUAL_ENV" ]; then
    source env/bin/activate
fi

result=$(pip list --local | grep -e "mypy *1.6.1")
if [ -z "$result" ]; then
    pip install mypy=="1.6.1"
fi

find howler -type f -name "*.py" -print0 | xargs -0 python -m mypy --install-types --non-interactive
