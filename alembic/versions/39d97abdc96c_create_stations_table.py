"""create stations table

Revision ID: 39d97abdc96c
Revises: 
Create Date: 2023-09-19 22:52:46.378044

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39d97abdc96c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

## shared names
fk_station_type_name = "fk_stations_station_types"


def upgrade() -> None:
    op.create_table(
        'station_types',
        sa.Column('station_type', sa.String, nullable=False,primary_key=True )
    )

    op.create_table(
        'stations',
        sa.Column('station_id', sa.String(50), primary_key=True, nullable=False),
        sa.Column('station_type', sa.String, nullable=False),
        sa.Column('install_date', sa.Date, nullable=False),
        sa.Column('tz', sa.String(2), nullable=False),
        sa.Column('station_config', sa.String, nullable=False)
    )

    op.create_foreign_key(
    fk_station_type_name,
    "stations", "station_types",
    ["station_type"], ["station_type"],
    )



def downgrade() -> None:
    op.drop_constraint(fk_station_type_name, 'stations', type_='foreignkey')
    op.drop_table('stations')
    op.drop_table('station_types')
