# ArchonHub — Brand Assets

Drop your final branded images into the folders below and push to GitHub.
Each placeholder file shows the **exact filename, size, and format** required.

---

## 📁 Folder Structure

```
assets/branding/
├── web/
│   ├── logo.svg              ← Sidebar logo (any height, ~180px wide)
│   ├── logo-dark.png         ← 400×120 px, transparent background, dark theme
│   ├── favicon.ico           ← 32×32 px, browser tab icon
│   ├── favicon-192.png       ← 192×192 px, PWA icon (Android home screen)
│   └── favicon-512.png       ← 512×512 px, PWA splash icon
│
├── desktop/
│   ├── app-icon.ico          ← 256×256 px, Windows taskbar & titlebar icon
│   └── splash.png            ← 800×500 px, optional loading splash
│
├── ios/
│   ├── AppIcon.appiconset/   ← iOS app icons (see Contents.json for all sizes)
│   │   ├── Contents.json
│   │   ├── icon-20.png       ← 20×20
│   │   ├── icon-20@2x.png    ← 40×40
│   │   ├── icon-20@3x.png    ← 60×60
│   │   ├── icon-29.png       ← 29×29
│   │   ├── icon-29@2x.png    ← 58×58
│   │   ├── icon-29@3x.png    ← 87×87
│   │   ├── icon-40.png       ← 40×40
│   │   ├── icon-40@2x.png    ← 80×80
│   │   ├── icon-40@3x.png    ← 120×120
│   │   ├── icon-60@2x.png    ← 120×120
│   │   ├── icon-60@3x.png    ← 180×180
│   │   ├── icon-76.png       ← 76×76  (iPad)
│   │   ├── icon-76@2x.png    ← 152×152 (iPad)
│   │   ├── icon-83.5@2x.png  ← 167×167 (iPad Pro)
│   │   └── icon-1024.png     ← 1024×1024 (App Store)
│   └── launch-screen.png     ← 1290×2796 px, iPhone 14 Pro Max launch image
│
└── watch/
    ├── AppIcon.appiconset/   ← Watch app icons (see Contents.json)
    │   ├── Contents.json
    │   ├── icon-44.png       ← 44×44 (Watch 40mm)
    │   ├── icon-50.png       ← 50×50 (Watch 44mm)
    │   └── icon-1024.png     ← 1024×1024 (App Store)
    └── complication-logo.png ← 50×50 px, white on transparent, Watch face
```

---

## 🎨 Brand Guidelines

| Element        | Value                        |
|----------------|------------------------------|
| Primary color  | `#6366f1` (Indigo)           |
| Background     | `#0f1117` (Near-black)       |
| Card bg        | `#1a1d27`                    |
| Text primary   | `#f8fafc` (Near-white)       |
| Accent light   | `#818cf8`                    |
| Brand mark     | `⬡` hexagon glyph OR custom  |
| Font (UI)      | System UI / SF Pro           |
| Font (brand)   | Your choice — bold sans-serif|

---

## 🔄 How to Apply After Uploading

### Web dashboard
After replacing `web/logo.svg` and `web/favicon.ico`, the dashboard
references them automatically from `/assets/branding/web/`.

### iOS app
Copy the `ios/AppIcon.appiconset/` folder contents into:
`ios/AgentHarnessIOS/Assets.xcassets/AppIcon.appiconset/`
Then clean build in Xcode (`Cmd+Shift+K` → `Cmd+B`).

### Desktop app
The Tkinter app will load `assets/branding/desktop/app-icon.ico`
automatically from the repo root on startup (path already wired in).

### Watch app
Copy `watch/AppIcon.appiconset/` into:
`ios/AgentHarnessWatch WatchKit App/Assets.xcassets/AppIcon.appiconset/`

---

## ✏️ Placeholder files

Each `PLACEHOLDER_*.txt` file in the subfolders shows what image to replace it with.
Delete the `.txt` placeholder and drop in your final `.png`/`.svg`/`.ico` file
with the **exact same base filename**.
