#!/usr/bin/bash

set -e

echorun() {
  echo -e "\n\033[1mRunning command:\033[0m $@"
  $@
}
