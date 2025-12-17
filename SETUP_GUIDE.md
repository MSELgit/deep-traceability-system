# Deep Traceability System - Setup Guide

## Prerequisites

- Node.js (v18 or higher)
- Python 3.10 or higher
- npm or yarn

## Quick Start

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- On macOS/Linux:
  ```bash
  source venv/bin/activate
  ```
- On Windows:
  ```bash
  venv\Scripts\activate
  ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create data directory:
```bash
mkdir -p data
```

6. Run database migration (if needed):
```bash
python migrations/add_priority_to_needs.py
```

7. Start the backend server:
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open your browser and navigate to:
```
http://localhost:5173
```

## Docker Setup (Alternative)

If you prefer using Docker:

```bash
docker-compose -f docker-compose.local.yml up --build
```

## Database

The system uses SQLite by default. The database file will be created automatically at:
- `backend/data/local.db`

## Environment Variables

No additional environment variables are required for basic setup. The system uses default configurations suitable for development.

## Features

- **Stakeholder-Need Matrix**: Define relationships between stakeholders and needs
- **Need-Performance Matrix**: Map needs to performance metrics with utility functions
- **Mountain View**: 3D visualization of design alternatives
- **Network Editor**: Create and visualize system networks
- **Two-Axis Evaluation**: Compare design alternatives on multiple dimensions

## Recent Updates

- **Priority System**: Needs can now have priorities (0-1) that affect vote distribution
- **Normalized Valid Votes**: Valid votes are normalized to sum to 1.0 for relative comparison
- **Enhanced Visualization**: Improved 3D mountain view with normalized height calculations

## Troubleshooting

1. **Port already in use**: If port 8000 or 5173 is already in use, you can change the port:
   - Backend: `uvicorn app.main:app --reload --port 8001`
   - Frontend: Update `vite.config.ts` to use a different port

2. **Database errors**: Delete `backend/data/local.db` and restart the backend to create a fresh database

3. **Module not found errors**: Ensure you've activated the virtual environment and installed all dependencies

## Support

For questions or issues, please refer to the main README.md file or create an issue in the project repository.