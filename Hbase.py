import happybase
import pandas as pd
from datetime import datetime

# Bloque principal de ejecución
try:
    # 1. Establecer conexión con HBase
    connection = happybase.Connection('localhost')
    print("Conexión establecida con HBase")

    # 2. Crear la tabla con las familias de columnas
    table_name = 'used_cars'
    families = {
        'basic': dict(),  # información básica del coche
        'specs': dict(),  # especificaciones técnicas
        'sales': dict(),  # información de venta
        'condition': dict()  # estado del vehículo
    }

    # Eliminar la tabla si ya existe
    if table_name.encode() in connection.tables():
        print(f"Eliminando tabla existente - {table_name}")
        connection.delete_table(table_name, disable=True)

    # Crear nueva tabla
    connection.create_table(table_name, families)
    table = connection.table(table_name)
    print("Tabla 'used_cars' creada exitosamente")

    # 3. Cargar datos del CSV
    car_data = pd.read_csv('Car_details_v3.csv')

    # Iterar sobre el DataFrame usando el índice
    for index, row in car_data.iterrows():
        # Generar row key basado en el índice
        row_key = f'car_{index}'.encode()

        # Organizar los datos en familias de columnas
        data = {
            b'basic:name': str(row['name']).encode(),
            b'basic:year': str(row['year']).encode(),
            b'basic:transmission': str(row['transmission']).encode(),
            b'basic:fuel': str(row['fuel']).encode(),
            b'specs:engine': str(row['engine']).encode(),
            b'specs:max_power': str(row['max_power']).encode(),
            b'specs:torque': str(row['torque']).encode(),
            b'specs:seats': str(row['seats']).encode(),
            b'specs:mileage': str(row['mileage']).encode(),
            b'sales:selling_price': str(row['selling_price']).encode(),
            b'sales:seller_type': str(row['seller_type']).encode(),
            b'condition:km_driven': str(row['km_driven']).encode(),
            b'condition:owner': str(row['owner']).encode()
        }
        table.put(row_key, data)

    print("Datos cargados exitosamente")

    # 4. Consultas y análisis de datos
    print("\n=== Todos los coches en la base de datos (primeros 3) ===")
    count = 0
    for key, data in table.scan():
        if count < 3:  # Limitamos a 3 para el ejemplo
            print(f"\nCoche ID: {key.decode()}")
            print(f"Nombre: {data[b'basic:name'].decode()}")
            print(f"Año: {data[b'basic:year'].decode()}")
            print(f"Precio: {data[b'sales:selling_price'].decode()}")
            count += 1

    # 5. Encontrar coches por rango de precio
    print("\n=== Coches con precio menor a 50000 ===")
    for key, data in table.scan():
        if int(data[b'sales:selling_price'].decode()) < 50000:
            print(f"\nCoche ID: {key.decode()}")
            print(f"Nombre: {data[b'basic:name'].decode()}")
            print(f"Precio: {data[b'sales:selling_price'].decode()}")

    # 6. Análisis de propietarios
    print("\n=== Coches por tipo de propietario ===")
    owner_stats = {}
    for key, data in table.scan():
        owner = data[b'condition:owner'].decode()
        owner_stats[owner] = owner_stats.get(owner, 0) + 1
    for owner, count in owner_stats.items():
        print(f"{owner}: {count} coches")

    # 7. Análisis de precios por tipo de combustible
    print("\n=== Precio promedio por tipo de combustible ===")
    fuel_prices = {}
    fuel_counts = {}
    for key, data in table.scan():
        fuel = data[b'basic:fuel'].decode()
        price = int(data[b'sales:selling_price'].decode())
        fuel_prices[fuel] = fuel_prices.get(fuel, 0) + price
        fuel_counts[fuel] = fuel_counts.get(fuel, 0) + 1
    for fuel in fuel_prices:
        avg_price = fuel_prices[fuel] / fuel_counts[fuel]
        print(f"{fuel}: {avg_price:.2f}")

    # 8. Top 3 coches con mayor kilometraje
    print("\n=== Top 3 coches con mayor kilometraje ===")
    cars_by_km = []
    for key, data in table.scan():
        cars_by_km.append({
            'id': key.decode(),
            'name': data[b'basic:name'].decode(),
            'km': int(data[b'condition:km_driven'].decode()),
            'price': int(data[b'sales:selling_price'].decode())
        })
    for car in sorted(cars_by_km, key=lambda x: x['km'], reverse=True)[:3]:
        print(f"ID: {car['id']}")
        print(f"Nombre: {car['name']}")
        print(f"Kilometraje: {car['km']}")
        print(f"Precio: {car['price']}\n")

    # 9. Análisis de precios por tipo de transmisión
    print("\n=== Precio promedio por tipo de transmisión ===")
    transmission_prices = {}
    transmission_counts = {}
    for key, data in table.scan():
        trans = data[b'basic:transmission'].decode()
        price = int(data[b'sales:selling_price'].decode())
        transmission_prices[trans] = transmission_prices.get(trans, 0) + price
        transmission_counts[trans] = transmission_counts.get(trans, 0) + 1
    for trans in transmission_prices:
        avg_price = transmission_prices[trans] / transmission_counts[trans]
        print(f"{trans}: {avg_price:.2f}")

    # --- Nuevas funcionalidades integradas ---

    # Selección de datos: mostrar un coche específico por ID
    car_id = 'car_5'
    print(f"\n=== Información del coche con ID: {car_id} ===")
    car_data = table.row(car_id.encode())
    if car_data:
        for column, value in car_data.items():
            print(f"{column.decode()}: {value.decode()}")
    else:
        print(f"No se encontró el coche con ID {car_id}")

    # Filtrado: coches con transmisión automática
    print("\n=== Coches con transmisión automática ===")
    for key, data in table.scan():
        if data[b'basic:transmission'].decode().lower() == 'automatic':
            print(f"Coche ID: {key.decode()} - Nombre: {data[b'basic:name'].decode()}")

    # Inserción: añadir nuevo coche
    new_car_id = 'car_1000'
    new_car_data = {
        b'basic:name': b'Test Car',
        b'basic:year': b'2024',
        b'basic:transmission': b'Automatic',
        b'basic:fuel': b'Petrol',
        b'sales:selling_price': b'500000'
    }
    table.put(new_car_id.encode(), new_car_data)
    print(f"\nNuevo coche insertado con ID: {new_car_id}")

    # Actualización: cambiar precio de un coche
    table.put(new_car_id.encode(), {b'sales:selling_price': b'450000'})
    print(f"Precio del coche {new_car_id} actualizado a 450000")

    # Eliminación: borrar coche
    table.delete(new_car_id.encode())
    print(f"Coche con ID {new_car_id} eliminado")

except Exception as e:
    print(f"Error: {str(e)}")

finally:
    connection.close()
