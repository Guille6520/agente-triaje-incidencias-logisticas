"""datos ampliados: pedidos, clientes, transportistas y casos de prueba

Revision ID: b7c1e4a9d2f3
Revises: ad4b8fe58f67
Create Date: 2026-09-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7c1e4a9d2f3'
down_revision: Union[str, Sequence[str], None] = 'ad4b8fe58f67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('pedidos') as batch:
        batch.add_column(sa.Column('fecha_pedido', sa.Date(), nullable=True))
        batch.add_column(sa.Column('fecha_envio', sa.Date(), nullable=True))
        batch.add_column(sa.Column('fecha_entrega_prevista', sa.Date(), nullable=True))
        batch.add_column(sa.Column('fecha_entrega_real', sa.Date(), nullable=True))
        batch.add_column(sa.Column('provincia_destino', sa.String(), nullable=True))
        batch.add_column(sa.Column('peso_kg', sa.Float(), nullable=True))
        batch.add_column(sa.Column('num_bultos', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('categoria', sa.String(), nullable=True))
        batch.add_column(sa.Column('perecedero', sa.Boolean(), nullable=True))

    op.create_table('clientes',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('nombre', sa.String(), nullable=False),
    sa.Column('tipo', sa.String(), nullable=False),
    sa.Column('empresa', sa.String(), nullable=True),
    sa.Column('fecha_alta', sa.Date(), nullable=False),
    sa.Column('reincidente', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clientes_email'), 'clientes', ['email'], unique=True)

    op.create_table('transportistas',
    sa.Column('nombre', sa.String(), nullable=False),
    sa.Column('zona', sa.String(), nullable=False),
    sa.Column('tasa_retraso', sa.Float(), nullable=False),
    sa.Column('tasa_dano', sa.Float(), nullable=False),
    sa.Column('tasa_perdida', sa.Float(), nullable=False),
    sa.PrimaryKeyConstraint('nombre')
    )

    op.create_table('casos_prueba',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('numero_pedido', sa.String(), nullable=True),
    sa.Column('remitente', sa.String(), nullable=False),
    sa.Column('asunto', sa.String(), nullable=True),
    sa.Column('cuerpo_mensaje', sa.Text(), nullable=False),
    sa.Column('categoria', sa.String(), nullable=False),
    sa.Column('tipo_esperado', sa.String(), nullable=False),
    sa.Column('urgencia_esperada', sa.String(), nullable=False),
    sa.Column('camino_esperado', sa.String(), nullable=False),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_casos_prueba_numero_pedido'), 'casos_prueba', ['numero_pedido'], unique=False)
    op.create_index(op.f('ix_casos_prueba_categoria'), 'casos_prueba', ['categoria'], unique=False)
    op.create_index(op.f('ix_casos_prueba_camino_esperado'), 'casos_prueba', ['camino_esperado'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_casos_prueba_camino_esperado'), table_name='casos_prueba')
    op.drop_index(op.f('ix_casos_prueba_categoria'), table_name='casos_prueba')
    op.drop_index(op.f('ix_casos_prueba_numero_pedido'), table_name='casos_prueba')
    op.drop_table('casos_prueba')
    op.drop_table('transportistas')
    op.drop_index(op.f('ix_clientes_email'), table_name='clientes')
    op.drop_table('clientes')

    with op.batch_alter_table('pedidos') as batch:
        batch.drop_column('perecedero')
        batch.drop_column('categoria')
        batch.drop_column('num_bultos')
        batch.drop_column('peso_kg')
        batch.drop_column('provincia_destino')
        batch.drop_column('fecha_entrega_real')
        batch.drop_column('fecha_entrega_prevista')
        batch.drop_column('fecha_envio')
        batch.drop_column('fecha_pedido')
