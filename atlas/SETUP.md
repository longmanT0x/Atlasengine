# ATLAS Setup Guide

Complete setup instructions for running ATLAS locally and in production.

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- npm or yarn

## Backend Setup

### 1. Install Python Dependencies

```bash
cd atlas/backend
pip install -r requirements.txt
```

### 2. Environment Configuration (Optional)

Create a `.env` file in `atlas/backend/`:

```env
# CORS Configuration
CORS_ORIGINS=http://localhost:3000

# Research Configuration
MAX_SOURCES=8

# Debug Mode
DEBUG=False

# Optional: LLM Configuration
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
```

### 3. Run Backend

```bash
cd atlas/backend
uvicorn main:app --reload
```

Backend will be available at: http://localhost:8000

## Frontend Setup

### 1. Install Node Dependencies

```bash
cd atlas/frontend
npm install
```

### 2. Environment Configuration

Create a `.env.local` file in `atlas/frontend/`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 3. Run Frontend

```bash
cd atlas/frontend
npm run dev
```

Frontend will be available at: http://localhost:3000

## Database

The SQLite database is automatically created on first run at:
`atlas/backend/app/storage/atlas.db`

No manual database setup is required.

## Testing

### Backend Tests

```bash
cd atlas/backend
pytest
```

### Frontend Tests

```bash
cd atlas/frontend
npm test
```

## Production Deployment

### Backend

1. Set environment variables:
   - `CORS_ORIGINS` to your frontend domain
   - `DEBUG=False`

2. Use production server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend

1. Build:
```bash
npm run build
```

2. Start:
```bash
npm start
```

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (should be 3.11+)
- Verify dependencies: `pip list`
- Check database permissions

### Frontend can't connect to backend
- Verify backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Check CORS configuration in backend

### Database errors
- Delete `atlas/backend/app/storage/atlas.db` to recreate
- Check file permissions on database directory


