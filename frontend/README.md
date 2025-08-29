# Frontend Application

Next.js-based web interface for the Quant Finance Platform, providing job management, financial modeling forms, and real-time monitoring.

## 🚀 Features

- **Job Management**: Create, monitor, and view financial modeling jobs
- **Financial Model Forms**: Interactive parameter input for Monte Carlo, Markowitz, and Black-Scholes
- **Real-time Updates**: Live job status monitoring
- **Responsive Design**: Mobile-first design using Tailwind CSS
- **MSW Integration**: Mock Service Worker for development

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js App   │    │   React Hooks   │    │   API Client    │
│   (Pages/Routes)│◄──►│   (State Mgmt)  │◄──►│   (HTTP Calls)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Components    │    │   Tailwind CSS  │    │   MSW (Dev)     │
│   (Reusable UI) │    │   (Styling)     │    │   (Mocking)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
frontend/
├── components/           # Reusable UI components
│   ├── Navbar.tsx      # Navigation component
│   ├── JobForm.tsx     # Job creation form
│   ├── JobList.tsx     # Job listing and monitoring
│   ├── JobResults.tsx  # Job results visualization
│   └── ui/             # Base UI components
├── pages/               # Next.js pages
│   ├── _app.tsx        # App wrapper with MSW setup
│   ├── index.tsx       # Home page
│   ├── jobs/           # Job management pages
│   ├── montecarlo.tsx  # Monte Carlo simulation page
│   ├── markowitz.tsx   # Portfolio optimization page
│   ├── blackscholes.tsx # Option pricing page
│   └── test-msw.tsx    # MSW testing page
├── lib/                 # Utility libraries
│   └── api.ts          # API client functions
├── mocks/               # Mock Service Worker setup
│   ├── handlers.ts     # API mock handlers
│   └── browser.ts      # MSW browser configuration
├── styles/              # Global styles
│   └── globals.css     # Tailwind CSS imports
├── public/              # Static assets
├── package.json         # Dependencies and scripts
├── next.config.js       # Next.js configuration
└── tsconfig.json        # TypeScript configuration
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- npm or yarn package manager

### Setup

1. **Install dependencies**

```bash
npm install
```

2. **Environment variables**

```bash
# Create .env.local file
NEXT_PUBLIC_API_BASE=http://localhost:8080
```

3. **Run development server**

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## 🛠️ Tech Stack

- **Framework**: Next.js 14 with TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React hooks
- **API Mocking**: MSW for development
- **Build Tool**: Webpack (Next.js default)

## 📚 Pages

### Core Pages

- **Home** (`/`): Platform overview and navigation
- **Jobs** (`/jobs`): Job management and monitoring
- **Job Details** (`/jobs/[id]`): Individual job information and results

### Financial Models

- **Monte Carlo** (`/montecarlo`): Stock price simulation
- **Markowitz** (`/markowitz`): Portfolio optimization
- **Black-Scholes** (`/blackscholes`): Option pricing

## 🧪 Development

### MSW (Mock Service Worker)

The frontend uses MSW to mock API calls during development, allowing you to work without a running backend.

- **Mock Data**: Realistic sample data for all financial models
- **API Handlers**: Mock endpoints for job management
- **Development Workflow**: Seamless switching between mock and real APIs

### Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript type checking
```

## 🔧 Configuration

### Environment Variables

| Variable               | Description          | Default                 |
| ---------------------- | -------------------- | ----------------------- |
| `NEXT_PUBLIC_API_BASE` | Backend API base URL | `http://localhost:8080` |

### Next.js Configuration

- **Port**: 3000 (configurable)
- **TypeScript**: Enabled with strict mode
- **ESLint**: Configured for code quality
- **Tailwind**: Utility-first CSS framework

## 🚀 Deployment

### Build for Production

```bash
npm run build
```

### Docker

```bash
docker build -t quant-finance-frontend .
docker run -p 3000:3000 quant-finance-frontend
```

### Vercel (Recommended)

```bash
npm install -g vercel
vercel
```

## 📚 Documentation

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [MSW Documentation](https://mswjs.io/docs/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**: Change port in `package.json` scripts
2. **MSW not working**: Check browser console for service worker errors
3. **TypeScript errors**: Run `npm run type-check` to see all issues
4. **Build failures**: Clear `.next` folder and reinstall dependencies
