import socket

def start_server(ip, puerto=5001):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((ip, puerto))
        s.listen()
        print(f"Servidor escuchando en {ip}:{puerto}")
        
        conn, addr = s.accept()
        with conn:
            print(f"Conexión desde {addr}")

            #Paso 1: Recibir el nombre del archivo (hasta '\n')
            nombre_archivo = b""
            while not nombre_archivo.endswith(b'\n'):
                nombre_archivo += conn.recv(1)
            nombre_archivo = nombre_archivo.strip().decode()

            #Paso 2: Recibir y guardar el contenido del archivo
            with open(nombre_archivo, "wb") as f:
                while True:
                    datos = conn.recv(4096)
                    if not datos:
                        break
                    f.write(datos)

            print(f"Archivo '{nombre_archivo}' recibido correctamente.")

# IP local del nodo (ajústalo según el nodo en el que se ejecuta)
start_server("25.59.202.144")  # ejemplo: KRPM