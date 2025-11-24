# Quick Start - NexaDB Dark Theme UI

## Launch the UI

```bash
cd /Users/krish/krishx/nexadb
python3 nexadb_admin_server.py
```

Then open: **http://localhost:9999**

## Features

### 🌙 Dark Theme (Default)
- Professional dark slate design
- Easy on the eyes for extended use
- Modern, sleek appearance
- VSCode-inspired code colors

### ☀️ Light Theme (Optional)
- Clean, bright interface
- Click the sun/moon icon in the top-right to switch
- Your preference is saved automatically

### 🎨 Theme Switcher
- **Location**: Top-right corner of header
- **Icon**: ☀️ (dark mode) / 🌙 (light mode)
- **Action**: Click to toggle themes
- **Persistence**: Theme choice is remembered

## UI Components (Both Themes)

All components adapt to the selected theme:
- ✅ Sidebar navigation
- ✅ Collection browser
- ✅ Document cards
- ✅ Modals and forms
- ✅ JSON syntax highlighting
- ✅ Toast notifications
- ✅ Connection status

## Color Palette

### Dark Theme
```
Backgrounds:  #0f172a, #1e293b, #334155
Text:         #f1f5f9, #cbd5e1, #94a3b8
Accents:      #6366f1 (primary), #8b5cf6 (secondary)
Success:      #10b981
Danger:       #ef4444
```

### Light Theme
```
Backgrounds:  #ffffff, #f8fafc, #f1f5f9
Text:         #0f172a, #334155, #64748b
Accents:      #6366f1 (primary), #8b5cf6 (secondary)
Success:      #10b981
Danger:       #ef4444
```

## Tips

1. **First Time**: Opens in dark theme automatically
2. **Switching**: Click theme button anytime - instant change
3. **Persistence**: Your choice is saved to browser localStorage
4. **Multiple Tabs**: Theme syncs when you reload
5. **No Server Required**: Theme switching works entirely client-side

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Create Collection | Click "+ New Collection" button |
| Insert Document | Click "Insert" button |
| Query Documents | Click "Query" button |
| Toggle Theme | Click sun/moon icon |

## What Changed?

**Before**: Light theme only
**After**: Dark theme by default + light theme option

All functionality remains the same - only the visual appearance changed!

## Troubleshooting

**Theme not switching?**
- Clear browser cache and reload
- Check JavaScript is enabled
- Try a different browser

**Theme not saving?**
- Check browser localStorage is enabled
- Not in incognito/private mode?

**Colors look wrong?**
- Hard refresh: Cmd+Shift+R (Mac) or Ctrl+F5 (Windows)
- Clear browser cache

---

**Enjoy your new professional dark theme! 🎨**
