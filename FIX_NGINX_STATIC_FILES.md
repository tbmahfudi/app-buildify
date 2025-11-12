# Fix: Nginx Static File 404 Handling

## Problem

When the application tried to load a missing JavaScript file (e.g., `/assets/js/settings-security.js`), nginx was serving the root `index.html` file instead of returning a 404 error. This caused JavaScript syntax errors because the browser tried to parse HTML as JavaScript.

### Error Message
```
settings-security.js:1 Uncaught SyntaxError: Unexpected token '<' (at settings-security.js:1:1)
✓ Script loaded: /assets/js/settings-security.js
```

The `<` character is the first character of `<!DOCTYPE html>` from the index.html file.

## Root Cause

The nginx configuration at `infra/nginx/app.conf` had:

```nginx
location / {
  root /usr/share/nginx/html;
  try_files $uri /index.html;
}
```

This configuration is correct for SPA (Single Page Application) routing, where non-existent routes should fall back to `index.html`. However, it also applied to static assets like JavaScript and CSS files, causing them to return HTML instead of a 404 error.

## Solution

Updated the nginx configuration to differentiate between:
1. **Static assets** (js, css, images, etc.): Return 404 if not found
2. **Routes** (everything else): Fall back to index.html for client-side routing

### Changes Made

Modified `infra/nginx/app.conf` to add a specific location block for static assets:

```nginx
# For static assets, serve only if they exist, otherwise return 404
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|webp|json|xml|txt|pdf|map)$ {
  root /usr/share/nginx/html;
  try_files $uri =404;

  # Cache static assets for better performance
  expires 1d;
  add_header Cache-Control "public, immutable";
}

# For all other requests (routes), fall back to index.html for SPA routing
location / {
  root /usr/share/nginx/html;
  try_files $uri /index.html;
}
```

## Benefits

1. **Proper Error Handling**: Missing static files now return 404 instead of HTML
2. **Better Debugging**: JavaScript errors will show real 404 errors instead of syntax errors
3. **Improved Caching**: Static assets are now cached for 1 day, improving performance
4. **Clearer Console**: Resource loader will correctly identify missing files

## Testing

After deploying this change, you need to:

1. **Restart the frontend container**:
   ```bash
   docker-compose -f infra/docker-compose.dev.yml restart frontend
   ```

2. **Verify the fix**:
   - Open browser DevTools (F12)
   - Navigate to the application
   - Check the Console and Network tabs
   - Missing JS/CSS files should now show "404 Not Found" instead of "SyntaxError"

3. **Test SPA routing**:
   - Ensure normal routes like `/dashboard`, `/users`, etc. still work
   - These should still fall back to index.html correctly

## Notes

- This fix applies to both development and production environments (they use the same nginx config)
- The route-specific JavaScript loading in `app.js:918` is optional, so missing files won't break the application
- The resource loader already has error handling for 404s (see `resource-loader.js:74` and `resource-loader.js:121`)

## Files Modified

- `infra/nginx/app.conf` - Updated nginx configuration with static file handling
