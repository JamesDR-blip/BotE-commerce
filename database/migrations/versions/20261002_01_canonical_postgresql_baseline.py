"""Create the canonical PostgreSQL 16 schema baseline.

Revision ID: 20261002_01
Revises:
Create Date: 2026-10-02

This is a frozen Alembic operation script. It does not import ORM metadata,
call create_all(), create seed data, or inspect pre-existing tables.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20261002_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('organizations',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('permissions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('resource', sa.String(length=100), nullable=False),
    sa.Column('action', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('resource', 'action', name='uq_permissions_resource_action')
    )
    op.create_table('risk_policies',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('high_risk_threshold', sa.Float(), nullable=False),
    sa.Column('critical_risk_threshold', sa.Float(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('roles',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('users',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('display_name', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('compliance_policies',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('organization_id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('resource', sa.String(length=100), nullable=False),
    sa.Column('action', sa.String(length=100), nullable=False),
    sa.Column('condition', sa.JSON(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('organization_id', 'name', name='uq_compliance_policy_organization_name')
    )
    op.create_table('memberships',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('organization_id', sa.String(length=36), nullable=False),
    sa.Column('role_id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'organization_id', 'role_id', name='uq_memberships_user_org_role')
    )
    op.create_table('organization_quotas',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('organization_id', sa.String(length=36), nullable=False),
    sa.Column('dimension', sa.String(length=50), nullable=False),
    sa.Column('limit', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('organization_id', 'dimension', name='uq_organization_quota_dimension')
    )
    op.create_table('role_permissions',
    sa.Column('role_id', sa.String(length=36), nullable=False),
    sa.Column('permission_id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.PrimaryKeyConstraint('role_id', 'permission_id'),
    sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permissions_role_permission')
    )
    op.create_table('workspaces',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('owner_id', sa.String(length=36), nullable=False),
    sa.Column('organization_id', sa.String(length=36), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('agent_memory',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('workspace_id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('memory_type', sa.String(length=64), nullable=False),
    sa.Column('memory_key', sa.String(length=255), nullable=False),
    sa.Column('value_json', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('channels',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('workspace_id', sa.String(length=36), nullable=False),
    sa.Column('channel_type', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('credentials_encrypted', sa.Text(), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('workspace_id', 'channel_type', 'name', name='uq_channels_workspace_channel_name')
    )
    op.create_table('projects',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('workspace_id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('channel_mappings',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('channel_id', sa.String(length=36), nullable=False),
    sa.Column('canonical_product_id', sa.String(length=255), nullable=False),
    sa.Column('channel_type', sa.String(length=50), nullable=False),
    sa.Column('external_product_id', sa.String(length=255), nullable=False),
    sa.Column('last_synced_hash', sa.String(length=64), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('channel_id', 'canonical_product_id', name='uq_channel_mappings_channel_product')
    )
    op.create_table('datasets',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('project_id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('source_type', sa.String(length=50), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=True),
    sa.Column('file_format', sa.String(length=20), nullable=True),
    sa.Column('size_bytes', sa.Integer(), nullable=True),
    sa.Column('content_hash', sa.String(length=64), nullable=True),
    sa.Column('storage_key', sa.Text(), nullable=True),
    sa.Column('row_count', sa.Integer(), nullable=True),
    sa.Column('column_count', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('workflows',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('project_id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('active_version', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('executions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=True),
    sa.Column('dataset_id', sa.String(length=36), nullable=True),
    sa.Column('category', sa.String(length=100), nullable=False),
    sa.Column('source_hash', sa.String(length=64), nullable=False),
    sa.Column('rule_version', sa.String(length=64), nullable=False),
    sa.Column('health_score', sa.Float(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('requirement_json', sa.Text(), nullable=True),
    sa.Column('plan_json', sa.Text(), nullable=True),
    sa.Column('planner_version', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sync_jobs',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('workspace_id', sa.String(length=36), nullable=False),
    sa.Column('dataset_id', sa.String(length=36), nullable=False),
    sa.Column('channel_id', sa.String(length=36), nullable=False),
    sa.Column('idempotency_key', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('workspace_id', 'idempotency_key', name='uq_sync_jobs_workspace_idempotency')
    )
    op.create_table('workflow_executions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('workflow_id', sa.String(length=36), nullable=False),
    sa.Column('dataset_id', sa.String(length=36), nullable=True),
    sa.Column('workflow_version', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('inputs_json', sa.Text(), nullable=True),
    sa.Column('outputs_json', sa.Text(), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ),
    sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('workflow_versions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('workflow_id', sa.String(length=36), nullable=False),
    sa.Column('version', sa.String(length=50), nullable=False),
    sa.Column('plan_json', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('workflow_id', 'version', name='uq_workflow_version')
    )
    op.create_table('capability_execution_traces',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('workflow_execution_id', sa.String(length=36), nullable=False),
    sa.Column('capability_id', sa.String(length=100), nullable=False),
    sa.Column('capability_version', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('inputs_json', sa.Text(), nullable=True),
    sa.Column('outputs_json', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('finished_at', sa.DateTime(), nullable=True),
    sa.Column('duration_ms', sa.Float(), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['workflow_execution_id'], ['workflow_executions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('changesets',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('dataset_id', sa.String(length=36), nullable=False),
    sa.Column('execution_id', sa.String(length=36), nullable=False),
    sa.Column('workflow_id', sa.String(length=36), nullable=False),
    sa.Column('workflow_version', sa.String(length=50), nullable=False),
    sa.Column('before_storage_key', sa.Text(), nullable=False),
    sa.Column('before_content_hash', sa.String(length=64), nullable=False),
    sa.Column('after_storage_key', sa.Text(), nullable=False),
    sa.Column('after_content_hash', sa.String(length=64), nullable=False),
    sa.Column('integrity_hash', sa.String(length=64), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('rolled_back_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ),
    sa.ForeignKeyConstraint(['execution_id'], ['workflow_executions.id'], ),
    sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('data_lineage_events',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('dataset_id', sa.String(length=36), nullable=False),
    sa.Column('execution_id', sa.String(length=36), nullable=False),
    sa.Column('workflow_id', sa.String(length=36), nullable=False),
    sa.Column('workflow_version', sa.String(length=50), nullable=False),
    sa.Column('capability_id', sa.String(length=100), nullable=False),
    sa.Column('capability_version', sa.String(length=50), nullable=False),
    sa.Column('event_type', sa.String(length=50), nullable=False),
    sa.Column('input_refs_json', sa.JSON(), nullable=False),
    sa.Column('output_refs_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ),
    sa.ForeignKeyConstraint(['execution_id'], ['workflow_executions.id'], ),
    sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('execution_traces',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('execution_id', sa.String(length=36), nullable=False),
    sa.Column('capability_id', sa.String(length=100), nullable=False),
    sa.Column('capability_version', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('inputs_json', sa.Text(), nullable=True),
    sa.Column('outputs_json', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('finished_at', sa.DateTime(), nullable=True),
    sa.Column('duration_ms', sa.Float(), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['execution_id'], ['executions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('reports',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('execution_id', sa.String(length=36), nullable=False),
    sa.Column('format', sa.String(length=12), nullable=False),
    sa.Column('path', sa.Text(), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['execution_id'], ['executions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('risk_assessments',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('execution_id', sa.String(length=36), nullable=False),
    sa.Column('risk_score', sa.String(length=20), nullable=False),
    sa.Column('confidence_score', sa.Float(), nullable=False),
    sa.Column('approval_required', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['execution_id'], ['workflow_executions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sync_attempts',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('sync_job_id', sa.String(length=36), nullable=False),
    sa.Column('attempt_number', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('request_hash', sa.String(length=64), nullable=False),
    sa.Column('external_product_id', sa.String(length=255), nullable=False),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['sync_job_id'], ['sync_jobs.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('sync_job_id', 'attempt_number', name='uq_sync_attempts_job_attempt')
    )
    op.create_table('validation_logs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('execution_id', sa.String(length=36), nullable=False),
    sa.Column('row_number', sa.Integer(), nullable=False),
    sa.Column('field', sa.String(length=100), nullable=False),
    sa.Column('code', sa.String(length=100), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('severity', sa.String(length=20), nullable=False),
    sa.ForeignKeyConstraint(['execution_id'], ['executions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('approvals',
    sa.Column('approval_id', sa.String(length=36), nullable=False),
    sa.Column('execution_id', sa.String(length=36), nullable=False),
    sa.Column('changeset_id', sa.String(length=36), nullable=False),
    sa.Column('risk_score', sa.String(length=20), nullable=False),
    sa.Column('confidence_score', sa.Float(), nullable=False),
    sa.Column('requested_by', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('decision', sa.String(length=20), nullable=True),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.ForeignKeyConstraint(['changeset_id'], ['changesets.id'], ),
    sa.ForeignKeyConstraint(['execution_id'], ['workflow_executions.id'], ),
    sa.PrimaryKeyConstraint('approval_id')
    )
    op.create_table('audit_events',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('workspace_id', sa.String(length=36), nullable=False),
    sa.Column('actor_id', sa.String(length=36), nullable=False),
    sa.Column('action', sa.String(length=100), nullable=False),
    sa.Column('resource_type', sa.String(length=100), nullable=False),
    sa.Column('resource_id', sa.String(length=36), nullable=False),
    sa.Column('execution_id', sa.String(length=36), nullable=True),
    sa.Column('changeset_id', sa.String(length=36), nullable=True),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('previous_hash', sa.String(length=64), nullable=True),
    sa.Column('event_hash', sa.String(length=64), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['changeset_id'], ['changesets.id'], ),
    sa.ForeignKeyConstraint(['execution_id'], ['workflow_executions.id'], ),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('changeset_items',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('changeset_id', sa.String(length=36), nullable=False),
    sa.Column('entity', sa.String(length=100), nullable=False),
    sa.Column('record_id', sa.String(length=255), nullable=False),
    sa.Column('before_snapshot', sa.JSON(), nullable=False),
    sa.Column('after_snapshot', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['changeset_id'], ['changesets.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_created_at'), 'organizations', ['created_at'], unique=False)
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_compliance_policies_organization_id'), 'compliance_policies', ['organization_id'], unique=False)
    op.create_index(op.f('ix_memberships_created_at'), 'memberships', ['created_at'], unique=False)
    op.create_index(op.f('ix_memberships_organization_id'), 'memberships', ['organization_id'], unique=False)
    op.create_index(op.f('ix_memberships_role_id'), 'memberships', ['role_id'], unique=False)
    op.create_index(op.f('ix_memberships_user_id'), 'memberships', ['user_id'], unique=False)
    op.create_index(op.f('ix_organization_quotas_organization_id'), 'organization_quotas', ['organization_id'], unique=False)
    op.create_index(op.f('ix_workspaces_created_at'), 'workspaces', ['created_at'], unique=False)
    op.create_index(op.f('ix_workspaces_organization_id'), 'workspaces', ['organization_id'], unique=False)
    op.create_index(op.f('ix_workspaces_owner_id'), 'workspaces', ['owner_id'], unique=False)
    op.create_index(op.f('ix_agent_memory_expires_at'), 'agent_memory', ['expires_at'], unique=False)
    op.create_index('ix_agent_memory_scope_type_key', 'agent_memory', ['workspace_id', 'user_id', 'memory_type', 'memory_key'], unique=False)
    op.create_index(op.f('ix_agent_memory_user_id'), 'agent_memory', ['user_id'], unique=False)
    op.create_index(op.f('ix_agent_memory_workspace_id'), 'agent_memory', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_channels_created_at'), 'channels', ['created_at'], unique=False)
    op.create_index(op.f('ix_channels_workspace_id'), 'channels', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_projects_workspace_id'), 'projects', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_channel_mappings_canonical_product_id'), 'channel_mappings', ['canonical_product_id'], unique=False)
    op.create_index(op.f('ix_channel_mappings_channel_id'), 'channel_mappings', ['channel_id'], unique=False)
    op.create_index(op.f('ix_channel_mappings_created_at'), 'channel_mappings', ['created_at'], unique=False)
    op.create_index(op.f('ix_datasets_content_hash'), 'datasets', ['content_hash'], unique=False)
    op.create_index(op.f('ix_datasets_project_id'), 'datasets', ['project_id'], unique=False)
    op.create_index(op.f('ix_datasets_status'), 'datasets', ['status'], unique=False)
    op.create_index(op.f('ix_workflows_project_id'), 'workflows', ['project_id'], unique=False)
    op.create_index(op.f('ix_executions_category'), 'executions', ['category'], unique=False)
    op.create_index(op.f('ix_executions_created_at'), 'executions', ['created_at'], unique=False)
    op.create_index(op.f('ix_executions_dataset_id'), 'executions', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_executions_source_hash'), 'executions', ['source_hash'], unique=False)
    op.create_index(op.f('ix_executions_user_id'), 'executions', ['user_id'], unique=False)
    op.create_index(op.f('ix_sync_jobs_channel_id'), 'sync_jobs', ['channel_id'], unique=False)
    op.create_index(op.f('ix_sync_jobs_created_at'), 'sync_jobs', ['created_at'], unique=False)
    op.create_index(op.f('ix_sync_jobs_dataset_id'), 'sync_jobs', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_sync_jobs_status'), 'sync_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_sync_jobs_workspace_id'), 'sync_jobs', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_workflow_executions_created_at'), 'workflow_executions', ['created_at'], unique=False)
    op.create_index(op.f('ix_workflow_executions_dataset_id'), 'workflow_executions', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_workflow_executions_workflow_id'), 'workflow_executions', ['workflow_id'], unique=False)
    op.create_index(op.f('ix_workflow_versions_workflow_id'), 'workflow_versions', ['workflow_id'], unique=False)
    op.create_index(op.f('ix_capability_execution_traces_workflow_execution_id'), 'capability_execution_traces', ['workflow_execution_id'], unique=False)
    op.create_index(op.f('ix_changesets_created_at'), 'changesets', ['created_at'], unique=False)
    op.create_index(op.f('ix_changesets_dataset_id'), 'changesets', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_changesets_execution_id'), 'changesets', ['execution_id'], unique=False)
    op.create_index(op.f('ix_changesets_status'), 'changesets', ['status'], unique=False)
    op.create_index(op.f('ix_changesets_workflow_id'), 'changesets', ['workflow_id'], unique=False)
    op.create_index(op.f('ix_data_lineage_events_created_at'), 'data_lineage_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_data_lineage_events_dataset_id'), 'data_lineage_events', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_data_lineage_events_execution_id'), 'data_lineage_events', ['execution_id'], unique=False)
    op.create_index(op.f('ix_data_lineage_events_workflow_id'), 'data_lineage_events', ['workflow_id'], unique=False)
    op.create_index(op.f('ix_execution_traces_execution_id'), 'execution_traces', ['execution_id'], unique=False)
    op.create_index(op.f('ix_reports_execution_id'), 'reports', ['execution_id'], unique=False)
    op.create_index(op.f('ix_risk_assessments_execution_id'), 'risk_assessments', ['execution_id'], unique=False)
    op.create_index(op.f('ix_sync_attempts_created_at'), 'sync_attempts', ['created_at'], unique=False)
    op.create_index(op.f('ix_sync_attempts_status'), 'sync_attempts', ['status'], unique=False)
    op.create_index(op.f('ix_sync_attempts_sync_job_id'), 'sync_attempts', ['sync_job_id'], unique=False)
    op.create_index(op.f('ix_validation_logs_execution_id'), 'validation_logs', ['execution_id'], unique=False)
    op.create_index(op.f('ix_approvals_changeset_id'), 'approvals', ['changeset_id'], unique=False)
    op.create_index(op.f('ix_approvals_execution_id'), 'approvals', ['execution_id'], unique=False)
    op.create_index(op.f('ix_audit_events_actor_id'), 'audit_events', ['actor_id'], unique=False)
    op.create_index(op.f('ix_audit_events_changeset_id'), 'audit_events', ['changeset_id'], unique=False)
    op.create_index(op.f('ix_audit_events_created_at'), 'audit_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_events_event_hash'), 'audit_events', ['event_hash'], unique=True)
    op.create_index(op.f('ix_audit_events_execution_id'), 'audit_events', ['execution_id'], unique=False)
    op.create_index(op.f('ix_audit_events_resource_id'), 'audit_events', ['resource_id'], unique=False)
    op.create_index(op.f('ix_audit_events_workspace_id'), 'audit_events', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_changeset_items_changeset_id'), 'changeset_items', ['changeset_id'], unique=False)


def downgrade() -> None:
    raise RuntimeError("The canonical baseline is not downgradeable; restore a matching database backup or use a reviewed forward fix.")
