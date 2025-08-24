# Quant Finance Platform - Frontend

Next.js 14 frontend with TypeScript, Tailwind CSS, and MSW for API mocking.

## Features

- **Modern UI**: Next.js 14 + React 18 + TypeScript
- **Beautiful Design**: Tailwind CSS with gradient backgrounds
- **Job Console**: Create, monitor, and view financial model jobs
- **MSW Integration**: API mocking for development without backend
- **Responsive**: Mobile-first design with desktop optimization

## Quick Start

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running (optional with MSW)

### Local Development

1. **Clone and setup**:

```bash
git clone <repo>
cd frontend
npm install
```

2. **Environment variables** (optional):

```bash
# Copy and configure
cp .env.example .env

# Override API base URL if needed
NEXT_PUBLIC_API_BASE=http://localhost:8080
```

3. **Run the development server**:

```bash
npm run dev
```

4. **Open your browser**:

```
http://localhost:3000
```

## MSW (Mock Service Worker)

The frontend includes MSW for API mocking during development:

### How It Works

- **Automatic**: MSW starts automatically in development mode
- **Realistic**: Mock responses simulate real API behavior
- **Configurable**: Easy to modify mock data and responses
- **Fallback**: Can be disabled to hit real backend

### Mock Endpoints

- `POST /api/v1/jobs/` → Job creation with realistic progression
- `GET /api/v1/jobs/` → List of demo jobs
- `GET /api/v1/jobs/:id` → Job details with results
- `DELETE /api/v1/jobs/:id` → Job cancellation
- `GET /api/v1/symbols` → Available symbols list

### Mock Data

The frontend includes realistic mock data for:

- **Monte Carlo**: Simulation results with percentiles
- **Markowitz**: Portfolio optimization with weights
- **Black-Scholes**: Option pricing with Greeks

### Disabling MSW

To use the real backend instead of mocks:

```bash
# Option 1: Set environment variable
export DISABLE_MSW=true

# Option 2: Comment out MSW import in _app.tsx
# import('../mocks/browser').then(...)

# Option 3: Start backend and use real API
cd ../backend
export USE_FIXTURE=true
uvicorn app.main:app --reload --port 8080
```

## Development Workflows

### 1. Frontend Only (MSW Enabled)

```bash
cd frontend
npm run dev
# All API calls are mocked
# Perfect for UI development
```

### 2. Frontend + Backend Fixture Mode

```bash
# Terminal 1: Backend with demo data
cd backend
export USE_FIXTURE=true
export USE_SQLITE=true
uvicorn app.main:app --reload --port 8080

# Terminal 2: Frontend
cd frontend
npm run dev
# API calls hit real backend with demo data
```

### 3. Frontend + Backend Production Mode

```bash
# Terminal 1: Backend with real APIs
cd backend
export USE_FIXTURE=false
# Configure real API keys
uvicorn app.main:app --reload --port 8080

# Terminal 2: Frontend
cd frontend
npm run dev
# API calls hit real backend with live data
```

## Project Structure

```
frontend/
├── components/           # Reusable UI components
│   ├── Navbar.tsx      # Main navigation
│   └── ...
├── pages/               # Next.js pages
│   ├── _app.tsx        # App wrapper + MSW init
│   ├── jobs/           # Job management
│   │   ├── index.tsx   # Jobs list
│   │   └── [id]/       # Dynamic job routes
│   ├── montecarlo/     # Monte Carlo tool
│   ├── markowitz/      # Markowitz tool
│   └── blackscholes/   # Black-Scholes tool
├── mocks/               # MSW configuration
│   ├── handlers.ts     # API mock handlers
│   └── browser.ts      # MSW browser setup
├── lib/                 # Utilities
│   └── api.ts          # API client functions
├── styles/              # CSS and Tailwind
└── public/              # Static assets
```

## API Integration

### Configuration

The frontend automatically detects the API base URL:

```typescript
// lib/api.ts
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8080";
```

### Available Functions

```typescript
import { getJobs, createJob, getJob, cancelJob, getSymbols } from "../lib/api";

// Use in components
const jobs = await getJobs();
const newJob = await createJob(jobData);
```

## Styling

### Tailwind CSS

- **Custom Colors**: Brand colors defined in `tailwind.config.js`
- **Gradients**: Beautiful background gradients throughout
- **Responsive**: Mobile-first with desktop breakpoints
- **Components**: Pre-built component classes

### Custom Classes

```css
/* globals.css */
.bg-gradient-brand {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.text-brand-600 {
  color: #4f46e5;
}
```

## Testing

```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage

# E2E tests (if configured)
npm run test:e2e
```

## Building

```bash
# Production build
npm run build

# Start production server
npm start

# Static export (if needed)
npm run export
```

## Deployment

### Vercel (Recommended)

```bash
# Deploy to Vercel
npm run deploy

# Or connect GitHub repo for auto-deploy
```

### Docker

```bash
# Build image
docker build -t quant-finance-frontend .

# Run locally
docker run -p 3000:3000 quant-finance-frontend
```

### Environment Variables

| Variable               | Description         | Default                 |
| ---------------------- | ------------------- | ----------------------- |
| `NEXT_PUBLIC_API_BASE` | Backend API URL     | `http://localhost:8080` |
| `DISABLE_MSW`          | Disable MSW mocking | `false`                 |

## Troubleshooting

### MSW Not Working

1. Check browser console for MSW messages
2. Verify `mocks/browser.ts` is imported in `_app.tsx`
3. Ensure development mode (`NODE_ENV=development`)
4. Check for Service Worker conflicts

### API Calls Failing

1. Verify backend is running on correct port
2. Check `NEXT_PUBLIC_API_BASE` environment variable
3. Ensure CORS is configured on backend
4. Check browser network tab for errors

### Build Errors

1. Clear `.next` directory: `rm -rf .next`
2. Reinstall dependencies: `rm -rf node_modules && npm install`
3. Check TypeScript errors: `npm run type-check`
4. Verify all imports are correct
