# Source Tab Feature - GrapeJS Builder

## Overview

Added a **Source** tab to the GrapeJS builder that displays the generated HTML, CSS, and JavaScript code in real-time. This allows developers to see and copy the code being created by the visual builder.

## Features

### 📑 Two-Tab Interface

The right sidebar now has two tabs:

1. **Design Tab** (Default)
   - Layers panel
   - Settings/Traits panel
   - Styles panel

2. **Source Tab** (New)
   - HTML viewer
   - CSS viewer
   - JavaScript viewer

### 🔍 Source Code Display

#### HTML Section
- Auto-formatted with proper indentation
- Color-coded (green text on dark background)
- Shows complete page structure
- Copy to clipboard button

#### CSS Section
- Displays all generated styles
- Color-coded (blue text on dark background)
- Shows inline and external CSS
- Copy to clipboard button

#### JavaScript Section
- Extracts scripts from all components
- Recursively finds child component scripts
- Color-coded (yellow text on dark background)
- Shows API component logic
- Copy to clipboard button

### ⚡ Real-Time Updates

- **Auto-refresh**: Updates automatically when you modify components (500ms debounce)
- **Manual refresh**: Click "Refresh Source" button anytime
- **Smart updates**: Only refreshes when Source tab is active (performance optimization)

### 📋 Copy Functionality

Each code section has a "Copy" button:
- One-click copy to clipboard
- Toast notification on success
- Works for HTML, CSS, and JS separately

## How to Use

### 1. Access the Source Tab

1. Open the UI Builder (`/#builder`)
2. Click the **"Source"** tab in the right sidebar
3. View the generated code

### 2. View Code

The source tab shows three sections:

```
┌─────────────────────────┐
│  [Design]  [Source*]    │ ← Tab navigation
├─────────────────────────┤
│  📄 HTML                │
│  [Copy]                 │
│  <section>...</section> │
├─────────────────────────┤
│  🎨 CSS                 │
│  [Copy]                 │
│  .class { ... }         │
├─────────────────────────┤
│  ⚡ JavaScript          │
│  [Copy]                 │
│  function() { ... }     │
├─────────────────────────┤
│  [Refresh Source]       │
└─────────────────────────┘
```

### 3. Copy Code

- Click **Copy** button next to any section (HTML/CSS/JS)
- Code is copied to clipboard
- Success message appears
- Paste anywhere you need it

### 4. Refresh Code

- Code updates automatically as you edit
- Click **"Refresh Source"** to manually update
- Useful after adding multiple components at once

## Code Examples

### What You'll See

#### HTML Output
```html
<section id="iojr" class="py-12 px-4" data-component="flex-section">
  <div class="max-w-7xl mx-auto">
    <h1 class="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-8 text-center">
      API Integration Demo
    </h1>
    <div data-component="api-datatable" data-api-entity="companies"></div>
  </div>
</section>
```

#### CSS Output
```css
#iojr {
  padding: 20px 10px 10px 10px;
  background-color: rgb(248, 249, 250);
}

.api-datatable-container {
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
```

#### JavaScript Output
```javascript
// Component Scripts

function() {
    const container = this;
    const endpoint = container.getAttribute('data-api-endpoint');

    async function loadData() {
        const response = await fetch(endpoint);
        // ... API logic
    }

    loadData();
}

// ---

function() {
    const button = this;
    button.addEventListener('click', async () => {
        // ... Button logic
    });
}
```

## Use Cases

### 1. **Learning & Education**
- See how visual components translate to code
- Understand HTML structure
- Learn CSS styling patterns
- Study JavaScript implementations

### 2. **Code Export**
- Copy generated HTML for external use
- Extract CSS for custom stylesheets
- Get JavaScript for standalone pages
- Export complete page source

### 3. **Debugging**
- Inspect actual HTML structure
- Check CSS specificity
- Verify component scripts
- Troubleshoot rendering issues

### 4. **Documentation**
- Copy code examples
- Share component implementations
- Create code snippets
- Document page structures

### 5. **External Integration**
- Export to static site generators
- Integrate with CMS systems
- Use in email templates
- Embed in other applications

## Technical Details

### HTML Formatting

The HTML formatter:
- Adds proper indentation (2 spaces per level)
- Handles nested elements correctly
- Preserves self-closing tags
- Maintains attributes

### CSS Extraction

The CSS extractor:
- Gets all styles from GrapeJS editor
- Includes inline styles
- Shows component-specific CSS
- Combines all stylesheets

### JavaScript Extraction

The JS extractor:
- Recursively searches all components
- Finds component `script` properties
- Extracts function code
- Separates multiple scripts

### Performance

- **Debounced updates**: 500ms delay prevents excessive refreshes
- **Conditional refresh**: Only updates when Source tab is active
- **Lazy formatting**: Formats code only when viewing
- **Efficient clipboard**: Uses native Clipboard API

## Keyboard Shortcuts

While no specific shortcuts exist yet, you can:
- Use browser's **Ctrl+F** to search within code blocks
- **Ctrl+A** to select all text in a code block
- **Ctrl+C** after selecting to copy manually

## Browser Compatibility

### Copy to Clipboard
- ✅ Chrome/Edge 63+
- ✅ Firefox 53+
- ✅ Safari 13.1+
- ⚠️ Requires HTTPS or localhost

### Tab Functionality
- ✅ All modern browsers
- ✅ Mobile responsive
- ✅ Dark mode support

## Troubleshooting

### Source tab shows "No HTML yet"
- Make sure you've added components to the canvas
- Try clicking "Refresh Source"
- Check that GrapeJS editor is initialized

### Copy button doesn't work
- Ensure you're on HTTPS or localhost
- Check browser clipboard permissions
- Try manually selecting and copying text

### JavaScript shows empty
- Not all components have scripts
- API components will show JavaScript
- Basic UI components may not have scripts

### Code not updating
- Click "Refresh Source" manually
- Check if you're on the Source tab
- Try switching tabs and back

## Future Enhancements

Potential future features:
- Syntax highlighting (using Prism.js or similar)
- Code editing capability
- Download source files (.html, .css, .js)
- Full page export with dependencies
- Minified/compressed versions
- Code search/find functionality

## Summary

The Source tab provides:
- ✅ Real-time code visibility
- ✅ HTML, CSS, and JS viewing
- ✅ Copy to clipboard functionality
- ✅ Auto-refresh on changes
- ✅ Formatted, readable code
- ✅ Component script extraction
- ✅ Dark mode code display
- ✅ Manual refresh option

**Perfect for developers who want to see the code behind their visual designs!** 🚀

---

## Files Modified

- `frontend/assets/js/pages/builder.js`
  - Added tab navigation UI
  - Added source code display sections
  - Implemented tab switching logic
  - Added HTML formatting function
  - Added CSS extraction
  - Added JS extraction from components
  - Added copy to clipboard functionality
  - Added auto-refresh on component updates
