# OCR-MCP Frontend

A production-ready, enterprise-grade React/TypeScript frontend for the OCR-MCP server with state-of-the-art UX, comprehensive internationalization, error handling, and performance monitoring.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open http://localhost:3000
```

## 🎯 Key Features

### ✨ Production-Ready Architecture
- **React 18 + TypeScript** with strict type checking
- **Error Boundaries** with graceful fallbacks
- **Performance Monitoring** with Core Web Vitals tracking
- **Internationalization** (EN, DE, FR, ES)
- **Comprehensive Testing** with Vitest + React Testing Library
- **Docker Deployment** ready

### 🎨 Beautiful Design System
- **Glassmorphism Effects** with backdrop blur
- **Dark/Light/System Themes** with persistence
- **Smooth Animations** and micro-interactions
- **Responsive Design** for all screen sizes
- **Enterprise Typography** and spacing

### 📱 Complete Three-Column Layout
- **Left Sidebar Navigation** with active states
- **Main Content Area** with page routing
- **Right Sidebar** with metadata and context
- **Slide-in Animations** with proper z-index management

### 🔧 All Mod Cons Modal System
- **Logger Modal** with real-time structured logging
- **Help Modal** with searchable documentation
- **Settings Modal** with comprehensive preferences
- **Scanner Settings Modal** with device profiles
- **Beautiful Modal Infrastructure** with glassmorphism

### 🌐 Internationalization
- **Multi-language Support** with react-i18next
- **Language Detection** and persistence
- **RTL Support** ready for Arabic/Hebrew
- **Translation Files** for easy maintenance

## Available Pages

- **Upload**: Single document processing with drag & drop
- **Batch**: Multi-document batch processing with progress tracking
- **Scanner**: Direct scanner control with preview
- **Analysis**: Advanced document analysis (text, tables, layout, quality)
- **Quality**: Comprehensive quality assessment with recommendations
- **Settings**: Comprehensive application preferences

## Key Features

### Topbar Controls
- **Authentication**: Login/logout with user management
- **Theme Toggle**: Light/dark/system mode switching
- **Language Selector**: Multi-language support ready
- **Help Button**: Integrated help system (modal ready)
- **Logger Panel**: Activity monitoring with live updates

### Sidebars
- **Left Sidebar**: Page navigation with active state indicators
- **Right Sidebar**: Document metadata, processing status, system info
- **Slide Animations**: Smooth transitions with proper z-indexing

### Modal System (All Mod Cons!)
- **Logger Modal**: Structured logging with real-time updates
- **Help Modal**: Searchable documentation system
- **Settings Modal**: Comprehensive preferences management
- **Scanner Settings Modal**: Device configuration and profiles

## 🚀 Development Commands

```bash
# Development
npm run dev              # Start development server (HMR enabled)
npm run build           # Production build with optimizations
npm run build:analyze   # Build with bundle analysis
npm run preview         # Preview production build locally

# Code Quality
npm run lint            # Run ESLint
npm run lint:fix        # Fix ESLint issues automatically
npm run type-check      # TypeScript type checking

# Testing
npm run test            # Run tests in watch mode
npm run test:ui         # Run tests with UI
npm run test:coverage   # Run tests with coverage report

# Docker
npm run docker:build    # Build Docker image
npm run docker:run      # Run Docker container
npm run docker:up       # Start with docker-compose
npm run docker:down     # Stop docker-compose

# Maintenance
npm run clean           # Clean build artifacts
npm run predeploy       # Pre-deployment checks (types + tests + build)
```

## 🐳 Docker Deployment

### Quick Start with Docker
```bash
# Build and run
npm run docker:build && npm run docker:run

# Or use docker-compose
npm run docker:up
```

### Production Deployment
```bash
# Pre-deployment checks
npm run predeploy

# Build optimized production image
docker build -t ocr-mcp-frontend:latest .

# Run in production
docker run -p 80:80 --name ocr-mcp-frontend ocr-mcp-frontend:latest
```

## 🌐 Internationalization

### Supported Languages
- **English (en)** - Complete translations
- **German (de)** - Core translations
- **French (fr)** - Ready for translation
- **Spanish (es)** - Ready for translation

### Adding New Languages
1. Create `src/locales/[lang].json`
2. Copy English translations as base
3. Translate values (keep keys in English)
4. Import in `src/lib/i18n.ts`

### Using Translations in Components
```typescript
import { useTranslation } from 'react-i18next'

