from unittest.mock import patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.contrib import admin as django_admin
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.base import Message
from django.test import RequestFactory
from django.db import connections

from .models import Tenant
from .admin import TenantAdmin, TenantCreateForm
from .database import (
    database_exists,
    create_tenant_database,
    drop_tenant_database,
)
from .routers import (
    set_current_tenant_db,
    clear_current_tenant_db,
)


class TenantReadonlyFieldsTest(TestCase):
    """
    Test TASK 1: database_name and related fields become readonly after creation.
    """
    
    def setUp(self):
        self.site = AdminSite()
        self.admin = TenantAdmin(Tenant, self.site)
        self.factory = RequestFactory()
    
    def test_new_tenant_has_editable_database_fields(self):
        """New tenant (obj=None) should have editable database fields."""
        request = self.factory.get('/admin/tenants/tenant/add/')
        
        readonly_fields = self.admin.get_readonly_fields(request, obj=None)
        
        # Only created_at and updated_at should be readonly for new tenants
        self.assertNotIn('database_name', readonly_fields)
        self.assertNotIn('database_host', readonly_fields)
        self.assertNotIn('database_port', readonly_fields)
        self.assertNotIn('database_user', readonly_fields)
        self.assertIn('created_at', readonly_fields)
        self.assertIn('updated_at', readonly_fields)
    
    def test_existing_tenant_has_readonly_database_fields(self):
        """Existing tenant should have database connection fields readonly."""
        tenant = Tenant(
            id=1,
            clinic_name="Test Clinic",
            slug="test",
            database_name="clinic_test",
            database_host="127.0.0.1",
            database_port=5432,
            database_user="postgres",
            database_password="password",
        )
        
        request = self.factory.get(f'/admin/tenants/tenant/{tenant.id}/change/')
        
        readonly_fields = self.admin.get_readonly_fields(request, obj=tenant)
        
        # Database connection fields should be readonly
        self.assertIn('database_name', readonly_fields)
        self.assertIn('database_host', readonly_fields)
        self.assertIn('database_port', readonly_fields)
        self.assertIn('database_user', readonly_fields)
        
        # These should still be readonly
        self.assertIn('created_at', readonly_fields)
        self.assertIn('updated_at', readonly_fields)
    
    def test_editable_fields_remain_editable(self):
        """Non-database fields should remain editable after creation."""
        tenant = Tenant(
            id=1,
            clinic_name="Test Clinic",
            slug="test",
            database_name="clinic_test",
            database_host="127.0.0.1",
            database_port=5432,
            database_user="postgres",
            database_password="password",
        )
        
        request = self.factory.get(f'/admin/tenants/tenant/{tenant.id}/change/')
        readonly_fields = self.admin.get_readonly_fields(request, obj=tenant)
        
        # These should NOT be readonly
        self.assertNotIn('clinic_name', readonly_fields)
        self.assertNotIn('slug', readonly_fields)
        self.assertNotIn('database_password', readonly_fields)
        self.assertNotIn('status', readonly_fields)


class DatabaseExistenceCheckTest(TransactionTestCase):
    """
    Test TASK 2: Database existence checking and orphan cleanup.
    """
    
    @patch('tenants.database.psycopg.connect')
    def test_database_exists_returns_true_when_exists(self, mock_connect):
        """database_exists should return True when database exists."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn
        
        result = database_exists("clinic_test")
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once()
    
    @patch('tenants.database.psycopg.connect')
    def test_database_exists_returns_false_when_not_exists(self, mock_connect):
        """database_exists should return False when database does not exist."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn
        
        result = database_exists("clinic_nonexistent")
        
        self.assertFalse(result)
    
    @patch('tenants.database.database_exists')
    @patch('tenants.database.psycopg.connect')
    def test_create_tenant_database_fails_if_already_exists(self, mock_connect, mock_exists):
        """create_tenant_database should fail if database already exists."""
        mock_exists.return_value = True
        
        with self.assertRaises(ValueError) as context:
            create_tenant_database("clinic_existing")
        
        self.assertIn("موجودة بالفعل", str(context.exception))
        # Should not attempt to create
        mock_connect.assert_not_called()
    
    @patch('tenants.database.database_exists')
    @patch('tenants.database.psycopg.connect')
    def test_create_tenant_database_succeeds_when_not_exists(self, mock_connect, mock_exists):
        """create_tenant_database should succeed when database does not exist."""
        mock_exists.return_value = False
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn
        
        result = create_tenant_database("clinic_new")
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once()
        self.assertIn('CREATE DATABASE', mock_cursor.execute.call_args[0][0])


