"""Initial Schema Migration

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-06 23:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('ADMIN', 'FACULTY', 'STUDENT', name='userrole'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 2. Exams table
    op.create_table(
        'exams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'PUBLISHED', 'COMPLETED', 'ARCHIVED', name='examstatus'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exams_created_by'), 'exams', ['created_by'], unique=False)
    op.create_index(op.f('ix_exams_id'), 'exams', ['id'], unique=False)

    # 3. Questions table
    op.create_table(
        'questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exam_id', sa.Integer(), nullable=False),
        sa.Column('question_text_encrypted', sa.Text(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('correct_answer_encrypted', sa.Text(), nullable=False),
        sa.Column('marks', sa.Integer(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_questions_exam_id'), 'questions', ['exam_id'], unique=False)
    op.create_index(op.f('ix_questions_id'), 'questions', ['id'], unique=False)

    # 4. Submissions table
    op.create_table(
        'submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exam_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('answers_encrypted', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('auto_score', sa.Float(), nullable=True),
        sa.Column('status', sa.Enum('IN_PROGRESS', 'SUBMITTED', 'EVALUATED', name='submissionstatus'), nullable=False),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_submissions_exam_id'), 'submissions', ['exam_id'], unique=False)
    op.create_index(op.f('ix_submissions_id'), 'submissions', ['id'], unique=False)
    op.create_index(op.f('ix_submissions_student_id'), 'submissions', ['student_id'], unique=False)

    # 5. AuditLogs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_resource', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)

    # 6. ProctoringEvents table
    op.create_table(
        'proctoring_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('frame_reference', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_proctoring_events_id'), 'proctoring_events', ['id'], unique=False)
    op.create_index(op.f('ix_proctoring_events_submission_id'), 'proctoring_events', ['submission_id'], unique=False)
    op.create_index(op.f('ix_proctoring_events_timestamp'), 'proctoring_events', ['timestamp'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_proctoring_events_timestamp'), table_name='proctoring_events')
    op.drop_index(op.f('ix_proctoring_events_submission_id'), table_name='proctoring_events')
    op.drop_index(op.f('ix_proctoring_events_id'), table_name='proctoring_events')
    op.drop_table('proctoring_events')

    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_timestamp'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_index(op.f('ix_submissions_student_id'), table_name='submissions')
    op.drop_index(op.f('ix_submissions_id'), table_name='submissions')
    op.drop_index(op.f('ix_submissions_exam_id'), table_name='submissions')
    op.drop_table('submissions')

    op.drop_index(op.f('ix_questions_id'), table_name='questions')
    op.drop_index(op.f('ix_questions_exam_id'), table_name='questions')
    op.drop_table('questions')

    op.drop_index(op.f('ix_exams_id'), table_name='exams')
    op.drop_index(op.f('ix_exams_created_by'), table_name='exams')
    op.drop_table('exams')

    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
