#!/bin/bash
flake8 ./xdev --count --select=E9,F63,F7,F82 --show-source --statistics
