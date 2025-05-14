import os
import subprocess
import re
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import socket
import tkinter as tk
from tkinter import filedialog, messagebox
import time

# ------------------ CONFIGURACIÓN ------------------
ips = {
    'KRPM': '25.59.202.144',
    'DAVID': '25.23.33.99',
    'IVAN': '25.59.204.21'
}

ancho_banda = {
    ('KRPM', 'IVAN'): 15.9, ('IVAN', 'KRPM'): 15.7,
    ('KRPM', 'DAVID'): 6.18, ('DAVID', 'KRPM'): 5.95,
    ('DAVID', 'IVAN'): 8.81, ('IVAN', 'DAVID'): 8.58
}

latencias_conocidas = {
    ('IVAN', 'KRPM'): 6,
    ('DAVID', 'KRPM'): 17,
    ('KRPM', 'DAVID'): 200,
}

# Cambiar según el nodo local donde se corre este script
nodo_local = 'KRPM'

# ------------------ FUNCIONES ------------------
def ping_latency(ip):
    try:
        result = subprocess.run(["ping", ip, "-n", "4"], capture_output=True, text=True, encoding='cp1252')
        output = result.stdout
        match = re.search(r"(Average|Promedio|Media)[^\d]*(\d+)\s*ms", output)
        return int(match.group(2)) if match else None
    except Exception as e:
        print(f"Error al hacer ping a {ip}: {e}")
        return None

def enviar_archivo(ip_destino, ruta_archivo, puerto=5001):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip_destino, puerto))

            # 1. Enviar el nombre del archivo (con extensión), seguido de '\n' como separador
            nombre_archivo = os.path.basename(ruta_archivo)
            s.sendall((nombre_archivo + '\n').encode())

            # 2. Enviar el contenido del archivo en binario
            with open(ruta_archivo, 'rb') as f:
                while chunk := f.read(4096):
                    s.sendall(chunk)

        print(f"Archivo '{nombre_archivo}' enviado a {ip_destino}")
        return True
    except Exception as e:
        print(f"Error al enviar archivo a {ip_destino}: {e}")
        return False

def medir_transferencia(ip_destino, ruta_archivo):
    inicio = time.time()
    exito = enviar_archivo(ip_destino, ruta_archivo)
    fin = time.time()
    return (exito, round(fin - inicio, 2))

# ------------------ GRAFO ------------------
G = nx.DiGraph()
for nodo in ips:
    G.add_node(nodo)

for origen, ip_origen in ips.items():
    for destino, ip_destino in ips.items():
        if origen != destino:
            latency = latencias_conocidas.get((origen, destino)) or ping_latency(ip_destino)
            bandwidth = ancho_banda.get((origen, destino), 'N/A')
            if latency is not None:
                G.add_edge(origen, destino, latency=latency, bandwidth=bandwidth)

print("\nTabla de Métricas:")
print("{:<10} {:<10} {:<10} {:<15}".format("Origen", "Destino", "Latencia", "Ancho de Banda"))
print("-" * 50)
for u, v, d in G.edges(data=True):
    print("{:<10} {:<10} {:<10} {:<15}".format(u, v, f"{d['latency']} ms", f"{d['bandwidth']} Mbps"))

# ------------------ VISUALIZACIÓN ------------------
plt.figure(figsize=(10, 8))
pos = nx.circular_layout(G)
nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=2500, edgecolors='black')
nx.draw_networkx_labels(G, pos, font_weight='bold', font_size=12)

def get_label_position(pos_u, pos_v, rad=0):
    if rad == 0:
        return 0.7 * pos_u + 0.3 * pos_v
    else:
        middle = 0.5 * pos_u + 0.5 * pos_v
        direction = np.array([pos_v[1]-pos_u[1], pos_u[0]-pos_v[0]])
        return middle + 0.2 * direction / np.linalg.norm(direction)

