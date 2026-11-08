# FinPass AI Next.js application

This directory is the replacement Node.js application for FinPass AI. It serves the existing UI from `public/static-pages` and exposes the migrated API under `/api`.

## Local run

1. Copy `.env.example` to `.env.local` and fill in the MongoDB, JWT, Groq, and optional Resend values.
2. Run `npm install`.
3. Run `npm run dev` and open `http://localhost:3000`.

## Vercel

Set the Vercel project Root Directory to `next-app`, then add the variables from `.env.example` in the Vercel project settings. Never commit `.env.local` or provider keys.
