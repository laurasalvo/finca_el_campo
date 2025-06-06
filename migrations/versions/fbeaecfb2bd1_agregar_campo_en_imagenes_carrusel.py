"""Agregar campo en imagenes carrusel

Revision ID: fbeaecfb2bd1
Revises: b93481503751
Create Date: 2025-05-21 08:49:24.140122

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fbeaecfb2bd1'
down_revision = 'b93481503751'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('carousel_images', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True, comment='Indica si la imagen está activa para mostrarla'))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('carousel_images', schema=None) as batch_op:
        batch_op.drop_column('is_active')

    # ### end Alembic commands ###
