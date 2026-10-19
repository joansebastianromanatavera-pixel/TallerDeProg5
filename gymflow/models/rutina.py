from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gymflow.db import Base

if TYPE_CHECKING:
    from gymflow.models.ejercicio import Ejercicio
    from gymflow.models.socio import Socio


class Rutina(Base):
    __tablename__ = "rutinas"

    id: Mapped[int] = mapped_column(primary_key=True)
    socio_id: Mapped[int] = mapped_column(ForeignKey("socios.id", ondelete="CASCADE"), index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    objetivo: Mapped[str] = mapped_column(String(100))  # hipertrofia, fuerza, resistencia...
    nivel: Mapped[str] = mapped_column(String(30))  # principiante | intermedio | avanzado

    socio: Mapped[Socio] = relationship(back_populates="rutinas")
    ejercicios: Mapped[list[Ejercicio]] = relationship(
        back_populates="rutina", cascade="all, delete-orphan"
    )
