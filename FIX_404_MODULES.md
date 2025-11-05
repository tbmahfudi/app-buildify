# Fix: Module Management Page Returns 404

## Problem

When navigating to `http://localhost:8000/app#modules`, you get:
```json
{"detail":"Not Found"}
```

## Root Cause

The `modules.html` template file was just created but the **backend server hasn't been restarted** to serve it. The backend is returning a FastAPI 404 error instead of serving the static file.

## Solution: Restart Backend

You need to restart your backend server to pick up the new template file:

### If using Docker:
```bash
cd /home/user/app-buildify
docker-compose restart backend
# or
docker-compose restart
```

### If running directly:
```bash
# Stop the current process (Ctrl+C) and restart
cd /home/user/app-buildify
./manage.sh restart
# or
python backend/app/main.py
```

### If using systemd:
```bash
sudo systemctl restart app-buildify
```

## Verify the Fix

After restarting, check if the template is accessible:

```bash
# Test if the template file is being served
curl http://localhost:8000/assets/templates/modules.html
```

You should see the HTML content, not a JSON error.

Then navigate to: `http://localhost:8000/app#modules`

## Alternative: Create the File in Running Container

If you can't restart, you can create the file directly in the running container:

```bash
# Find the container
docker ps | grep backend

# Copy the file into the container
docker cp frontend/assets/templates/modules.html <container_id>:/app/frontend/assets/templates/

# Or exec into container and create it
docker exec -it <container_id> bash
cat > /app/frontend/assets/templates/modules.html << 'EOF'
<div id="app-content"></div>

<script type="module">
  import { moduleManager } from '/assets/js/module-manager-enhanced.js';

  document.addEventListener('route:loaded', async (e) => {
    if (e.detail.route === 'modules') {
      await moduleManager.render();
    }
  });

  if (window.location.hash === '#modules') {
    moduleManager.render();
  }
</script>
EOF
exit
```

## Why This Happens

The backend serves static files from the `frontend` directory, but:
1. Static file serving is typically set up at startup
2. New files need the server to restart to be recognized
3. Some servers cache directory listings

## Quick Test

After restarting, test the route:

1. Open: `http://localhost:8000/app#modules`
2. Open browser console (F12)
3. You should see:
   - No JSON error
   - The module management page loading
   - Console logs about loading modules

## Still Getting 404?

Try these steps:

### 1. Verify File Exists
```bash
ls -la /home/user/app-buildify/frontend/assets/templates/modules.html
```

### 2. Check File Permissions
```bash
chmod 644 /home/user/app-buildify/frontend/assets/templates/modules.html
```

### 3. Check Backend Static File Mount

Look in `backend/app/main.py` for:
```python
from fastapi.staticfiles import StaticFiles

app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")
```

### 4. Clear Browser Cache
- Hard refresh: `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
- Or clear all cache in browser settings

### 5. Check Docker Volume Mounts

If using Docker, verify the volume is mounted correctly in `docker-compose.yml`:
```yaml
services:
  backend:
    volumes:
      - ./frontend:/app/frontend
```

## Expected Behavior After Fix

1. Navigate to `#modules`
2. See loading spinner briefly
3. See module management page with:
   - Header: "Module Management"
   - Two tabs: "Available Modules" and "Enabled Modules"
   - Search bar
   - Module cards (if modules are discovered)

## Next Steps

1. **Restart backend** (most important!)
2. Navigate to `#modules`
3. Run permission seeder if you want the menu item to show:
   ```bash
   python -m app.seeds.seed_module_management_rbac
   ```

---

**TL;DR**: Restart your backend server, then try `#modules` again!
