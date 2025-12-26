"""add_cluster_id_to_cluster_users

Revision ID: 18a95f4df268
Revises: bbed4c82c4d8
Create Date: 2025-12-26 21:50:27.422338

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "18a95f4df268"
down_revision: Union[str, Sequence[str], None] = "bbed4c82c4d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "cluster_users",
        sa.Column(
            "cluster_id",
            sa.String(length=36),
            nullable=False,
            comment="Идентификатор кластера",
        ),
    )

    op.create_foreign_key(
        "fk_cluster_users_cluster_id_clusters",
        "cluster_users",
        "clusters",
        ["cluster_id"],
        ["id"],
        onupdate="restrict",
        ondelete="restrict",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_cluster_users_cluster_id_clusters",
        "cluster_users",
        type_="foreignkey",
    )

    op.drop_column("cluster_users", "cluster_id")
