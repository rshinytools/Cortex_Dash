-- ABOUTME: Complete database initialization script for Cortex Dashboard
-- ABOUTME: Creates all tables, enums, indexes and initial data for fresh installation

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create ENUM types with correct values
CREATE TYPE organizationtype AS ENUM ('pharmaceutical', 'biotech', 'cro', 'academic', 'other');
CREATE TYPE studyphase AS ENUM ('phase_1', 'phase_2', 'phase_3', 'phase_4', 'observational', 'expanded_access');
CREATE TYPE studystatus AS ENUM ('DRAFT', 'PLANNING', 'SETUP', 'ACTIVE', 'PAUSED', 'COMPLETED', 'ARCHIVED');
CREATE TYPE dashboardcategory AS ENUM ('overview', 'safety', 'efficacy', 'operational', 'quality', 'custom');
CREATE TYPE templatestatus AS ENUM ('PUBLISHED', 'DEPRECATED', 'ARCHIVED');
CREATE TYPE inheritancetype AS ENUM ('none', 'extends', 'includes');
CREATE TYPE menuitemtype AS ENUM ('dashboard_page', 'group', 'divider', 'external');
CREATE TYPE widgettype AS ENUM ('metric', 'chart', 'table', 'text', 'custom');
CREATE TYPE charttype AS ENUM ('line', 'bar', 'pie', 'scatter', 'heatmap', 'box', 'area');
CREATE TYPE datasourcetype AS ENUM ('api', 'sftp', 'folder', 'manual', 'database');
CREATE TYPE pipelinestatus AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
CREATE TYPE activitytype AS ENUM ('create', 'update', 'delete', 'access', 'export', 'import', 'process');
CREATE TYPE filetype AS ENUM ('sas7bdat', 'xpt', 'csv', 'excel', 'parquet', 'json');
CREATE TYPE processingstatusenum AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled');

-- Create organization table
CREATE TABLE organization (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE,
    type organizationtype DEFAULT 'pharmaceutical',
    is_active BOOLEAN DEFAULT true,
    settings JSON DEFAULT '{}',
    features JSON DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user table
CREATE TABLE "user" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    org_id UUID REFERENCES organization(id),
    role VARCHAR(50),
    permissions JSON DEFAULT '[]',
    preferences JSON DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Create study table
CREATE TABLE study (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50),
    protocol_number VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    phase studyphase,
    therapeutic_area VARCHAR(100),
    indication VARCHAR(255),
    planned_start_date TIMESTAMP,
    planned_end_date TIMESTAMP,
    actual_start_date TIMESTAMP,
    actual_end_date TIMESTAMP,
    config JSON DEFAULT '{}',
    pipeline_config JSON DEFAULT '{}',
    dashboard_config JSON DEFAULT '{}',
    dashboard_template_id UUID,
    field_mappings JSON DEFAULT '{}',
    template_overrides JSON DEFAULT '{}',
    data_retention_days INTEGER DEFAULT 2555,
    refresh_frequency VARCHAR(50) DEFAULT 'daily',
    org_id UUID NOT NULL REFERENCES organization(id),
    status studystatus DEFAULT 'SETUP',
    is_active BOOLEAN DEFAULT true,
    initialization_status VARCHAR(50) DEFAULT 'not_started',
    initialization_progress INTEGER DEFAULT 0,
    initialization_steps JSON DEFAULT '{}',
    template_applied_at TIMESTAMP,
    data_uploaded_at TIMESTAMP,
    mappings_configured_at TIMESTAMP,
    activated_at TIMESTAMP,
    last_transformation_at TIMESTAMP,
    transformation_status VARCHAR(50),
    transformation_count INTEGER DEFAULT 0,
    derived_datasets JSON DEFAULT '{}',
    transformation_errors JSON DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES "user"(id),
    updated_by UUID REFERENCES "user"(id),
    folder_path VARCHAR(500),
    protocol_version VARCHAR(20) DEFAULT '1.0',
    protocol_approved_date TIMESTAMP,
    protocol_approved_by UUID REFERENCES "user"(id),
    subject_count INTEGER DEFAULT 0,
    site_count INTEGER DEFAULT 0,
    data_points_count INTEGER DEFAULT 0,
    last_data_update TIMESTAMP
);

