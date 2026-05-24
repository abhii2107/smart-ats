# Smart ATS Deployment

Recommended setup:

- Backend: Render web service
- Frontend: Vercel static Vite app

## 1. Deploy Backend On Render

1. Push this repository to GitHub.
2. Go to Render and create a new Blueprint from the repository.
3. Render will read `render.yaml`.
4. Add environment variables:

```text
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
```

5. Deploy the service.
6. After deployment, copy the backend URL. It will look like:

```text
https://smart-ats-backend.onrender.com
```

Health check:

```text
https://smart-ats-backend.onrender.com/api/
```

## 2. Deploy Frontend On Vercel

1. Import the same GitHub repository in Vercel.
2. Set the root directory to:

```text
frontend
```

3. Add this environment variable:

```text
VITE_API_BASE_URL=https://smart-ats-backend.onrender.com/api
```

4. Build command:

```text
npm run build
```

5. Output directory:

```text
dist
```

6. Deploy.

## 3. Update Backend CORS

After Vercel gives you the frontend URL, update Render environment variable:

```text
ALLOWED_ORIGINS=https://your-real-vercel-url.vercel.app
```

Then redeploy/restart the Render backend.

## Local Development

Backend:

```powershell
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm run dev -- --host=127.0.0.1 --port=5173
```

