#!/bin/bash
git filter-branch --force --index-filter 'git rm -rf --cached --ignore-unmatch macroquant/data/postgres' --prune-empty --tag-name-filter cat -- --all
