"""resultados de prueba

Revision ID: c3d5f7a1b9e2
Revises: b7c1e4a9d2f3
Create Date: 2026-09-24 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d5f7a1b9e2'
down_revision: Union[str, Sequence[str], None] = 'b7c1e4a9d2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('resultados_prueba',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('caso_id', sa.Integer(), nullable=False),
    sa.Column('motor', sa.String(), nullable=False),
    sa.Column('camino_obtenido', sa.String(), nullable=False),
    sa.Column('tipo_obtenido', sa.String(), nullable=True),
    sa.Column('urgencia_obtenida', sa.String(), nullable=True),
    sa.Column('motivo', sa.Text(), nullable=True),
    sa.Column('llamadas_llm', sa.Integer(), nullable=False),
    sa.Column('acierto_camino', sa.Boolean(), nullable=False),
    sa.Column('acierto_tipo', sa.Boolean(), nullable=True),
    sa.Column('acierto_urgencia', sa.Boolean(), nullable=True),
    sa.Column('fallo_critico', sa.Boolean(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['caso_id'], ['casos_prueba.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('caso_id', 'motor')
    )
    op.create_index(op.f('ix_resultados_prueba_caso_id'), 'resultados_prueba', ['caso_id'], unique=False)
    op.create_index(op.f('ix_resultados_prueba_motor'), 'resultados_prueba', ['motor'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resultados_prueba_motor'), table_name='resultados_prueba')
    op.drop_index(op.f('ix_resultados_prueba_caso_id'), table_name='resultados_prueba')
    op.drop_table('resultados_prueba')