class TenantCreationCleanupTest(TransactionTestCase):
    """
    Test TASK 2: Orphan database cleanup on failed tenant creation.
    """
    
    def setUp(self):
        self.site = AdminSite()
        self.admin = TenantAdmin(Tenant, self.site)
        self.factory = RequestFactory()
    
    @patch('tenants.admin.connections')
    @patch('tenants.admin.drop_tenant_database')
    @patch('tenants.admin.create_tenant_database')
    @patch('tenants.admin.configure_tenant_database')
    @patch('tenants.admin.migrate_tenant_database')
    @patch('tenants.admin.messages')
    @patch('tenants.admin.Tenant.objects.using')
    def test_failed_migration_drops_newly_created_database(
        self, mock_using, mock_messages, mock_migrate, mock_configure, mock_create, mock_drop, mock_connections
    ):
        """If migration fails after DB creation, the new DB should be dropped."""
        # Simulate successful database creation
        mock_create.return_value = True
        
        # Simulate migration failure
        mock_migrate.side_effect = Exception("Migration failed")
        
        # Mock connections
        mock_connections.__getitem__.return_value.close = MagicMock()
        
        # Mock Tenant.objects.using().filter().delete()
        mock_using.return_value.filter.return_value.delete.return_value = None
        
        request = self.factory.post('/admin/tenants/tenant/add/')
        request.user = MagicMock()
        
        tenant = Tenant(
            id=999,  # Give it an ID so delete logic can work
            clinic_name="Test Clinic",
            slug="test",
            database_name="clinic_test",
            database_host="127.0.0.1",
            database_port=5432,
            database_user="postgres",
            database_password="password",
        )
        
        form = TenantCreateForm(data={
            'clinic_name': 'Test Clinic',
            'slug': 'test',
            'database_name': 'clinic_test',
            'database_host': '127.0.0.1',
            'database_port': 5432,
            'database_user': 'postgres',
            'database_password': 'password',
            'status': 'active',
            'doctor_username': 'doctor',
            'doctor_full_name': 'Doctor Test',
            'doctor_password': 'password123',
        })
        form.instance = tenant
        form.is_valid()  # Validate the form
        
        # Mock the super().save_model() call
        with patch.object(django_admin.ModelAdmin, 'save_model'):
            # Should raise IntegrityError
            with self.assertRaises(Exception):
                self.admin.save_model(request, tenant, form, change=False)
        
        # Verify database was dropped
        mock_drop.assert_called_once_with('clinic_test')
    
    @patch('tenants.admin.connections')
    @patch('tenants.admin.drop_tenant_database')
    @patch('tenants.admin.create_tenant_database')
    @patch('tenants.admin.configure_tenant_database')
    @patch('tenants.admin.messages')
    @patch('tenants.admin.Tenant.objects.using')
    def test_failed_connection_drops_newly_created_database(
        self, mock_using, mock_messages, mock_configure, mock_create, mock_drop, mock_connections
    ):
        """If connection fails after DB creation, the new DB should be dropped."""
        # Simulate successful database creation
        mock_create.return_value = True
        
        # Simulate connection failure
        mock_configure.side_effect = Exception("Connection failed")
        
        # Mock connections
        mock_connections.__getitem__.return_value.close = MagicMock()
        
        # Mock Tenant.objects.using().filter().delete()
        mock_using.return_value.filter.return_value.delete.return_value = None
        
        request = self.factory.post('/admin/tenants/tenant/add/')
        request.user = MagicMock()
        
        tenant = Tenant(
            id=999,  # Give it an ID so delete logic can work
            clinic_name="Test Clinic",
            slug="test",
            database_name="clinic_test",
            database_host="127.0.0.1",
            database_port=5432,
            database_user="postgres",
            database_password="password",
        )
        
        form = TenantCreateForm(data={
            'clinic_name': 'Test Clinic',
            'slug': 'test',
            'database_name': 'clinic_test',
            'database_host': '127.0.0.1',
            'database_port': 5432,
            'database_user': 'postgres',
            'database_password': 'password',
            'status': 'active',
            'doctor_username': 'doctor',
            'doctor_full_name': 'Doctor Test',
            'doctor_password': 'password123',
        })
        form.instance = tenant
        form.is_valid()  # Validate the form
        
        # Mock the super().save_model() call
        with patch.object(django_admin.ModelAdmin, 'save_model'):
            # Should raise IntegrityError
            with self.assertRaises(Exception):
                self.admin.save_model(request, tenant, form, change=False)
        
        # Verify database was dropped
        mock_drop.assert_called_once_with('clinic_test')
    
    @patch('tenants.admin.connections')
    @patch('tenants.admin.drop_tenant_database')
    @patch('tenants.admin.create_tenant_database')
    @patch('tenants.admin.messages')
    def test_existing_database_not_dropped_on_failure(self, mock_messages, mock_create, mock_drop, mock_connections):
        """If DB already existed, it should NOT be dropped on failure."""
        # Simulate database already exists (creation returns False or raises)
        mock_create.side_effect = ValueError("Database already exists")
        
        # Mock connections
        mock_connections.__getitem__.return_value.close = MagicMock()
        
        request = self.factory.post('/admin/tenants/tenant/add/')
        request.user = MagicMock()
        
        tenant = Tenant(
            clinic_name="Test Clinic",
            slug="test",
            database_name="clinic_existing",
            database_host="127.0.0.1",
            database_port=5432,
            database_user="postgres",
            database_password="password",
        )
        
        form = TenantCreateForm(data={
            'clinic_name': 'Test Clinic',
            'slug': 'test',
            'database_name': 'clinic_existing',
            'database_host': '127.0.0.1',
            'database_port': 5432,
            'database_user': 'postgres',
            'database_password': 'password',
            'status': 'active',
            'doctor_username': 'doctor',
            'doctor_full_name': 'Doctor Test',
            'doctor_password': 'password123',
        })
        form.instance = tenant
        
        # Should raise IntegrityError
        with self.assertRaises(Exception):
            self.admin.save_model(request, tenant, form, change=False)
        
        # Verify database was NOT dropped (since it wasn't created by this operation)
        mock_drop.assert_not_called()


