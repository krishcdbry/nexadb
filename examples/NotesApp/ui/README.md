# NexaDB Notes UI

A beautiful, interactive web interface for the NexaDB Notes API built with React, TypeScript, Vite, and Tailwind CSS.

## Features

- **Create, Edit, Delete Notes** - Full CRUD operations
- **Text Search** - Search notes by title and content
- **Semantic Search** - Find similar notes using vector similarity
- **Tag Management** - Filter notes by tags and view popular tags
- **Archive/Unarchive** - Organize notes by archiving completed items
- **Real-time Statistics** - View total notes, active notes, archived notes, and notes created today
- **Responsive Design** - Beautiful UI that works on all devices
- **Modern Tech Stack** - React 18, TypeScript, Vite, Tailwind CSS

## Prerequisites

Before running the UI, make sure you have:

1. **Node.js 18+** installed
2. **NexaDB server running** on port 6970
3. **Notes API server running** on port 8000

## Installation

\`\`\`bash
# Navigate to the UI directory
cd ui

# Install dependencies
npm install
\`\`\`

## Running the Application

\`\`\`bash
# Development mode with hot reload
npm run dev
\`\`\`

The UI will be available at **http://localhost:5173**

## Building for Production

\`\`\`bash
# Build the app
npm run build

# Preview the production build
npm run preview
\`\`\`

## Usage

### Creating a Note

1. Click the **"+ New Note"** button
2. Fill in the title, content, and tags (comma-separated)
3. Click **"Create Note"**

### Searching Notes

**Text Search:**
- Enter keywords in the "Text Search" input
- Press Enter or click "Search"
- Results will show notes matching the text

**Semantic Search:**
- Enter a concept or phrase in the "Semantic Search" input
- Press Enter or click "Search"
- Results will show notes similar by meaning

### Filtering by Tags

- Click on any tag to filter notes by that tag
- Popular tags are shown at the top
- Click **"Clear Filters"** to reset

### Archiving Notes

- Click **"Archive"** on any note to archive it
- Click **"Archived"** button to view archived notes
- Click **"Unarchive"** to restore a note

### Editing Notes

- Click **"Edit"** on any note
- Modify the title, content, or tags
- Click **"Update Note"** to save changes

### Deleting Notes

- Click **"Delete"** on any note
- Confirm the deletion

## API Configuration

The UI connects to the Notes API at \`http://localhost:8000\`.

To change the API URL, edit \`src/api/notes.ts\`:

\`\`\`typescript
const API_BASE_URL = 'http://your-api-url:port';
\`\`\`

## Project Structure

\`\`\`
ui/
├── src/
│   ├── api/
│   │   └── notes.ts          # API client for Notes API
│   ├── types/
│   │   └── note.ts           # TypeScript type definitions
│   ├── App.tsx               # Main application component
│   ├── main.tsx              # Application entry point
│   └── index.css             # Global styles with Tailwind
├── public/                   # Static assets
├── index.html                # HTML template
├── package.json              # Dependencies and scripts
├── tailwind.config.js        # Tailwind CSS configuration
├── tsconfig.json             # TypeScript configuration
└── vite.config.ts            # Vite configuration
\`\`\`

## Available Scripts

- \`npm run dev\` - Start development server
- \`npm run build\` - Build for production
- \`npm run preview\` - Preview production build
- \`npm run lint\` - Run ESLint

## Technologies Used

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Fetch API** - HTTP requests

## Features Overview

### Statistics Dashboard
View key metrics at a glance:
- Total notes count
- Active notes count
- Archived notes count
- Notes created today

### Search Capabilities
- **Text Search**: Traditional keyword-based search
- **Vector Search**: AI-powered semantic similarity search

### Tag System
- Add multiple tags to notes (comma-separated)
- Click tags to filter notes
- View most popular tags
- Tag-based organization

### Archive System
- Archive completed or old notes
- Keep workspace clean
- Easy restoration of archived notes

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Development

### Adding New Features

1. Create new components in \`src/components/\`
2. Add types to \`src/types/\`
3. Extend API client in \`src/api/notes.ts\`
4. Update App.tsx to use new features

### Styling

This project uses Tailwind CSS. Refer to [Tailwind documentation](https://tailwindcss.com/docs) for utility classes.

## Troubleshooting

**API Connection Error**
\`\`\`
Failed to fetch notes
\`\`\`
- Ensure the Notes API is running on http://localhost:8000
- Check browser console for CORS errors
- Verify NexaDB server is running on port 6970

**Build Errors**
\`\`\`
npm run build fails
\`\`\`
- Delete \`node_modules\` and run \`npm install\` again
- Ensure Node.js version is 18 or higher

**Blank Page After Build**
\`\`\`
Production build shows blank page
\`\`\`
- Check browser console for errors
- Verify API_BASE_URL is accessible from your deployment

## License

This UI is part of the NexaDB project.

## Support

For issues or questions:
- NexaDB Documentation
- GitHub Issues
- Community Discord
