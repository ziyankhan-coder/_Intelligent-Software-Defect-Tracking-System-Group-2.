# BugFlow — Frontend (React.js + Tailwind CSS)

**Owner:** Ramya (Frontend Lead)

## Week 1 Setup Instructions
1. Initialize React app inside this directory:
   ```bash
   npm create vite@latest . -- --template react
   npm install
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   npm install axios react-router-dom lucide-react
   ```
2. Configure Axios base URL to point to backend:
   ```javascript
   // src/api/axios.js
   import axios from 'axios';

   const api = axios.create({
     baseURL: 'http://127.0.0.1:8000/api/v1',
   });

   api.interceptors.request.use((config) => {
     const token = localStorage.getItem('access_token');
     if (token) {
       config.headers.Authorization = `Bearer ${token}`;
     }
     return config;
   });

   export default api;
   ```
3. Run dev server:
   ```bash
   npm run dev
   ```
