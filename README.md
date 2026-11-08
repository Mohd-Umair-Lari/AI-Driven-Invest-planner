# Finpass-AI

Finpass-AI is a production Next.js application for AI-assisted financial planning and investment guidance for Indian investors.

## Production architecture

- **Application:** Next.js App Router and Node.js route handlers
- **UI:** Preserved Finpass-AI client experience under `next-app/public`
- **Database:** MongoDB Atlas
- **AI:** Groq API
- **Email:** Resend, used for password recovery
- **Authentication:** JWT access and refresh tokens, password hashing, GitHub OAuth, and Google OAuth
- **Deployment:** Vercel

## Repository structure

```text
Finpass-AI/
├── next-app/
│   ├── app/                 # Next.js pages and API route handlers
│   ├── lib/                 # Auth, MongoDB, AI, OAuth, and security modules
│   ├── public/              # Finpass-AI UI assets and client scripts
│   ├── .env.example         # Safe deployment configuration template
│   ├── package.json
│   └── next.config.ts
└── README.md
```

## Deploy to Vercel

Create a Vercel project from this repository and configure:

```text
Root Directory: next-app
Framework Preset: Next.js
Install Command: npm install
Build Command: npm run build
Output Directory: leave empty or use the Next.js default
```

Add the variables listed in [`next-app/.env.example`](./next-app/.env.example) to the Vercel project. Keep API keys and database credentials private. `APP_URL` must be the public Vercel URL, and OAuth callback URLs must use that same domain.

## Verification

```text
/api/health
/api/test-connection
```

Run the production build from `next-app` with `npm run build` before releasing a change.

## Safety notice

Finpass-AI is an educational and informational tool. It does not execute trades, manage funds, or provide legally binding financial advice. Projections are illustrative; consult a SEBI-registered investment advisor before making significant financial decisions.
