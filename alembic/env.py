import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from app.shared.database.base import Base

# Import de mixins para que Alembic conozca el enum RecordStatus
from app.shared.database.mixins import RecordStatus  # noqa: F401

# Importar modelos de cada módulo aquí conforme se creen:
from app.modules.auth.infrastructure.models import (  # noqa: F401
    PermissionModel,
    RoleModel,
    RolePermissionModel,
    UserModel,
    UserRoleModel,
)
from app.modules.patients.infrastructure.models import PatientModel  # noqa: F401
# from app.modules.appointments.infrastructure.models import AppointmentModel  # noqa: F401
from app.modules.inventory.infrastructure.models import (  # noqa: F401
    BatchModel,
    DispatchExceptionModel,
    DispatchItemModel,
    DispatchLimitModel,
    DispatchModel,
    MedicationModel,
    PrescriptionItemModel,
    PrescriptionModel,
    PurchaseOrderItemModel,
    PurchaseOrderModel,
    SupplierModel,
)

settings = get_settings()
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