edge_labels = {}
for (u, v, d) in G.edges(data=True):
    rad = 0.2 if (v, u) in G.edges else 0.0
    nx.draw_networkx_edges(
        G, pos, edgelist=[(u, v)],
        arrowstyle='-|>', arrowsize=20,
        connectionstyle=f'arc3,rad={rad}',
        edge_color='gray', width=2, node_size=2500
    )
    label_pos = get_label_position(pos[u], pos[v], rad)
    edge_labels[(u, v)] = {
        'label': f"L:{d['latency']}ms B:{d['bandwidth']}Mbps",
        'position': label_pos
    }

for (u, v), data in edge_labels.items():
    plt.text(
        data['position'][0], data['position'][1],
        data['label'],
        bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.3'),
        fontsize=9, ha='center', va='center'
    )

plt.title("Grafo VPN - Latencia (L) y Ancho de Banda (B)", pad=20)
plt.axis('off')
plt.tight_layout()
plt.ion()              
plt.show(block=False)  

# ------------------ GUI ------------------
def seleccionar_archivo():
    archivo = filedialog.askopenfilename()
    if archivo:
        entry_archivo.delete(0, tk.END)
        entry_archivo.insert(0, archivo)
        label_nombre_archivo.config(text=f"Archivo: {os.path.basename(archivo)}")

def mostrar_topologia_mst():
    plt.close('all')

    # Crear grafo no dirigido para Kruskal
    G_bw = nx.Graph()
    for (u, v), bw in ancho_banda.items():
        if isinstance(bw, (int, float)):
            # Usamos el inverso del ancho de banda como peso para obtener el MST que maximice el ancho de banda
            costo = 1 / bw
            G_bw.add_edge(u, v, weight=costo, bandwidth=bw)

    # Aplicar algoritmo de Kruskal
    mst = nx.minimum_spanning_tree(G_bw, algorithm='kruskal')
    
    # Calcular métricas de comparación
    bw_original = sum(d['bandwidth'] for u, v, d in G_bw.edges(data=True))
    bw_mst = sum(d['bandwidth'] for u, v, d in mst.edges(data=True))
    eficiencia = (bw_mst / bw_original) * 100

    # Crear figura con dos subplots
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    pos = nx.spring_layout(G_bw, seed=42)

    # Dibujar topología original
    nx.draw(G_bw, pos, ax=axes[0], with_labels=True, 
            node_color='lightblue', edge_color='gray', node_size=2000)
    labels_full = {(u, v): f"{d['bandwidth']} Mbps" for u, v, d in G_bw.edges(data=True)}
    nx.draw_networkx_edge_labels(G_bw, pos, edge_labels=labels_full, ax=axes[0])
    axes[0].set_title(f"Topología Original\nAncho de banda total: {bw_original:.2f} Mbps")

    # Dibujar MST resultante
    nx.draw(mst, pos, ax=axes[1], with_labels=True, 
            node_color='lightgreen', edge_color='black', node_size=2000)
    labels_mst = {(u, v): f"{d['bandwidth']} Mbps" for u, v, d in mst.edges(data=True)}
    nx.draw_networkx_edge_labels(mst, pos, edge_labels=labels_mst, ax=axes[1])
    axes[1].set_title(f"Topología Eficiente (Kruskal)\nAncho de banda total: {bw_mst:.2f} Mbps\nEficiencia: {eficiencia:.1f}%")

    plt.tight_layout()
    plt.show(block=False)

