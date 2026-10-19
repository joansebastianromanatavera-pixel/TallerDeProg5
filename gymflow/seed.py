"""Optional seed data. Run with: python -m gymflow.seed"""

from datetime import date, timedelta

from sqlalchemy import select

from gymflow.db import Base, SessionLocal, engine
from gymflow.models import Ejercicio, Membresia, Rutina, Socio


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(Socio.id).limit(1)) is not None:
            print("The database already has data; seed skipped.")
            return

        today = date.today()

        laura = Socio(nombre="Laura Gómez", email="laura.gomez@example.com", telefono="+57 300 123 4567")
        laura.membresias.append(
            Membresia(tipo="mensual", fecha_inicio=today, fecha_fin=today + timedelta(days=30), precio=120000)
        )
        upper = Rutina(nombre="Fuerza tren superior", objetivo="fuerza", nivel="intermedio")
        upper.ejercicios = [
            Ejercicio(nombre="Press de banca", grupo_muscular="pecho", series=4, repeticiones=8,
                      descripcion="Empuje horizontal con barra; controla la bajada hasta el pecho."),
            Ejercicio(nombre="Remo con barra", grupo_muscular="espalda", series=4, repeticiones=10,
                      descripcion="Tirón horizontal manteniendo la espalda neutra."),
            Ejercicio(nombre="Press militar", grupo_muscular="hombros", series=3, repeticiones=10,
                      descripcion="Empuje vertical de pie con barra o mancuernas."),
        ]
        laura.rutinas.append(upper)

        andres = Socio(nombre="Andrés Pérez", email="andres.perez@example.com", telefono="+57 311 987 6543")
        andres.membresias.append(
            Membresia(tipo="anual", fecha_inicio=today - timedelta(days=200),
                      fecha_fin=today + timedelta(days=165), precio=1100000)
        )
        legs = Rutina(nombre="Pierna y core", objetivo="hipertrofia", nivel="principiante")
        legs.ejercicios = [
            Ejercicio(nombre="Sentadilla", grupo_muscular="piernas", series=4, repeticiones=12,
                      descripcion="Sentadilla con barra; rodillas en línea con los pies."),
            Ejercicio(nombre="Peso muerto rumano", grupo_muscular="isquiotibiales", series=3, repeticiones=10,
                      descripcion="Bisagra de cadera con piernas semiextendidas."),
            Ejercicio(nombre="Plancha", grupo_muscular="core", series=3, repeticiones=1,
                      descripcion="Mantener 45 segundos con el cuerpo alineado."),
            Ejercicio(nombre="Flexiones", grupo_muscular="pecho", series=3, repeticiones=15,
                      descripcion="Empuje con peso corporal, codos a 45 grados."),
        ]
        andres.rutinas.append(legs)

        sofia = Socio(nombre="Sofía Martínez", email="sofia.martinez@example.com", activo=False)
        sofia.membresias.append(
            Membresia(tipo="trimestral", fecha_inicio=today - timedelta(days=120),
                      fecha_fin=today - timedelta(days=30), precio=330000, activa=False)
        )

        db.add_all([laura, andres, sofia])
        db.commit()
        print("Seed data inserted: 3 members, 3 memberships, 2 routines, 7 exercises.")


if __name__ == "__main__":
    seed()
