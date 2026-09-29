# Security Guidelines

## Environment Configuration

### Before Deployment to Production

1. **Generate a New SECRET_KEY**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Update `SECRET_KEY` in your `.env` file with the generated value.

2. **Set DEBUG to False**
   ```
   DEBUG=False
   ```

3. **Configure ALLOWED_HOSTS**
   ```
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```
   List all domains that will serve your application (comma-separated, no spaces).

4. **Use Strong Database Credentials**
   - Change the default `DB_PASSWORD` to a strong, unique password
   - Use a dedicated database user with minimal required privileges
   - Never use default passwords like "password" or "12345678"

5. **Secure Database Access**
   - If possible, use `127.0.0.1` for `DB_HOST` (localhost)
   - Restrict database access to application server IP only
   - Use SSL/TLS for database connections in production

## Environment Variables

The application uses the following environment variables (see `.env.example`):

- `SECRET_KEY` - Django secret key (REQUIRED)
- `DEBUG` - Debug mode flag (default: False)
- `ALLOWED_HOSTS` - Comma-separated list of allowed domains
- `DB_NAME` - PostgreSQL database name
- `DB_USER` - PostgreSQL username
- `DB_PASSWORD` - PostgreSQL password
- `DB_HOST` - PostgreSQL host
- `DB_PORT` - PostgreSQL port

## File Security

### Protected Files (Never Commit)
- `.env` - Contains all secrets and credentials
- `*.key` - Private keys
- `*.pem` - Certificate files
- `db.sqlite3` - Database file (development only)

### Safe to Commit
- `.env.example` - Template without actual secrets
- All Python source files (no hardcoded secrets)

## Security Checklist for Production

- [ ] New SECRET_KEY generated
- [ ] DEBUG=False
- [ ] ALLOWED_HOSTS configured
- [ ] Strong database password set
- [ ] .env file is NOT in git repository
- [ ] Database user has minimal privileges
- [ ] SSL/TLS enabled for database connections
- [ ] Application served over HTTPS
- [ ] Regular security updates applied

## Reporting Security Issues

If you discover a security vulnerability, please email the development team immediately. Do not open a public issue.
