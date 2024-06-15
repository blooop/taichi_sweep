#!/bin/bash

mv taichi_sweep $1

find . \( -type d -name .git -prune \) -o \( -type f -not -name 'tasks.json' -not -name 'update_from_template.sh' -not -name 'update_from_template_ours.sh' \) -print0 | xargs -0 sed -i "s/taichi_sweep/$1/g"
