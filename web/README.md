# CovenantAI - Web Interface

This directory contains the Next.js application for the CovenantAI platform, a Regulatory Intelligence Platform designed for enterprise compliance.

## 🚀 Project Overview

CovenantAI bridges compliance frameworks to operational action, turning static regulatory noise into dynamic, auditable action.

### Tech Stack

- **Framework:** [Next.js 15+](https://nextjs.org/) (App Router)
- **Styling:** [Tailwind CSS](https://tailwindcss.com/) (v4)
- **Icons:** [Lucide React](https://lucide.dev/)
- **Animations:** [React Type Animation](https://www.npmjs.com/package/react-type-animation)
- **Language:** TypeScript

## 🛠️ Setup & Installation

1.  **Navigate to the web directory:**
    ```bash
    cd web
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Run the development server:**
    ```bash
    npm run dev
    ```

    Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## 📂 Project Structure

```
web/
├── src/
│   ├── app/
│   │   ├── globals.css      # Global styles (Dark/Terminal theme)
│   │   ├── layout.tsx       # Root layout with metadata
│   │   └── page.tsx         # Main landing page
│   └── components/
│       ├── ArchitectureCard.tsx  # Reusable card for architecture section
│       ├── CTAForm.tsx           # Email submission form
│       └── Terminal.tsx          # Hero section terminal with typewriter effect
├── public/                  # Static assets
├── next.config.ts           # Next.js configuration
├── tailwind.config.ts       # Tailwind configuration
└── tsconfig.json            # TypeScript configuration
```

## 🎨 Design System

The project follows a "System Interface" / "Developer Mode" aesthetic:
- **Colors:** Dark background (`#050505`), Neon Green (`#22c55e`) accents, White text.
- **Typography:** Monospace fonts (Geist Mono) for a technical feel.
- **Components:**
    - **Terminal:** Simulates a system boot sequence.
    - **Architecture Cards:** Grid layout with hover effects.
    - **Status Indicators:** Visual cues for system health (ONLINE, PASSED, SECURE).

## 📦 Build for Production

To create an optimized production build:

```bash
npm run build
```

To start the production server:

```bash
npm start
```
