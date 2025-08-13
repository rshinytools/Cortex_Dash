# Cortex Clinical Dashboard

A modern clinical trial data management and visualization platform.

## Quick Start

### Prerequisites
- Docker Desktop installed and running
- At least 8GB RAM available
- Ports 3000 and 8000 available

### Installation

1. **Fresh Installation** (removes all existing data):
   ```powershell
   .\fresh_install.bat
   ```

2. **Access the Application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

3. **Default Login**:
   - Email: `admin@sagarmatha.ai`
   - Password: `adadad123`

## Development Commands

### Rebuild After Code Changes
```powershell
# Rebuild all services
.\rebuild.bat

# Rebuild specific service
.\rebuild.bat backend
.\rebuild.bat frontend
```

### Quick Restart (no rebuild)
```powershell
.\restart.bat
```

### Development Helper
```powershell
# Show all available commands
.\dev.bat

# View logs
.\dev.bat logs

# Connect to database
.\dev.bat db

# Check status
.\dev.bat status
```

## Project Structure

```
Cortex_Dash/
├── backend/          # FastAPI backend application
├── frontend/         # Next.js frontend application
├── data/            # Data storage directory
├── Implementation/  # Project documentation
├── tests/           # Test files
└── Trash/           # Archived/unused files
```

## Tech Stack

- **Backend**: FastAPI, PostgreSQL, SQLAlchemy, Celery
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui
- **Infrastructure**: Docker, Redis

## Documentation

See the `Implementation/` folder for detailed documentation:
- `USER_MANUAL.md` - User guide
- `FRESH_INSTALL_SETUP.md` - Installation details
- `README_SCRIPTS.md` - Script usage guide

## Support

For issues or questions, please contact the development team.