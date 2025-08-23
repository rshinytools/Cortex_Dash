# API Client Migration Guide

## Security Update: Migrating from localStorage to Memory-Only Token Storage

### Overview
We've implemented a more secure authentication system that:
- Stores access tokens in memory only (prevents XSS attacks)
- Uses httpOnly cookies for refresh tokens (prevents JavaScript access)
- Implements automatic token refresh

### Migration Steps

#### 1. For API calls in React components:

**Old way (using apiClient):**
```typescript
import { apiClient } from '@/lib/api/client';

const fetchData = async () => {
  const response = await apiClient.get('/users');
  return response.data;
};
```

**New way (using secureApiClient):**
```typescript
import { secureApiClient } from '@/lib/api/secure-client';

const fetchData = async () => {
  const response = await secureApiClient.get('/users');
  return response.data;
};
```

#### 2. For API utility files:

Replace all imports:
```typescript
// Old
import { apiClient } from '@/lib/api/client';

// New
import { secureApiClient } from '@/lib/api/secure-client';
export const apiClient = secureApiClient; // Alias for backward compatibility
```

#### 3. For hooks that need the token:

**Old way:**
```typescript
const token = localStorage.getItem('auth_token');
```

**New way:**
```typescript
import { useAuth } from '@/lib/auth-context';

const { getAccessToken } = useAuth();
const token = await getAccessToken();
```

### Important Notes

1. **Gradual Migration**: The old `apiClient` will continue to work but is less secure. Migrate gradually by updating files as you work on them.

2. **CORS Configuration**: Ensure your backend allows credentials:
   ```typescript
   // Backend CORS setup
   allow_credentials=True
   ```

3. **Cookie Settings**: The backend now sets cookies with:
   - `httpOnly=True` (prevents JavaScript access)
   - `secure=True` (HTTPS only in production)
   - `sameSite=Strict` (CSRF protection)

4. **Token Refresh**: Tokens are automatically refreshed 5 minutes before expiry. No action needed in components.

### Testing the Migration

1. Clear browser storage:
   ```javascript
   localStorage.clear();
   sessionStorage.clear();
   ```

2. Login again to get the new httpOnly refresh token

3. Verify no tokens in localStorage:
   - Open DevTools > Application > Local Storage
   - Should be empty or no auth_token

4. Verify httpOnly cookie exists:
   - Open DevTools > Application > Cookies
   - Should see `refresh_token` with HttpOnly flag

### Rollback Plan

If issues occur, you can temporarily use both clients:
1. Keep using `apiClient` for existing code
2. Use `secureApiClient` for new code
3. Gradually migrate old code

### Common Issues

1. **401 Errors after migration**: Clear all storage and login again
2. **CORS errors**: Ensure `withCredentials: true` is set
3. **Token not found**: Check that auth context is properly initialized

### Benefits of This Migration

✅ **Prevents XSS attacks**: Tokens can't be stolen via JavaScript injection
✅ **Prevents CSRF**: SameSite cookie attribute blocks cross-site requests  
✅ **Automatic refresh**: No manual token management needed
✅ **Better security**: Follows OWASP best practices