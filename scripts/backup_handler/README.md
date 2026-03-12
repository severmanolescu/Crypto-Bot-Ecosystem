# Crypto Bot Ecosystem Backup Script

This script backs up the critical data files from the Crypto Bot Ecosystem to a private GitHub repository.

---

## What Gets Backed Up

| File/Folder | Description |
|---|---|
| `data_bases/` | All SQLite databases |
| `config/portfolio.json` | Current portfolio state |
| `config/portfolio_history.json` | Historical portfolio data |
| `config/transactions.json` | Transaction history |
| `config/variables.json` | Bot configuration variables |

---

## Setup

### 1. Clone the backup repo

```bash
git clone git@github.com:severmanolescu/your-backup-repo.git /mnt/data/Repos/Backups
```

### 2. Make the script executable

```bash
chmod +x backup.sh
```

### 3. Run manually

```bash
./backup.sh
```

### 4. Automate with cron

```bash
crontab -e
```

Add:
```bash
0 3 * * * /path/to/backup.sh
```

This runs the backup every night at 3AM.

---

## Notes

- The backup repo should be **private** on GitHub
- Ensure SSH key is configured so the push works without a password prompt
- `variables.json` may contain sensitive data such as API keys — make sure the repo is private before pushing