#!/bin/bash
BACKUP_REPO="/mnt/data/Repos/Backups"
DEST_FOLDER="$BACKUP_REPO/Crypto-Bot-Ecosystem"

# Copy only specific files
cp -r /mnt/data/Crypto-Bot-Ecosystem/data_bases "$DEST_FOLDER/"
cp /mnt/data/Crypto-Bot-Ecosystem/config/portfolio.json "$DEST_FOLDER/"
cp /mnt/data/Crypto-Bot-Ecosystem/config/portfolio_history.json "$DEST_FOLDER/"
cp /mnt/data/Crypto-Bot-Ecosystem/config/transactions.json "$DEST_FOLDER/"
cp /mnt/data/Crypto-Bot-Ecosystem/config/variables.json "$DEST_FOLDER/"

# Commit and push
cd "$BACKUP_REPO"
git add .
git commit -m "backup $(date +%Y-%m-%d)"
git push origin main