def transferir():
    destino = combo_nodos.get()
    archivo = entry_archivo.get()
    criterio = criterio_opt.get()

    if not archivo or not destino or destino not in ips or destino == nodo_local:
        label_resultado.config(text="Error: Selecciona un archivo y destino válido", fg="red")
        return

    try:
        # Configurar pesos según criterio
        if criterio == 'latency':
            peso = 'latency'
            mensaje = "Menor latencia"
        else:
            for u, v, d in G.edges(data=True):
                if d.get('bandwidth') and isinstance(d['bandwidth'], (int, float)):
                    d['inv_bw'] = 1 / d['bandwidth']
                else:
                    d['inv_bw'] = float('inf')
            peso = 'inv_bw'
            mensaje = "Mayor ancho de banda"

        # Calcular ruta óptima
        ruta_optima = nx.dijkstra_path(G, nodo_local, destino, weight=peso)
        ruta_ips_optima = [ips[n] for n in ruta_optima[1:]]

        # === Ruta directa (latencia directa sin Dijkstra) ===
        latencia_directa = G[nodo_local][destino]['latency']

        # Calcular ruta directa
        ruta_directa = [destino]
        ruta_ips_directa = [ips[destino]]

        # Medir tiempos
        tiempo_optimo = 0
        for ip in ruta_ips_optima:
            _, t = medir_transferencia(ip, archivo)
            tiempo_optimo += t

        tiempo_directo = 0
        for ip in ruta_ips_directa:
            _, t = medir_transferencia(ip, archivo)
            tiempo_directo += t

        # Mostrar resultados
        resultado = (
            f"Transferencia completada - Criterio: {mensaje}\n"
            f"Ruta óptima: {' -> '.join(ruta_optima)}\n"
            f"Tiempo ruta óptima: {tiempo_optimo:.2f} s\n"
            f"Ruta directa: {nodo_local} -> {destino}\n"
            f"Latencia de ruta directa: {latencia_directa} ms"
        )
        
        label_resultado.config(text=resultado, fg="green")

    except Exception as e:
        print(f"Error durante la transferencia: {e}")
        label_resultado.config(text=f"Transferencia completada con posibles errores: {str(e)}", fg="orange")

# ------------------ INTERFAZ GRÁFICA ------------------
root = tk.Tk()
root.title("File Transfer Optimizer")
root.geometry("500x650")

# Estilos
font_style = ('Arial', 10)
title_style = ('Arial', 12, 'bold')

# Sección de archivo
tk.Label(root, text="Transferencia de Archivos", font=title_style).pack(pady=5)
tk.Label(root, text="Seleccionar archivo:", font=font_style).pack()
entry_archivo = tk.Entry(root, width=50, font=font_style)
entry_archivo.pack()
tk.Button(root, text="Buscar", command=seleccionar_archivo, font=font_style).pack(pady=5)
label_nombre_archivo = tk.Label(root, text="", font=font_style)
label_nombre_archivo.pack()

# Sección de destino
tk.Label(root, text="Seleccionar destino:", font=font_style).pack(pady=5)
combo_nodos = tk.StringVar(value="Seleccione un nodo")
menu = tk.OptionMenu(root, combo_nodos, *[n for n in ips if n != nodo_local])
menu.config(width=20, font=font_style)
menu.pack()
label_destino_seleccionado = tk.Label(root, text="Destino: Ninguno seleccionado", font=font_style, fg="blue")
label_destino_seleccionado.pack()

def actualizar_destino_seleccionado(*args):
    destino = combo_nodos.get()
    if destino in ips:
        label_destino_seleccionado.config(text=f"Destino seleccionado: {destino}", fg="green")
    else:
        label_destino_seleccionado.config(text="Destino: Ninguno seleccionado", fg="blue")

combo_nodos.trace("w", actualizar_destino_seleccionado)

# Sección de criterios
tk.Label(root, text="Criterio de optimización:", font=font_style).pack(pady=5)
criterio_opt = tk.StringVar(value='latency')
tk.Radiobutton(root, text="Menor latencia", variable=criterio_opt, value='latency', font=font_style).pack()
tk.Radiobutton(root, text="Mayor ancho de banda", variable=criterio_opt, value='bandwidth', font=font_style).pack()

# Botón de transferencia
tk.Button(root, text="Transferir Archivo", command=transferir, 
          font=('Arial', 12, 'bold'), bg='#4CAF50', fg='white').pack(pady=10)

# Botón de topología
tk.Button(root, text="Mostrar Topología MST", command=mostrar_topologia_mst,
          font=('Arial', 12, 'bold'), bg='#2196F3', fg='white').pack(pady=10)

# Sección de resultados
tk.Label(root, text="Resultados:", font=title_style).pack()
label_resultado = tk.Label(root, text="", font=font_style, wraplength=450, justify=tk.LEFT)
label_resultado.pack(pady=10)

root.mainloop()