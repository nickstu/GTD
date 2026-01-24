# GTD Task Management Application

## Overview

This is a Getting Things Done (GTD) productivity application built with a React frontend and Express backend. It implements the core GTD methodology with features for capturing, clarifying, organizing, and reviewing tasks and projects. The application follows a clean, minimalist design philosophy with keyboard-centric navigation.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: React with TypeScript, using Vite as the build tool
- **Routing**: Wouter for lightweight client-side routing
- **State Management**: TanStack React Query for server state management with optimistic updates
- **UI Components**: shadcn/ui component library built on Radix UI primitives
- **Styling**: Tailwind CSS with custom CSS variables for theming
- **Drag and Drop**: @dnd-kit for sortable task lists on the dashboard

### Backend Architecture
- **Framework**: Express.js with TypeScript
- **API Design**: RESTful endpoints defined in `shared/routes.ts` with Zod schemas for validation
- **Database ORM**: Drizzle ORM with PostgreSQL dialect
- **Build Process**: esbuild for server bundling, Vite for client bundling

### Data Layer
- **Database**: PostgreSQL (configured via DATABASE_URL environment variable)
- **Schema Location**: `shared/schema.ts` contains all table definitions using Drizzle
- **Core Entities**:
  - `items`: Tasks with status (inbox, next, waiting, someday, reference, done, trash), optional project association, time estimates, energy levels, and due dates
  - `projects`: Multi-step outcomes with name, desired outcome description, and status (active, completed, archived)

### Shared Code Pattern
The `shared/` directory contains code used by both frontend and backend:
- `schema.ts`: Database table definitions and Zod validation schemas
- `routes.ts`: API contract definitions with paths, methods, input schemas, and response types

### Key Design Decisions
- **Type-safe API**: Zod schemas defined once in shared routes, used for both client-side validation and server-side parsing
- **GTD Workflow**: Status-based item organization mirrors GTD buckets (Inbox, Next Actions, Waiting For, Someday/Maybe, Reference)
- **Keyboard Shortcuts**: Global shortcuts for quick capture ('q' or 'c') built into the layout shell

## External Dependencies

### Database
- PostgreSQL database required (connection via DATABASE_URL environment variable)
- Drizzle Kit for schema migrations (`npm run db:push`)

### Third-Party Libraries
- **UI**: Radix UI primitives, Lucide React icons, class-variance-authority for component variants
- **Date Handling**: date-fns for calendar and due date formatting
- **Forms**: react-hook-form with Zod resolver for form validation

### Development Tools
- Replit-specific Vite plugins for development (cartographer, dev-banner, runtime-error-modal)
- TypeScript with strict mode enabled