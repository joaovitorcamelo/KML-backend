#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install poetry
/opt/render/project/src/.venv/bin/poetry install

python manage.py collectstatic --no-input
python manage.py migrate

if [[ $CREATE_SUPERUSER ]];
then
  python manage.py createsuperuser --no-input
fi
