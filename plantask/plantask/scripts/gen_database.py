#WARNING: !!!!!!!!

#DO NOT USE THIS SCRIPT IF ITS NOT 100% NECESSARY!!!!!!!
#THIS SCRIPT IS FOR TESTING PURPOSES ONLY AND MAY CAUSE UNEXPECTED BEHAVIOR IN THE DATABASE
#OR THE APPLICATION ITSELF.
#USE AT YOUR OWN RISK!!!!!!!
#THIS SCRIPT IS NOT SUPPORTED BY THE APPLICATION AND MAY CAUSE DATA LOSS OR CORRUPTION.
#USE AT YOUR OWN RISK!!!!!!!

from sqlalchemy import create_engine, MetaData
from sqlalchemy.schema import CreateTable

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from plantask.models.base import Base

engine = create_engine("postgresql://docker_user:Plantaskwawawa@3.133.125.109:5432/plantask_db", echo=True)

def crear_tablas():
    """Crea las tablas definidas en los modelos directamente en la base de datos."""
    Base.metadata.create_all(engine)
    print("✅ Las tablas han sido creadas en la base de datos.")

def mostrar_sql():
    """Muestra el código SQL (DDL) que SQLAlchemy generaría para las tablas."""
    print("\n📄 Código SQL generado por SQLAlchemy:")
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(engine))
        print(f"\n-- Tabla: {table.name}\n{ddl}\n")

def main():
    print("=== Menú de opciones ===")
    print("1. Crear tablas en la base de datos")
    print("2. Mostrar SQL generado sin ejecutar")
    print("0. Salir")

    opcion = input("\nSelecciona una opción: ")

    if opcion == "1":
        crear_tablas()
    elif opcion == "2":
        mostrar_sql()
    elif opcion == "0":
        print("👋 Saliendo...")
    else:
        print("❌ Opción no válida.")

if __name__ == "__main__":
    main()