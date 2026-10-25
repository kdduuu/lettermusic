
from logging.config import fileConfig

from alembic import context

from backend.app.database import criar_motor
from backend.app.models import Base


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_online():
    motor = criar_motor()

    try:
        with motor.connect() as conexao:
            context.configure(
                connection=conexao,
                target_metadata=target_metadata
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        motor.dispose()


if context.is_offline_mode():
    raise RuntimeError("Esta configuracao exige conexao ao PostgreSQL.")
else:
    run_migrations_online()

from logging.config import fileConfig

from alembic import context

from backend.app.database import criar_motor
from backend.app.models import Base


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_online():
    motor = criar_motor()

    try:
        with motor.connect() as conexao:
            context.configure(
                connection=conexao,
                target_metadata=target_metadata
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        motor.dispose()


if context.is_offline_mode():
    raise RuntimeError("Esta configuracao exige conexao ao PostgreSQL.")
else:
    run_migrations_online()
