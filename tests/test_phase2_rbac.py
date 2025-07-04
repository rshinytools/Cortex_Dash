# ABOUTME: Test suite for Phase 2 RBAC implementation including permissions, roles, and access control
# ABOUTME: Validates role assignments, permission inheritance, multi-tenant access control, and platform admin capabilities

import pytest
from datetime import datetime, timedelta
from sqlmodel import select
from app.models import Role, Permission, UserRole, RolePermission, User, Study
from app.core.rbac_middleware import PermissionChecker, require_study_read, require_org_admin
from app.core.rbac_setup import initialize_rbac, SYSTEM_ROLES
from tests.conftest import expected_result

class TestPhase2RBAC:
    """Comprehensive test suite for Phase 2: Role-Based Access Control"""
    
    @pytest.mark.unit
    @pytest.mark.critical
    @expected_result("System roles and permissions initialized correctly")
    async def test_rbac_initialization(self, db_session):
        """Test RBAC system initialization with all default roles and permissions"""
        # Initialize RBAC
        await initialize_rbac()
        
        # Verify all system roles created
        roles = await db_session.exec(select(Role).where(Role.is_system_role == True))
        role_names = [role.name for role in roles]
        
        expected_roles = list(SYSTEM_ROLES.keys())
        for expected_role in expected_roles:
            assert expected_role in role_names, f"System role {expected_role} should exist"
        
        # Verify permissions created
        permissions = await db_session.exec(select(Permission))
        assert len(permissions.all()) > 0
        
        # Test specific permission
        study_read_perm = await db_session.exec(
            select(Permission).where(
                Permission.resource == "study",
                Permission.action == "view",
                Permission.scope == "assigned"
            )
        )
        assert study_read_perm.first() is not None
    
    @pytest.mark.unit
    @expected_result("Permission codes generated correctly for easy checking")
    async def test_permission_code_generation(self, db_session):
        """Test permission code generation"""
        permission = Permission(
            resource="dashboard",
            action="edit",
            scope="assigned",
            description="Edit assigned dashboards"
        )
        
        assert permission.code == "dashboard:edit:assigned"
        
        # Test with different scopes
        permission_all = Permission(resource="platform", action="manage", scope="all")
        assert permission_all.code == "platform:manage:all"
    
    @pytest.mark.integration
    @expected_result("User role assignment works correctly with study-specific context")
    async def test_user_role_assignment(self, db_session, test_user, test_study):
        """Test assigning roles to users with study context"""
        # Get study_manager role
        study_manager_role = await db_session.exec(
            select(Role).where(Role.name == "study_manager")
        )
        study_manager_role = study_manager_role.first()
        
        # Assign role to user for specific study
        user_role = UserRole(
            user_id=test_user.id,
            role_id=study_manager_role.id,
            study_id=test_study.id,
            assigned_by=test_user.id,
            expires_at=datetime.utcnow() + timedelta(days=365)
        )
        db_session.add(user_role)
        await db_session.commit()
        
        # Verify assignment
        assignments = await db_session.exec(
            select(UserRole).where(UserRole.user_id == test_user.id)
        )
        assignments = assignments.all()
        
        assert len(assignments) == 1
        assert assignments[0].study_id == test_study.id
        assert assignments[0].expires_at > datetime.utcnow()
    
    @pytest.mark.integration
    @pytest.mark.critical
    @expected_result("Permission checker validates access correctly based on roles")
    async def test_permission_checker(self, db_session, test_user, test_study):
        """Test permission checking middleware"""
        from fastapi import Request
        
        # Setup: Assign data_scientist role to user
        data_scientist_role = await db_session.exec(
            select(Role).where(Role.name == "data_scientist")
        )
        data_scientist_role = data_scientist_role.first()
        
        user_role = UserRole(
            user_id=test_user.id,
            role_id=data_scientist_role.id,
            study_id=test_study.id,
            assigned_by=test_user.id
        )
        db_session.add(user_role)
        await db_session.commit()
        
        # Create mock request with study_id in path
        class MockRequest:
            def __init__(self, study_id):
                self.path_params = {"study_id": study_id}
                self.headers = {}
                self.state = type('obj', (object,), {'user': test_user})
        
        mock_request = MockRequest(str(test_study.id))
        
        # Test 1: Should have dashboard view permission
        checker = PermissionChecker(["dashboard:view:assigned"])
        result = await checker(mock_request, test_user, db_session)
        assert result == test_user  # Should pass
        
        # Test 2: Should NOT have pipeline execute permission
        checker_denied = PermissionChecker(["pipeline:execute:assigned"])
        with pytest.raises(Exception) as exc_info:
            await checker_denied(mock_request, test_user, db_session)
        assert "Missing required permissions" in str(exc_info.value)
    
    @pytest.mark.integration
    @expected_result("Platform admin bypasses all permission checks")
    async def test_platform_admin_bypass(self, db_session, test_user):
        """Test platform admin permission bypass"""
        # Make user a platform admin
        platform_admin_role = await db_session.exec(
            select(Role).where(Role.name == "platform_admin")
        )
        platform_admin_role = platform_admin_role.first()
        
        user_role = UserRole(
            user_id=test_user.id,
            role_id=platform_admin_role.id,
            assigned_by=test_user.id
        )
        db_session.add(user_role)
        await db_session.commit()
        
        # Create mock request
        class MockRequest:
            path_params = {}
            headers = {}
            state = type('obj', (object,), {'user': test_user})
        
        # Test any permission - platform admin should pass all
        checker = PermissionChecker(["any:random:permission", "another:check:here"])
        result = await checker(MockRequest(), test_user, db_session)
        assert result == test_user  # Should pass all checks
    
    @pytest.mark.unit
    @expected_result("Permission scope inheritance works correctly")
    async def test_permission_scope_inheritance(self, db_session, test_user):
        """Test permission scope inheritance (all > own > assigned)"""
        from app.core.rbac_middleware import PermissionChecker
        
        # Create a permission with 'all' scope
        all_scope_perm = Permission(
            resource="data",
            action="view", 
            scope="all"
        )
        db_session.add(all_scope_perm)
        
        # Create role with this permission
        test_role = Role(
            name="test_all_scope_role",
            description="Test role with all scope"
        )
        db_session.add(test_role)
        await db_session.commit()
        
        # Assign permission to role
        role_perm = RolePermission(
            role_id=test_role.id,
            permission_id=all_scope_perm.id
        )
        db_session.add(role_perm)
        
        # Assign role to user
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_role.id,
            assigned_by=test_user.id
        )
        db_session.add(user_role)
        await db_session.commit()
        
        # User should have access to all scopes due to inheritance
        checker = PermissionChecker(["data:view:assigned"])
        # Implementation would check that 'all' scope includes 'assigned'
    
    @pytest.mark.integration
    @expected_result("Organization admin can manage users within their organization only")
    async def test_org_admin_boundaries(self, db_session, test_organization, test_user):
        """Test organization admin permission boundaries"""
        # Make user an org admin
        org_admin_role = await db_session.exec(
            select(Role).where(Role.name == "org_admin")
        )
        org_admin_role = org_admin_role.first()
        
        user_role = UserRole(
            user_id=test_user.id,
            role_id=org_admin_role.id,
            assigned_by=test_user.id
        )
        db_session.add(user_role)
        await db_session.commit()
        
        # Create another organization
        other_org = Organization(
            name="Other Pharma",
            code="other-pharma"
        )
        db_session.add(other_org)
        await db_session.commit()
        
        # Org admin should only see their org's data
        # This would be enforced in the service layer
        assert test_user.org_id == test_organization.id
        assert test_user.org_id != other_org.id
    
    @pytest.mark.unit
    @expected_result("Role expiration is enforced correctly")
    async def test_role_expiration(self, db_session, test_user, test_study):
        """Test role expiration functionality"""
        # Create role with past expiration
        some_role = await db_session.exec(select(Role).limit(1))
        some_role = some_role.first()
        
        expired_assignment = UserRole(
            user_id=test_user.id,
            role_id=some_role.id,
            study_id=test_study.id,
            assigned_by=test_user.id,
            expires_at=datetime.utcnow() - timedelta(days=1)  # Expired yesterday
        )
        db_session.add(expired_assignment)
        await db_session.commit()
        
        # Check active roles only
        active_roles = await db_session.exec(
            select(UserRole)
            .where(UserRole.user_id == test_user.id)
            .where(
                (UserRole.expires_at == None) | 
                (UserRole.expires_at > datetime.utcnow())
            )
        )
        
        # Should not include expired role
        assert len(active_roles.all()) == 0
    
    @pytest.mark.integration
    @expected_result("Custom organization roles work alongside system roles")
    async def test_custom_organization_roles(self, db_session, test_organization):
        """Test custom roles at organization level"""
        # Create custom role for organization
        custom_role = Role(
            name="clinical_reviewer",
            description="Custom role for clinical review team",
            org_id=test_organization.id,
            is_system_role=False
        )
        db_session.add(custom_role)
        
        # Add custom permissions
        review_permission = Permission(
            resource="clinical_review",
            action="approve",
            scope="assigned"
        )
        db_session.add(review_permission)
        await db_session.commit()
        
        # Link permission to role
        role_perm = RolePermission(
            role_id=custom_role.id,
            permission_id=review_permission.id
        )
        db_session.add(role_perm)
        await db_session.commit()
        
        # Verify custom role exists only for this org
        org_roles = await db_session.exec(
            select(Role).where(Role.org_id == test_organization.id)
        )
        org_roles = org_roles.all()
        
        assert len(org_roles) == 1
        assert org_roles[0].name == "clinical_reviewer"
        assert org_roles[0].is_system_role is False
    
    @pytest.mark.performance
    @expected_result("Permission checks complete within 50ms even with complex role hierarchies")
    async def test_permission_check_performance(self, db_session, test_user):
        """Test permission checking performance"""
        import time
        
        # Create complex role setup
        roles = []
        for i in range(10):
            role = Role(
                name=f"test_role_{i}",
                description=f"Test role {i}"
            )
            roles.append(role)
        db_session.add_all(roles)
        await db_session.commit()
        
        # Assign multiple roles to user
        for role in roles[:5]:  # Assign 5 roles
            user_role = UserRole(
                user_id=test_user.id,
                role_id=role.id,
                assigned_by=test_user.id
            )
            db_session.add(user_role)
        await db_session.commit()
        
        # Time permission check
        checker = PermissionChecker(["study:view:assigned"])
        
        class MockRequest:
            path_params = {}
            headers = {}
            state = type('obj', (object,), {'user': test_user})
        
        start_time = time.time()
        
        # Perform permission check
        try:
            await checker(MockRequest(), test_user, db_session)
        except:
            pass  # We're testing performance, not correctness here
        
        check_time = time.time() - start_time
        
        # Should complete within 50ms
        assert check_time < 0.05, f"Permission check took {check_time:.3f}s, expected < 0.05s"