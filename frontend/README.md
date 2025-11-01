# Frontend Setup

## Quick Start

### Option 1: Using Python (Recommended for development)

```bash
# Make sure you're in the frontend directory
cd /home/user/app-buildify/frontend

# Start the development server
python3 -m http.server 8080
```

Then open your browser to: **http://localhost:8080**

### Option 2: Using the provided script

```bash
# From the app-buildify root directory
cd /home/user/app-buildify
./start-frontend.sh
```

## Important Notes

1. **Always start the server from the `frontend` directory**
   - If you start it from the wrong directory, the JavaScript modules won't load correctly

2. **Make sure the backend is running**
   - The frontend needs the backend API at http://localhost:8000
   - Start the backend with: `cd backend && uvicorn app.main:app --reload`

3. **Clear your browser cache**
   - If you see old errors, do a hard refresh: `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)

## Troubleshooting

### "Failed to load module script" errors

This error usually means:
- The server isn't running from the correct directory
- The backend isn't running
- Your browser has cached old files

**Fix:**
1. Make sure you're in the `/home/user/app-buildify/frontend` directory
2. Start the server: `python3 -m http.server 8080`
3. Make sure backend is running on port 8000
4. Clear browser cache and reload

### Nothing shows on the page

1. Check browser console for errors
2. Verify backend is running: `curl http://localhost:8000/api/health`
3. Clear browser cache and reload

## File Structure

```
frontend/
├── index.html              # Entry point (loads after login)
├── assets/
│   ├── templates/
│   │   ├── login.html     # Login page
│   │   ├── main.html      # Main app layout
│   │   └── ...            # Other page templates
│   ├── js/
│   │   ├── app-entry.js   # JavaScript entry point
│   │   ├── app.js         # Main app logic
│   │   ├── api.js         # API client
│   │   ├── rbac.js        # Role-based access control
│   │   └── ...            # Other modules
│   └── css/
│       └── app.css        # Custom styles
└── README.md              # This file
```
