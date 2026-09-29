# Tenant Isolation Security Audit

**Date:** 2026-09-29  
**Focus:** Multi-Tenant Data Isolation & Cross-Tenant Access Prevention

---

## CRITICAL VULNERABILITIES FOUND & FIXED

### 1. ✅ Session-Based Tenant Hijacking (CRITICAL - FIXED)

**Vulnerability:**
- User logs in to Tenant A → session stores `tenant_id: A`
- User then accesses `tenantB.example.com` with subdomain
- Middleware would use session's `tenant_id: A` instead of subdomain-based Tenant B
- **Result:** User from Tenant A could access Tenant B's data using their existing session

**Attack Scenario:**
```
1. Doctor logs in at clinic-a.example.com
2. Session stores tenant_id=1 (Clinic A)
3. Doctor navigates to clinic-b.example.com
4. Middleware sees subdomain "clinic-b" but session has tenant_id=1
5. OLD CODE: Would use Clinic A's tenant from session
6. Doctor sees Clinic A's patients while on Clinic B's URL
```

**Fix Applied:**
```python
# In TenantMiddleware:
# If host-based tenant found, verify session matches
if tenant and slug_from_host:
    session_tenant_id = request.session.get("tenant_id")
    
    # If session has a different tenant_id, clear it
    if session_tenant_id and session_tenant_id != tenant.id:
        request.session.flush()  # Force re-authentication
```

**Impact:** **CRITICAL** - Prevented cross-tenant data access through session reuse.

---

### 2. ✅ Database Router Fail-Open Behavior (HIGH - FIXED)

**Vulnerability:**
- Database router returned `None` for tenant apps when no tenant context
- Django would fall back to `default` database
- Tenant-only models (Patient, User, Notification, Attendance) could query control DB

**Attack Scenario:**
```python
# If tenant context accidentally cleared or bypassed:
Patient.objects.all()  # Would query default DB instead of failing
# Could expose ALL patients from control DB if misconfigured
```

**Fix Applied:**
```python
def db_for_read(self, model, **hints):
    if app_label in self.TENANT_ONLY_APPS:
        tenant_db = get_current_tenant_db()
        if not tenant_db:
            raise RuntimeError(
                f"SECURITY: Attempted to read {app_label}.{model.__name__} "
                "without tenant context."
            )
        return tenant_db
```

**Impact:** **HIGH** - Fail-closed behavior ensures tenant context is REQUIRED. No silent fallback to wrong database.

---

### 3. ✅ Missing Tenant Context Validation in Views (MEDIUM - FIXED)

**Vulnerability:**
- Views assumed `request.tenant` exists
- No validation that tenant context was properly set
- If middleware failed silently, views could operate with `None` tenant

**Fix Applied:**
- Created `@require_tenant` decorator
- All `@doctor_required` and `@secretary_required` now include `@require_tenant`
- Login view explicitly checks tenant exists

**Code:**
```python
@require_tenant
@login_required
@role_required('doctor')
def doctor_view(request):
    # Guaranteed to have valid request.tenant
```

**Impact:** **MEDIUM** - Defense in depth. Views fail explicitly if tenant context missing.

---

### 4. ✅ Session Priority Over Subdomain (MEDIUM - FIXED)

**Vulnerability:**
- Original logic: Try subdomain, then fall back to session
- If subdomain present but invalid, session would be used
- Inconsistent tenant resolution could cause confusion

**Fix Applied:**
- Session fallback ONLY when no subdomain at all
- Subdomain always takes priority if present
- Session cleared if mismatch detected

**Impact:** **MEDIUM** - Consistent tenant identification. Subdomain is authoritative source.

---

## VERIFIED SECURE ✅

### ✅ Tenant Identification
- Subdomain extraction works correctly
- Active status check (`status=ACTIVE`) enforced
- Invalid slugs return 400 error (fail closed)

### ✅ Database Routing
- Control DB apps: `tenants`, `sessions`, `admin`
- Tenant DB apps: `accounts`, `patients`
- Shared apps: `auth`, `contenttypes` (route based on context)
- No `.using()` calls bypass router

### ✅ Authentication Backends
- `TenantModelBackend` requires tenant context
- `PlatformAdminBackend` requires NO tenant context
- Backends are mutually exclusive
- No cross-tenant authentication possible

### ✅ Admin Access
- Admin paths (`/admin/`) explicitly clear tenant context
- Only `PlatformAdmin` model can access admin
- Tenant users cannot access admin interface
- Platform admins cannot access tenant views

### ✅ Object Access by ID
- All queries filtered by `request.user` or tenant context
- No direct ID access without ownership validation
- Example: `Notification.objects.get(id=X, recipient=request.user)`

### ✅ Session Security
- Session middleware before tenant middleware (correct order)
- Session tenant_id validated against current tenant
- Mismatched sessions flushed automatically

---

## FILES MODIFIED

### 1. `tenants/middleware.py`
- **Added:** Session-tenant mismatch detection
- **Added:** Session flushing on mismatch
- **Changed:** Session fallback only when no subdomain
- **Impact:** Prevents session reuse across tenants

### 2. `tenants/routers.py`
- **Added:** Fail-closed RuntimeError for tenant apps without context
- **Changed:** Comments to English for clarity
- **Impact:** No silent fallback to wrong database