function MyComponent() {
  const { t } = useTranslation()

  return <h1>{t('pages.upload.title')}</h1>
}
```

## Architecture

- **React 18** with TypeScript for type safety
- **Zustand** for global state management
- **React Query** for server state and caching
- **React Router** for client-side navigation
- **Tailwind CSS** with custom design tokens
- **Radix UI** primitives for accessibility

## Project Structure

```
src/
├── components/
│   ├── layout/          # Topbar, sidebars, main layout
│   ├── ui/              # Reusable UI components
│   ├── features/        # Feature-specific components
│   └── providers/       # Context providers
├── pages/               # Route components
├── stores/              # Zustand stores
├── types/               # TypeScript definitions
├── utils/               # Helper functions
└── lib/                 # Configuration and utilities
```

## 📊 Performance & Monitoring

### Core Web Vitals Targets
- **LCP** (Largest Contentful Paint): < 2.5s
- **FID** (First Input Delay): < 100ms
- **CLS** (Cumulative Layout Shift): < 0.1

### Bundle Metrics
- **Initial Load**: < 200KB gzipped
- **Main Chunk**: < 100KB gzipped
- **Vendor Chunk**: < 50KB gzipped

### Performance Monitoring
- Real-time Core Web Vitals tracking
- Memory usage monitoring
- Error boundary with automatic reporting
- Bundle analysis with `npm run build:analyze`

## 🧪 Testing Strategy

### Test Categories
- **Unit Tests**: Component logic and utilities
- **Integration Tests**: Component interactions
- **E2E Tests**: User workflow testing (future)

### Running Tests
```bash
# Watch mode (recommended for development)
npm run test

# Single run with coverage
npm run test:coverage

# Visual test runner
npm run test:ui
```

## 🏗️ Project Structure

```
frontend-new/
├── src/
│   ├── components/
│   │   ├── layout/          # Topbar, sidebars, main layout
│   │   ├── ui/              # Base UI components (Button, Dialog)
│   │   ├── modals/          # All modal components
│   │   ├── features/        # Feature-specific components
│   │   └── providers/       # Context providers
│   ├── pages/               # Route components
│   ├── stores/              # Zustand stores
│   ├── hooks/               # Custom React hooks
│   ├── lib/                 # Utilities (i18n, utils)
│   ├── types/               # TypeScript definitions
│   ├── utils/               # Helper functions
│   ├── locales/             # Translation files
│   ├── test/                # Test utilities
│   └── styles/              # Global styles
├── public/                  # Static assets
├── docker/                  # Docker files
├── nginx.conf               # Nginx configuration
├── docker-compose.yml       # Docker Compose setup
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── vite.config.ts
├── .eslintrc.json          # ESLint configuration
└── README.md
```

## 🔧 Configuration

### Environment Variables
```bash
# .env.local
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_ENV=development
```

### Build Configuration
- **Vite** for fast development and optimized production builds
- **TypeScript** with strict mode and path aliases
- **Tailwind CSS** with custom design tokens
- **ESLint** for code quality and consistency

## 🚨 Error Handling

### Global Error Boundary
- Catches React component errors
- Displays user-friendly error messages
- Includes error details in development
- Automatic error reporting (ready for integration)

### Error Recovery
- "Try Again" functionality
- Page reload option
- Graceful degradation
- Error logging and monitoring

## 📈 Status

**Phase 4 Complete**: Production-ready with internationalization, error handling, performance monitoring, Docker deployment, and comprehensive testing setup!

### ✅ Completed Features
- **Error Boundaries** with graceful fallbacks
- **Internationalization** (EN/DE/FR/ES) with react-i18next
- **Performance Monitoring** with Core Web Vitals tracking
- **Docker Deployment** with nginx and docker-compose
- **Testing Setup** with Vitest and React Testing Library
- **Build Optimization** for production deployment
- **Code Quality** with ESLint and TypeScript strict mode

### 🎯 Ready for Production
- Enterprise-grade error handling
- Multi-language support
- Performance monitoring and optimization
- Docker containerization
- Comprehensive testing suite
- Production build pipeline

---

**Built with ❤️ using modern React, TypeScript, and enterprise best practices**

**Deploy with confidence!** 🚀