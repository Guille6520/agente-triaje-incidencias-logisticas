"""opinion de clef en incidencias

Revision ID: d4e6a8b0c2f4
Revises: c3d5f7a1b9e2
Create Date: 2026-10-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e6a8b0c2f4'
down_revision: Union[str, Sequence[str], None] = 'c3d5f7a1b9e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('incidencias') as batch:
        batch.add_column(sa.Column('clef_manipulacion', sa.Float(), nullable=True))
        batch.add_column(sa.Column('clef_autorizacion', sa.Float(), nullable=True))
        batch.add_column(sa.Column('clef_estado', sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('incidencias') as batch:
        batch.drop_column('clef_estado')
        batch.drop_column('clef_autorizacion')
        batch.drop_column('clef_manipulacion')
