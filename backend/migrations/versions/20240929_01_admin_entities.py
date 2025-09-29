"""admin entities: teams, contracts, team_members

Revision ID: 20240929_01
Revises: <put_previous_revision_id_here>
Create Date: 2025-09-29

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240929_01'
down_revision = '<PUT_PREVIOUS_REVISION_ID>'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('supervisor_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.UniqueConstraint('name', name='uq_team_name')
    )

    op.create_table(
        'contracts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('posts.id'), nullable=False),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id'), nullable=True),
        sa.Column('start', sa.Date(), nullable=False),
        sa.Column('end', sa.Date(), nullable=True),
    )
    op.create_index('ix_contracts_user_post_dates', 'contracts', ['user_id','post_id','start','end'])

    op.create_table(
        'team_members',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False, server_default='nchd'),
        sa.UniqueConstraint('team_id','user_id', name='uq_team_user')
    )
    op.create_index('ix_team_members_team', 'team_members', ['team_id'])
    op.create_index('ix_team_members_user', 'team_members', ['user_id'])

def downgrade():
    op.drop_index('ix_team_members_user', table_name='team_members')
    op.drop_index('ix_team_members_team', table_name='team_members')
    op.drop_table('team_members')
    op.drop_index('ix_contracts_user_post_dates', table_name='contracts')
    op.drop_table('contracts')
    op.drop_table('teams')
