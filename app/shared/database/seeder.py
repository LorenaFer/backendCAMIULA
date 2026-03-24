"""
Clase base para seeders de módulos.

Cada módulo puede tener uno o más seeders en:
    app/modules/{modulo}/infrastructure/seeders/

Un seeder es una clase que hereda de BaseSeeder e implementa `run()`.

Uso:
    python -m app.shared.database.seeder              # ejecuta TODOS los seeders
    python -m app.shared.database.seeder patients      # ejecuta solo los de patients
    python -m app.shared.database.seeder --fresh        # limpia tablas antes de sembrar
"""

import asyncio
import importlib
import pkgutil
import sys
from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database.session import async_session_factory


class BaseSeeder(ABC):
    """Clase base para seeders de datos."""

    # Orden de ejecución (menor = primero). Útil para dependencias entre seeders.
    order: int = 100

    @abstractmethod
    async def run(self, session: AsyncSession) -> None:
        """Inserta los datos iniciales/de prueba."""
        ...

    @abstractmethod
    async def clear(self, session: AsyncSession) -> None:
        """Elimina los datos sembrados por este seeder (para --fresh)."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__module__}.{self.__class__.__name__}"


def discover_seeders(module_filter: Optional[str] = None) -> list[BaseSeeder]:
    """Descubre todos los seeders registrados en los módulos.

    Si module_filter se provee, solo carga seeders de ese módulo.
    """
    seeders: list[BaseSeeder] = []
    modules_path = "app.modules"

    try:
        modules_pkg = importlib.import_module(modules_path)
    except ImportError:
        return seeders

    for _, module_name, is_pkg in pkgutil.iter_modules(
        modules_pkg.__path__, prefix=f"{modules_path}."
    ):
        if not is_pkg:
            continue

        short_name = module_name.split(".")[-1]
        if module_filter and short_name != module_filter:
            continue

        seeders_path = f"{module_name}.infrastructure.seeders"
        try:
            seeders_pkg = importlib.import_module(seeders_path)
        except ImportError:
            continue

        for _, seeder_mod_name, _ in pkgutil.iter_modules(
            seeders_pkg.__path__, prefix=f"{seeders_path}."
        ):
            try:
                mod = importlib.import_module(seeder_mod_name)
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseSeeder)
                        and attr is not BaseSeeder
                    ):
                        seeders.append(attr())
            except ImportError:
                continue

    seeders.sort(key=lambda s: s.order)
    return seeders


async def run_seeders(
    module_filter: Optional[str] = None,
    fresh: bool = False,
) -> None:
    """Ejecuta los seeders descubiertos."""
    seeders = discover_seeders(module_filter)

    if not seeders:
        scope = f"módulo '{module_filter}'" if module_filter else "el proyecto"
        print(f"No se encontraron seeders en {scope}.")
        return

    async with async_session_factory() as session:
        if fresh:
            print("Limpiando datos existentes (--fresh)...")
            for seeder in reversed(seeders):
                print(f"  Clearing: {seeder}")
                await seeder.clear(session)
            await session.commit()

        print(f"Ejecutando {len(seeders)} seeder(s)...")
        for seeder in seeders:
            print(f"  Seeding: {seeder}")
            await seeder.run(session)
        await session.commit()

    print("Seeders ejecutados exitosamente.")


if __name__ == "__main__":
    args = sys.argv[1:]
    module_filter = None
    fresh = False

    for arg in args:
        if arg == "--fresh":
            fresh = True
        else:
            module_filter = arg

    asyncio.run(run_seeders(module_filter=module_filter, fresh=fresh))
