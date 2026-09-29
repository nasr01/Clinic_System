"""
Account Views Module
Organized into logical submodules for better code organization
"""
from .auth_views import login_view, logout_view
from .doctor_views import doctor_dashboard, doctor_employees
from .secretary_views import secretary_dashboard, secretary_attendance


__all__ = [
    # Auth views
    'login_view',
    'logout_view',
    
    # Doctor views
    'doctor_dashboard',
    'doctor_employees',
    
    # Secretary views
    'secretary_dashboard',
    'secretary_attendance',
]
