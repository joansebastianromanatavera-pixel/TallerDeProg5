from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gymflow.db import Base

if TYPE_CHECKING:
    from gymflow.models.membresia import Membresia
    from gymflow.models.rutina import Rutina


class Socio(Base):
    __tablename__ = "socios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    telefono: Mapped[str | None] = mapped_column(String(20), default=None)
    fecha_registro: Mapped[date] = mapped_column(Date, default=date.today)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    membresias: Mapped[list[Membresia]] = relationship(
        back_populates="socio", cascade="all, delete-orphan"
    )
    rutinas: Mapped[list[Rutina]] = relationship(
        back_populates="socio", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Socio(id={self.id!r}, email={self.email!r})"