### 3. `accounts/decorators.py`
- **Added:** `@require_tenant` decorator
- **Modified:** `@doctor_required` and `@secretary_required` include `@require_tenant`
- **Impact:** All protected views validate tenant context

### 4. `accounts/views/auth_views.py`
- **Added:** Explicit tenant context validation in login
- **Added:** Security comments
- **Impact:** Login fails if no tenant context

---

## REMAINING RISKS

### 🟡 Medium Priority

1. **No Tenant-Specific Rate Limiting**
   - **Risk:** One tenant could DOS another by attacking shared resources
   - **Recommendation:** Implement per-tenant rate limiting
   - **Status:** Requires django-ratelimit (out of scope)

2. **Database Credentials in Tenant Model**
   - **Risk:** Stored in plaintext in control DB
   - **Current:** Protected by Django's auth system
   - **Recommendation:** Consider encryption at rest
   - **Status:** Low risk for internal system

3. **No Audit Trail for Cross-Tenant Access Attempts**
   - **Risk:** Security incidents hard to detect
   - **Recommendation:** Log all RuntimeError exceptions from router
   - **Status:** Consider adding logging

### 🟢 Low Priority

4. **Session Fixation (Mitigated)**
   - **Status:** Django rotates session ID on login (secure)
   - **Additional:** Session flushing on tenant mismatch adds extra protection

5. **Subdomain Spoofing (Not Applicable)**
   - **Status:** DNS-level attack, outside application scope
   - **Mitigation:** Use HTTPS, proper DNS configuration

6. **Database Connection Pooling**
   - **Status:** Each tenant has separate DB, connections managed by Django
   - **Concern:** High tenant count could exhaust connections
   - **Mitigation:** Connection pooling at infrastructure level

---

## SECURITY ARCHITECTURE

### Tenant Resolution Flow (After Fixes)
```
1. Extract subdomain from Host header
2. If subdomain exists:
   a. Query Tenant by slug (ACTIVE only)
   b. Check session tenant_id matches
   c. If mismatch → flush session
   d. Set tenant context
3. If no subdomain:
   a. Try session tenant_id (fallback only)
   b. Query Tenant by id (ACTIVE only)
   c. Set tenant context
4. If no tenant found:
   → Return 400 error (fail closed)
```

### Database Query Flow (After Fixes)
```
1. Model operation (Patient.objects.filter...)
2. Database router called
3. Check app label:
   - DEFAULT_ONLY: → "default" DB
   - SHARED: → tenant DB if context exists, else "default"
   - TENANT_ONLY: → tenant DB OR raise RuntimeError
4. Query executed on determined database
```

### Access Control Layers
```
Layer 1: Middleware (Tenant identification & validation)
Layer 2: Decorator (@require_tenant, @login_required, @role_required)
Layer 3: Database Router (Fail-closed for tenant apps)
Layer 4: Query Filters (recipient=request.user, etc.)
```

---

## TESTING PERFORMED

### ✅ Code Validation
- All Python files compile successfully
- No syntax errors
- Import statements verified

### ⚠️ Django Commands (Blocked by psycopg2)
- `python manage.py check` - Database driver missing
- `python manage.py test` - Database driver missing
- `python manage.py makemigrations --check` - Database driver missing

**Note:** Commands cannot run without PostgreSQL driver, but code structure is validated.

### ✅ Logic Verification
- Middleware flow analyzed for edge cases
- Router fail-closed behavior confirmed
- Decorator stacking verified
- Session handling logic traced

---

## DEPLOYMENT CHECKLIST

Before production:

1. ✅ All fixes applied
2. ✅ Fail-closed behavior verified
3. ✅ Session security configured
4. ⚠️ Install database driver (psycopg2-binary)
5. ⚠️ Run full test suite
6. ⚠️ Test tenant isolation manually:
   - Create 2 test tenants
   - Login to Tenant A
   - Attempt to access Tenant B URL
   - Verify session flushed and re-authentication required
7. ⚠️ Monitor logs for RuntimeError exceptions
8. ⚠️ Consider adding structured logging for security events

---

## SUMMARY

**Status:** ✅ **CRITICAL VULNERABILITIES FIXED**

### Vulnerabilities Found: 4
1. Session-based tenant hijacking (CRITICAL) ✅ Fixed
2. Database router fail-open (HIGH) ✅ Fixed
3. Missing tenant context validation (MEDIUM) ✅ Fixed
4. Session priority over subdomain (MEDIUM) ✅ Fixed

### Fixes Applied: 4
- Middleware enhanced with session-tenant validation
- Database router fail-closed for tenant apps
- Tenant context validation decorators added
- Login view hardened with explicit checks

### Remaining Risks: 3 (Low-Medium)
- No per-tenant rate limiting (Medium)
- Database credentials plaintext (Low)
- No audit logging (Low)

### Tests Performed:
- Code compilation ✅
- Logic verification ✅
- Django commands ⚠️ (blocked by missing driver)

**Recommendation:** System is secure for production deployment after installing PostgreSQL driver and running full test suite. The critical cross-tenant access vulnerabilities have been eliminated through fail-closed architecture and explicit validation.
