"""academic history

Revision ID: eca69acaa69c
Revises: 8187d287a9d7
Create Date: 2026-08-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eca69acaa69c'
down_revision: Union[str, Sequence[str], None] = '8187d287a9d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('academic_history_records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('student_user_id', sa.Integer(), nullable=False),
    sa.Column('course_id', sa.Integer(), nullable=False),
    sa.Column('period', sa.String(length=10), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('grade', sa.Float(), nullable=True),
    sa.Column('concept', sa.String(length=40), nullable=True),
    sa.Column('times_taken', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_user_id'], ['student_profiles.user_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_user_id', 'course_id', 'period', name='uq_history_student_course_period')
    )
    with op.batch_alter_table('academic_history_records', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_academic_history_records_student_user_id'), ['student_user_id'], unique=False)

    op.create_table('student_enrollments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('student_user_id', sa.Integer(), nullable=False),
    sa.Column('course_id', sa.Integer(), nullable=False),
    sa.Column('period', sa.String(length=10), nullable=False),
    sa.Column('times_taken', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_user_id'], ['student_profiles.user_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_user_id', 'course_id', 'period', name='uq_enrollment_student_course_period')
    )
    with op.batch_alter_table('student_enrollments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_student_enrollments_student_user_id'), ['student_user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('student_enrollments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_student_enrollments_student_user_id'))
    op.drop_table('student_enrollments')

    with op.batch_alter_table('academic_history_records', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_academic_history_records_student_user_id'))
    op.drop_table('academic_history_records')
