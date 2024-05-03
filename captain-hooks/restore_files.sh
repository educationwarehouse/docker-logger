#!/bin/bash
# recover the backup from the files snapshot and save it in ./
# ignore the .git folder to be able to compare the restored files with the current ones.
# Most appropriate when recovering in an already instantiated environment.
restic $HOST -r $URI restore $SNAPSHOT --tag files --target ./ --exclude .git
