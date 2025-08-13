# Cortex Dashboard - Script Usage Guide

## Running Scripts in Windows

### PowerShell (Recommended)
In PowerShell, you need to prefix scripts with `.\`:

```powershell
# Fresh installation (removes all data)
.\fresh_install.bat

# Rebuild after code changes
.\rebuild.bat           # Rebuild all
.\rebuild.bat backend   # Rebuild backend only
.\rebuild.bat frontend  # Rebuild frontend only

# Quick restart (no rebuild)
.\restart.bat           # Restart all
.\restart.bat backend   # Restart backend only

# Development helper
.\dev.bat              # Show menu
.\dev.bat logs         # View logs
.\dev.bat db           # Connect to database
.\dev.bat status       # Check status
```

### Command Prompt (CMD)
In Command Prompt, you can run directly:

```cmd
fresh_install.bat
rebuild.bat
restart.bat
dev.bat
```

## Common Workflows

### 1. First Time Setup
```powershell
.\fresh_install.bat
```
This will:
- Remove any existing containers and volumes
- Build fresh images
- Initialize database with correct schema
- Create default organization
- Set up admin user

### 2. After Backend Code Changes
```powershell
.\rebuild.bat backend
```

### 3. After Frontend Code Changes
```powershell
.\rebuild.bat frontend
```

### 4. View Logs
```powershell
.\dev.bat logs
# Or for specific service
.\dev.bat backend-logs
```

### 5. Connect to Database
```powershell
.\dev.bat db
```

## Linux/Mac Users

For Linux/Mac, use the .sh versions:
```bash
# Make scripts executable first (one time)
chmod +x fresh_install.sh rebuild.sh

# Run scripts
./fresh_install.sh
./rebuild.sh backend
```

## Quick Reference

| Task | Command |
|------|---------|
| Fresh install | `.\fresh_install.bat` |
| Rebuild all | `.\rebuild.bat` |
| Rebuild backend | `.\rebuild.bat backend` |
| Rebuild frontend | `.\rebuild.bat frontend` |
| Restart all | `.\restart.bat` |
| View logs | `.\dev.bat logs` |
| Database console | `.\dev.bat db` |
| Container status | `.\dev.bat status` |
| Stop all | `.\dev.bat stop` |
| Start all | `.\dev.bat start` |

## Important Notes

1. **Fresh Install** - Removes ALL data. Use only when you want a complete reset.
2. **Rebuild** - Preserves database data, only rebuilds code.
3. **Restart** - Quick restart without rebuilding images.

## Troubleshooting

If scripts don't run in PowerShell, you might need to:

1. Use the `.\` prefix (as shown above)
2. Or change execution policy:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```