-- Create dashboard_templates table
CREATE TABLE dashboard_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category dashboardcategory DEFAULT 'overview',
    major_version INTEGER DEFAULT 1,
    minor_version INTEGER DEFAULT 0,
    patch_version INTEGER DEFAULT 0,
    status templatestatus DEFAULT 'PUBLISHED',
    parent_template_id UUID REFERENCES dashboard_templates(id),
    inheritance_type inheritancetype DEFAULT 'none',
    template_structure JSON NOT NULL,
    required_fields JSON DEFAULT '[]',
    field_mappings JSON DEFAULT '{}',
    default_filters JSON DEFAULT '{}',
    permissions JSON DEFAULT '{}',
    tags VARCHAR[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    is_system BOOLEAN DEFAULT false,
    created_by UUID REFERENCES "user"(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP,
    published_by UUID REFERENCES "user"(id)
);

-- Create widget_definitions table
CREATE TABLE widget_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    type widgettype NOT NULL,
    chart_type charttype,
    config_schema JSON NOT NULL,
    default_config JSON DEFAULT '{}',
    data_requirements JSON DEFAULT '{}',
    render_template TEXT,
    script_template TEXT,
    style_template TEXT,
    category VARCHAR(50),
    tags VARCHAR[] DEFAULT '{}',
    version VARCHAR(20) DEFAULT '1.0.0',
    is_active BOOLEAN DEFAULT true,
    is_system BOOLEAN DEFAULT false,
    created_by UUID REFERENCES "user"(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create study_data_configuration table
CREATE TABLE study_data_configuration (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    study_id UUID NOT NULL REFERENCES study(id) ON DELETE CASCADE,
    dataset_schemas JSON DEFAULT '{}',
    field_mappings JSON DEFAULT '{}',
    calculated_fields JSON DEFAULT '{}',
    data_quality_rules JSON DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES "user"(id),
    updated_by UUID REFERENCES "user"(id),
    UNIQUE(study_id)
);

-- Create data_source table
CREATE TABLE data_source (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type datasourcetype NOT NULL,
    study_id UUID NOT NULL REFERENCES study(id) ON DELETE CASCADE,
    connection_config JSON NOT NULL,
    sync_config JSON DEFAULT '{}',
    last_sync_at TIMESTAMP,
    last_sync_status VARCHAR(50),
    last_sync_error TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES "user"(id)
);

-- Create pipeline_config table
CREATE TABLE pipeline_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    study_id UUID NOT NULL REFERENCES study(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    pipeline_type VARCHAR(50) NOT NULL,
    source_config JSON NOT NULL,
    transformation_steps JSON DEFAULT '[]',
    output_config JSON NOT NULL,
    schedule_config JSON DEFAULT '{}',
    error_handling JSON DEFAULT '{}',
    version INTEGER DEFAULT 1,
    is_current_version BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES "user"(id),
    updated_by UUID REFERENCES "user"(id)
);

-- Create pipeline_execution table
CREATE TABLE pipeline_execution (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_config_id UUID NOT NULL REFERENCES pipeline_config(id),
    study_id UUID NOT NULL REFERENCES study(id),
    execution_id VARCHAR(255) UNIQUE NOT NULL,
    status pipelinestatus DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    input_metadata JSON DEFAULT '{}',
    output_metadata JSON DEFAULT '{}',
    error_details JSON,
    logs TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES "user"(id)
);

-- Create activity_log table
CREATE TABLE activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES "user"(id),
    org_id UUID REFERENCES organization(id),
    study_id UUID REFERENCES study(id),
    activity_type activitytype NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    description TEXT,
    metadata JSON DEFAULT '{}',
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create widget_data_mapping table
CREATE TABLE widget_data_mapping (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    study_id UUID NOT NULL REFERENCES study(id) ON DELETE CASCADE,
    widget_code VARCHAR(50) NOT NULL,
    dashboard_id VARCHAR(100),
    dataset_name VARCHAR(100),
    field_mappings JSON NOT NULL,
    filters JSON DEFAULT '{}',
    transformations JSON DEFAULT '{}',
    cache_config JSON DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES "user"(id),
    updated_by UUID REFERENCES "user"(id)
);

-- Create data_source_upload table (if not exists check for migration compatibility)
CREATE TABLE IF NOT EXISTS data_source_upload (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    study_id UUID NOT NULL REFERENCES study(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES organization(id),
    file_name VARCHAR(255) NOT NULL,
    file_type filetype NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    upload_status processingstatusenum DEFAULT 'pending',
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    error_message TEXT,
    dataset_name VARCHAR(100),
    row_count INTEGER,
    column_count INTEGER,
    data_schema JSON,
    validation_results JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES "user"(id)
);

-- Create indexes for performance
CREATE INDEX idx_study_org_id ON study(org_id);
CREATE INDEX idx_study_status ON study(status);
CREATE INDEX idx_study_protocol ON study(protocol_number);
CREATE INDEX idx_user_email ON "user"(email);
CREATE INDEX idx_user_org_id ON "user"(org_id);
CREATE INDEX idx_activity_log_user ON activity_log(user_id);
CREATE INDEX idx_activity_log_study ON activity_log(study_id);
CREATE INDEX idx_activity_log_created ON activity_log(created_at);
CREATE INDEX idx_data_source_study ON data_source(study_id);
CREATE INDEX idx_pipeline_config_study ON pipeline_config(study_id);
CREATE INDEX idx_pipeline_execution_study ON pipeline_execution(study_id);
CREATE INDEX idx_widget_mapping_study ON widget_data_mapping(study_id);

-- Insert default organization
INSERT INTO organization (id, name, slug, type, is_active, settings, features)
VALUES (
    '459f818d-baa6-4f85-ae82-a2c4e0d77ab8',
    'Sagarmatha AI',
    'sagarmatha-ai',
    'pharmaceutical',
    true,
    '{}',
    '{}'
);

-- Insert default admin user (password: adadad123)
INSERT INTO "user" (id, email, hashed_password, full_name, is_active, is_superuser, org_id, role)
VALUES (
    '9d6d95c0-e28a-4eef-b9b0-86f7d8c2e9c7',
    'admin@sagarmatha.ai',
    '$2b$12$iWZQkqdDWVSskV7m7Lj8Q.MfzL7wH7tY5Qv5r7FQzKqOKl1R6zXFy',
    'System Administrator',
    true,
    true,
    '459f818d-baa6-4f85-ae82-a2c4e0d77ab8',
    'admin'
);

-- Create update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update timestamp triggers
CREATE TRIGGER update_organization_updated_at BEFORE UPDATE ON organization
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_updated_at BEFORE UPDATE ON "user"
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_study_updated_at BEFORE UPDATE ON study
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dashboard_templates_updated_at BEFORE UPDATE ON dashboard_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_widget_definitions_updated_at BEFORE UPDATE ON widget_definitions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed for your setup)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;