class TenantDeletionTest(TestCase):
    """
    Test TASK 3: Safe tenant deletion without dropping PostgreSQL database.
    """
    
    def setUp(self):
        self.site = AdminSite()
        self.admin = TenantAdmin(Tenant, self.site)
        self.factory = RequestFactory()
    
    @patch('tenants.admin.drop_tenant_database')
    @patch('tenants.admin.messages')
    def test_delete_tenant_does_not_drop_database(self, mock_messages, mock_drop):
        """Deleting a tenant should NOT drop the PostgreSQL database."""
        tenant = Tenant.objects.create(
            clinic_name="Test Clinic",
            slug="test",
            database_name="clinic_test",
            database_host="127.0.0.1",
            database_port=5432,
            database_user="postgres",
            database_password="password",
        )
        
        request = self.factory.post(f'/admin/tenants/tenant/{tenant.id}/delete/')
        request.user = MagicMock()
        
        # Delete the tenant
        self.admin.delete_model(request, tenant)
        
        # Verify tenant was deleted from database
        self.assertFalse(Tenant.objects.filter(id=tenant.id).exists())
        
        # Verify PostgreSQL database was NOT dropped
        mock_drop.assert_not_called()
        
        # Verify warning message was called
        mock_messages.warning.assert_called_once()
    
    @patch('tenants.admin.drop_tenant_database')
    @patch('tenants.admin.messages')
    def test_bulk_delete_tenants_does_not_drop_databases(self, mock_messages, mock_drop):
        """Bulk deleting tenants should NOT drop PostgreSQL databases."""
        tenant1 = Tenant.objects.create(
            clinic_name="Clinic 1",
            slug="clinic1",
            database_name="clinic_test1",
            database_host="127.0.0.1",
            database_port=5432,
            database_user="postgres",
            database_password="password",
        )
        tenant2 = Tenant.objects.create(
            clinic_name="Clinic 2",
            slug="clinic2",
            database_name="clinic_test2",
            database_host="127.0.0.1",
            database_port=5432,
            database_user="postgres",
            database_password="password",
        )
        
        request = self.factory.post('/admin/tenants/tenant/')
        request.user = MagicMock()
        
        queryset = Tenant.objects.filter(id__in=[tenant1.id, tenant2.id])
        
        # Bulk delete
        self.admin.delete_queryset(request, queryset)
        
        # Verify tenants were deleted
        self.assertFalse(Tenant.objects.filter(id=tenant1.id).exists())
        self.assertFalse(Tenant.objects.filter(id=tenant2.id).exists())
        
        # Verify PostgreSQL databases were NOT dropped
        mock_drop.assert_not_called()
        
        # Verify warning message was called
        mock_messages.warning.assert_called_once()
    
    def test_delete_shows_warning_message(self):
        """Deleting a tenant should show a warning about manual database cleanup."""
        tenant = Tenant.objects.create(
            clinic_name="Test Clinic",
            slug="test",
            database_name="clinic_test",
            database_host="127.0.0.1",
            database_port=5432,
            database_user="postgres",
            database_password="password",
        )
        
        request = self.factory.post(f'/admin/tenants/tenant/{tenant.id}/delete/')
        request.user = MagicMock()
        # Use simple list for messages instead of FallbackStorage
        request._messages = []
        
        # Patch messages.warning to capture it
        with patch('tenants.admin.messages.warning') as mock_warning:
            # Delete the tenant
            self.admin.delete_model(request, tenant)
            
            # Check that warning message was called
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[0]
            message_text = call_args[1]
            self.assertIn('لم يتم حذفها', message_text)
            self.assertIn('clinic_test', message_text)


class TenantDatabaseRoutingTest(TestCase):
    """
    Test that existing tenant database routing still works after changes.
    """
    
    def test_tenant_model_routes_to_default(self):
        """Tenant model should use default database."""
        from .routers import TenantDatabaseRouter
        
        router = TenantDatabaseRouter()
        db = router.db_for_read(Tenant)
        
        self.assertEqual(db, 'default')
    
    def test_session_routes_to_default(self):
        """Session model should use default database."""
        from django.contrib.sessions.models import Session
        from .routers import TenantDatabaseRouter
        
        router = TenantDatabaseRouter()
        db = router.db_for_read(Session)
        
        self.assertEqual(db, 'default')
    
    def test_tenant_specific_models_route_to_tenant_db(self):
        """Patient model should route to tenant database when set."""
        from patients.models import Patient
        from .routers import TenantDatabaseRouter
        
        router = TenantDatabaseRouter()
        
        # Without tenant context
        db_without = router.db_for_read(Patient)
        self.assertIsNone(db_without)
        
        # With tenant context
        set_current_tenant_db('tenant')
        try:
            db_with = router.db_for_read(Patient)
            self.assertEqual(db_with, 'tenant')
        finally:
            clear_current_tenant_db()
