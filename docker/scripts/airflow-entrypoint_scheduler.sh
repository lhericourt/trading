#!/usr/bin/env bash
python3 -m ensurepip --upgrade
pip install -r /opt/trading/requirements.txt
airflow scheduler