from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gymflow.db import Base

if TYPE_CHECKING:
    from gymflow.models.rutina import Rutina


class Ejercicio(Base):
    __tablename__ = "ejercicios"

    id: Mapped[int] = mapped_column(primary_key=True)
    rutina_id: Mapped[int] = mapped_column(ForeignKey("rutinas.id", ondelete="CASCADE"), index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    grupo_muscular: Mapped[str] = mapped_column(String(50))
    series: Mapped[int]
    repeticiones: Mapped[int]
    descripcion: Mapped[str | None] = mapped_column(Text, default=None)

    rutina: Mapped[Rutina] = relationship(back_populates="ejercicios")
