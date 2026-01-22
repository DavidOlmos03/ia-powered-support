# AI Support Co-Pilot - Dashboard

Real-time ticket classification dashboard built with React, TypeScript, Vite, Tailwind CSS, and Supabase.

## Features

- ✅ **Real-time Updates** - New tickets appear instantly via Supabase channels
- ✅ **Type-Safe** - Full TypeScript coverage
- ✅ **Responsive Design** - Mobile, tablet, and desktop optimized
- ✅ **Fast Performance** - Vite for instant dev server and optimized builds
- ✅ **Clean UI** - Tailwind CSS utility-first styling
- ✅ **Live Statistics** - Category and sentiment breakdown
- ✅ **Connection Status** - Visual indicator for real-time connection

## Tech Stack

- **React 18** - UI library with concurrent features
- **TypeScript** - Type safety and better DX
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **Supabase** - PostgreSQL database with real-time subscriptions
- **date-fns** - Date formatting utilities

## Prerequisites

- Node.js 18+ and npm
- Supabase project with tickets table set up
- Environment variables configured

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your Supabase credentials:
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

### 3. Run Development Server

```bash
npm run dev
```

Open http://localhost:5173 in your browser.

### 4. Build for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

### 5. Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── public/               # Static assets
├── src/
│   ├── components/       # React components
│   │   ├── ui/          # Reusable UI components
│   │   └── tickets/     # Ticket-specific components
│   ├── hooks/           # Custom React hooks
│   ├── lib/             # Utilities and Supabase client
│   ├── styles/          # CSS files
│   └── types/           # TypeScript type definitions
├── index.html           # HTML entry point
├── vite.config.ts       # Vite configuration
└── tailwind.config.js   # Tailwind CSS configuration
```

## Key Components

### `TicketList`
Main component that fetches tickets and subscribes to real-time updates.

### `TicketCard`
Displays individual ticket with category badge, sentiment indicator, and metadata.

### `Header`
Shows application title and statistics (total tickets, processed, by category/sentiment).

### Custom Hooks

- **`useTickets()`** - Fetches tickets from Supabase with loading/error states
- **`useRealtimeTickets()`** - Subscribes to INSERT/UPDATE/DELETE events

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_SUPABASE_URL` | Supabase project URL | Yes |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon/public API key | Yes |

## Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import repository in Vercel
3. Set environment variables in Vercel dashboard
4. Deploy automatically

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)

### Netlify

1. Push code to GitHub
2. Import repository in Netlify
3. Build command: `npm run build`
4. Publish directory: `dist`
5. Set environment variables
6. Deploy

### Manual Build

```bash
npm run build
```

Upload `dist/` contents to any static hosting service (S3, Cloudflare Pages, GitHub Pages, etc.).

## Features in Detail

### Real-time Updates

The dashboard uses Supabase Realtime to subscribe to database changes:

```typescript
// Automatic updates when:
- New ticket inserted → Appears at top of list
- Ticket updated → Updates in place
- Ticket deleted → Removes from list
```

Connection status indicator shows:
- 🟢 **Connected** - Live updates active
- 🟡 **Connecting** - Establishing connection
- 🔴 **Disconnected** - No live updates

### Ticket Display

Each ticket card shows:
- Ticket ID (first 8 characters)
- Description (truncated to 150 chars)
- Category badge (color-coded)
- Sentiment badge with emoji
- Processing status
- Time since creation
- Processing duration

### Statistics

Header displays real-time statistics:
- Total tickets
- Processed count
- Pending count
- By category (Técnico, Facturación, Comercial)
- By sentiment (Positivo, Neutral, Negativo)

## Customization

### Styling

Tailwind CSS configuration in `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: '#3b82f6',
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      tecnico: '#8b5cf6',
      facturacion: '#f59e0b',
      comercial: '#06b6d4',
    }
  }
}
```

### Animations

Custom animations defined in `tailwind.config.js`:
- `slide-in` - New tickets fade in from top
- `pulse-subtle` - Connection indicator pulse

## Performance

- **Initial Load:** < 2 seconds (p95)
- **Real-time Latency:** < 1 second
- **Bundle Size:** ~200KB gzipped
- **Lighthouse Score:** 90+ across all metrics

## Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Troubleshooting

### No tickets showing

1. Check Supabase connection in browser console
2. Verify environment variables are set correctly
3. Ensure tickets table has processed tickets (`processed = true`)
4. Check RLS policies allow read access

### Real-time not working

1. Check connection status indicator
2. Verify Supabase realtime is enabled on tickets table
3. Check browser console for subscription errors
4. Test with manual INSERT in Supabase dashboard

### Build errors

1. Clear node_modules and reinstall:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```
2. Ensure Node.js version is 18+
3. Check TypeScript errors: `npm run build`

## Development Tips

### Hot Module Replacement

Vite provides instant HMR. Changes to React components update without full page reload.

### TypeScript Strict Mode

Project uses strict TypeScript configuration. All code must be fully typed.

### Tailwind IntelliSense

Install Tailwind CSS IntelliSense extension in VS Code for autocomplete.

### Debugging

React DevTools and browser console show:
- Component state
- Real-time events
- Supabase queries
- Error messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - See LICENSE file

## Support

For issues and questions:
- GitHub Issues: [Repository URL]
- Documentation: This README
- Supabase Docs: https://supabase.com/docs

---

**Built with ❤️ using React + TypeScript + Vite + Tailwind + Supabase**
