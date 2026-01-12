#!/usr/bin/env bash
set -euo pipefail

# CHANGE THIS to the directory you want to run from
WORKDIR="/home/george/Courses/ID2223/kth-id2223-project/backend"

cd "$WORKDIR"

export $(cat .env | xargs)

# Compute dates:
# start_date = today - 7 days
# end_date   = today - 1 day
start_date=$(date -d "today - 7 days" +%F)
end_date=$(date -d "today - 1 day" +%F)

# Run command
uv run python3 packages/training/src/training/train_model_weekly \
  "$start_date" "$end_date" ./data

