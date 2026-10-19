from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gymflow.db import Base

if TYPE_CHECKING:
    from gymflow.models.socio import Socio


class Membresia(Base):
    __tablename__ = "membresias"

    id: Mapped[int] = mapped_column(primary_key=True)
    socio_id: Mapped[int] = mapped_column(ForeignKey("socios.id", ondelete="CASCADE"), index=True)
    tipo: Mapped[str] = mapped_column(String(30))  # mensual | trimestral | anual
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date] = mapped_column(Date)
    precio: Mapped[float] = mapped_column(Numeric(10, 2))
    activa: Mapped[bool] = mapped_column(Boolean, default=True)

    socio: Mapped[Socio] = relationship(back_populates="membresias")
