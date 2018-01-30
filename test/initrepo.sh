#!/usr/bin/env sh
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  git init
  git config user.email "author@example.com"
  git config  user.name "A U Thor"
  git add .
  git commit -m "Initial commit"
fi
