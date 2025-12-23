# ATLAS Frontend

Next.js 14+ App Router frontend for the ATLAS Decision Intelligence Engine.

## Features

- **TypeScript**: Full type safety
- **App Router**: Next.js 14+ App Router architecture
- **Clean Styling**: Minimal design with Tailwind CSS and strong typography
- **Two Routes**: 
  - `/` - Input form for market viability analysis
  - `/report` - Results memo viewer
- **PDF Export**: Download analysis as PDF memo
- **Evidence Ledger**: Toggleable debug mode to view evidence ledger

## Prerequisites

- Node.js 18+ and npm
- Backend API running (default: `http://localhost:8000`)

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `.env.local` file from the example:

```bash
cp .env.local.example .env.local
```

Edit `.env.local` and set your backend API URL:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

**Note**: Update the URL if your backend is running on a different host/port.

### 3. Run Development Server

```bash
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000)

### 4. Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx              # Input form route (/)
│   ├── report/
│   │   └── page.tsx          # Results memo viewer route (/report)
│   ├── layout.tsx            # Root layout
│   └── globals.css           # Global styles and Tailwind imports
├── .env.local.example        # Environment variables template
├── package.json              # Dependencies and scripts
├── tailwind.config.js        # Tailwind CSS configuration
├── tsconfig.json             # TypeScript configuration
├── next.config.js            # Next.js configuration
└── README.md                 # This file
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000/api/v1` |

## Usage

1. **Fill out the form** at `/` with your startup idea details
2. **Submit** to start the analysis
3. **View results** at `/report` in a professional memo format
4. **Download PDF** using the "Download PDF Memo" button
5. **Toggle Evidence Ledger** to view detailed evidence (if debug mode was enabled)

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

### Tech Stack

- **Next.js 14+**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Inter Font**: Clean, professional typography

## Troubleshooting

### Backend Connection Issues

If you see connection errors:
1. Ensure the backend is running
2. Check `NEXT_PUBLIC_API_URL` in `.env.local` matches your backend URL
3. Verify CORS is enabled on the backend

### Build Errors

If you encounter build errors:
1. Delete `node_modules` and `.next` folders
2. Run `npm install` again
3. Try `npm run build` again

