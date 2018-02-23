#!/usr/bin/env sh
if git rev-parse --git-dir > /dev/null 2>&1
then
  git add --all .
  git diff --cached --exit-code || git commit -m "Commit at $(date --utc --iso-8601=second)"
else
  git init
  git config user.email "author@example.com"
  git config user.name "A U Thor"
  echo '__salt.tmp.*' >> .gitignore
  git add .
  git commit -m "Initial commit"
fi
