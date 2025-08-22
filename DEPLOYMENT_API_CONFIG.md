# API Configuration for Different Deployment Environments

## Overview
The application now uses a dynamic API configuration that automatically adapts to different deployment environments without hardcoding URLs.

## How It Works

The API configuration (`frontend/src/lib/api-config.ts`) determines the backend URL in this priority:

1. **Environment Variable** (`NEXT_PUBLIC_API_URL`) - Highest priority
2. **Automatic Detection** - Based on current window location
3. **Default Fallback** - For development environments

## Configuration for Different Environments

### 1. Local Development (Docker Compose)
```yaml
# docker-compose.local-dev.yml
environment:
  - NEXT_PUBLIC_API_URL=http://localhost:8000
```
✅ Already configured - no changes needed

### 2. VM Deployment (Single Server)
```bash
# In your VM, set the environment variable
export NEXT_PUBLIC_API_URL=http://YOUR_VM_IP:8000

# Or in .env.production
NEXT_PUBLIC_API_URL=http://192.168.1.100:8000
```

### 3. Production with Domain Name
```bash
# .env.production
NEXT_PUBLIC_API_URL=https://api.yourdomain.com

# Or if backend is on same domain, different port
NEXT_PUBLIC_API_URL=https://yourdomain.com:8000
```

### 4. Kubernetes / Cloud Deployment
```yaml
# In your deployment.yaml
env:
  - name: NEXT_PUBLIC_API_URL
    value: "https://api.your-cluster.com"
```

### 5. Reverse Proxy (Nginx/Apache)
```bash
# If backend is behind /api path
NEXT_PUBLIC_API_URL=https://yourdomain.com/api

# Nginx config example:
location /api {
    proxy_pass http://backend:8000;
}
```

## Testing Your Configuration

After deployment, verify the API configuration:

1. Open browser console
2. Run: `localStorage.getItem('token')` (ensure you're logged in)
3. Check network tab - API calls should go to correct backend URL
4. No more 404 errors on filter validation

## Benefits of This Approach

✅ **No Hardcoding** - Works in any environment  
✅ **Easy Migration** - Just update environment variable  
✅ **Docker Ready** - Auto-detects Docker environment  
✅ **Production Safe** - Supports HTTPS, custom domains  
✅ **Fallback Logic** - Smart defaults prevent breakage  

## Quick Setup for VM Deployment

```bash
# 1. SSH to your VM
ssh user@your-vm-ip

# 2. Clone the repository
git clone <your-repo>

# 3. Update environment variable
echo "NEXT_PUBLIC_API_URL=http://$(hostname -I | awk '{print $1}'):8000" >> frontend/.env.production

# 4. Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Issue: API calls still going to wrong URL
**Solution**: Clear browser cache and restart frontend container

### Issue: CORS errors
**Solution**: Ensure backend CORS settings include your frontend URL

### Issue: 404 on API calls
**Solution**: Verify NEXT_PUBLIC_API_URL matches your backend location

## Files Changed

1. **Created**: `frontend/src/lib/api-config.ts` - Dynamic API configuration
2. **Updated**: `frontend/src/components/filters/FilterBuilder.tsx` - Use api config
3. **Updated**: `frontend/.env.production` - Added configuration examples
4. **Updated**: `docker-compose.local-dev.yml` - Fixed environment variables

## Summary

The application now intelligently determines the backend API URL based on the deployment environment. No more hardcoded `localhost:8000` - it will work seamlessly whether you deploy to:
- Local Docker
- VM with IP address
- Cloud with domain name
- Kubernetes cluster
- Behind a reverse proxy

Just set `NEXT_PUBLIC_API_URL` in your environment, and the application handles the rest!