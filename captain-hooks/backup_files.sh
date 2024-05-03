#!/usr/bin/env bash

ew stop

restic $HOST -r $URI backup --tag files --exclude sessions --exclude __pychache__ --exclude "*.bak" ./

ew up
