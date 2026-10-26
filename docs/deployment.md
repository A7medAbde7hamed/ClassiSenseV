# Vercel deployment

Project: `classisense-v`. Repository: `A7medAbde7hamed/ClassiSenseV`.

- Framework preset: Other / null
- Node: 24.x
- Build command: `npm run build`
- Static output: `public`
- API: `api/monitoring.js`, `api/session.js`
- Server-only Secrets: `FIREBASE_SERVICE_ACCOUNT_JSON`, `DASHBOARD_PASSWORD`

With no Secrets configured, the deployment deliberately shows setup mode. `?demo=1` opens a clearly labelled sample workspace. It does not write to Firebase or control physical devices.

The CV process, SQLite outbox and Arduino firmware must run locally; Vercel does not host video capture, serial devices, or the persistent outbox worker.

After environment changes, redeploy and sign in from Connection settings. Use a dedicated test database. Verify `/api/monitoring` without a session returns 401 once configured, and that live values become stale after the local tracker stops. Never place the service-account key under `public/` or in any client-visible environment variable.

PWA: verify HTTPS, standalone manifest, PNG/maskable icons, active service worker, and offline navigation after the first successful visit. Installing the app does not provide background gas detection or push notifications on the phone.
