#!/bin/bash
set -e

# 若有数据库迁移等操作可在这里加
# if [ -f "manage.py" ]; then python manage.py migrate; fi

exec gunicorn app:app --bind 0.0.0.0:8000 --workers 2