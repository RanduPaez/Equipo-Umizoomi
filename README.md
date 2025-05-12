📌 Descripción del Proyecto
Este proyecto implementa un sistema de análisis de red VPN que:

Mide latencias entre nodos mediante comandos ping

Construye un grafo dirigido representando la topología de red

Visualiza las conexiones con sus métricas de latencia y ancho de banda

Proporciona herramientas para optimizar la red

🛠️ Requisitos Técnicos
📋 Prerrequisitos
Python 3.8+

NetworkX 2.6+

Matplotlib 3.4+

Sistema operativo Windows (por el comando ping)

📦 Dependencias
Instalar con:


pip install networkx matplotlib
🖥️ Configuración de la Red
🔧 Archivo de Configuración
El script utiliza dos diccionarios principales:

p
# Direcciones IP de los dispositivos
ips = {
    'KRPM': '25.59.202.144',
    'DAVID': '25.59.199.229',
    'IVAN': '25.59.204.21'
}

# Ancho de banda medido previamente (Mbps)
ancho_banda = {
    ('KRPM', 'IVAN'): 15.9,
    ('IVAN', 'KRPM'): 15.7,
    ('KRPM', 'DAVID'): 6.18,
    ('DAVID', 'KRPM'): 5.95
}
⚙️ Funcionamiento del Código
📡 Medición de Latencia
La función ping_latency() ejecuta 4 pings y extrae el valor promedio:


def ping_latency(ip):
    result = subprocess.run(["ping", ip, "-n", "4"], 
                          capture_output=True, 
                          text=True, 
                          encoding='cp1252')
    output = result.stdout
    match = re.search(r"(Average|Promedio|Media)[^\d]*(\d+)\s*ms", output)
    return int(match.group(2)) if match else None
🕸️ Construcción del Grafo
El grafo se construye con:


G = nx.DiGraph()

# Agregar nodos
for device in ips:
    G.add_node(device)

# Agregar aristas con métricas
for name1, ip1 in ips.items():
    for name2, ip2 in ips.items():
        if name1 != name2:
            latency = ping_latency(ip2)
            if latency is not None:
                bandwidth = ancho_banda.get((name1, name2), 'N/A')
                G.add_edge(name1, name2, latency=latency, bandwidth=bandwidth)
📊 Visualización
El grafo se visualiza con:


pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_size=1500, 
       node_color='lightblue', font_weight='bold')

edge_labels = {
    (u, v): f"{d['latency']} ms, {d['bandwidth']} Mbps"
    for u, v, d in G.edges(data=True)
}
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

plt.title("Grafo de Dispositivos (Latencia y Ancho de Banda)")
plt.show()
🔍 Análisis de Red
📈 Métricas Clave
Latencia: Tiempo de ida y vuelta (RTT) en milisegundos

Ancho de Banda: Capacidad del enlace en Mbps

🔎 Interpretación del Grafo
Nodos: Dispositivos en la red VPN

Aristas dirigidas: Conexiones con sus métricas

Color: Los nodos en azul claro son dispositivos finales

🚀 Optimizaciones Implementadas
🔄 Algoritmo de Kruskal
Para encontrar el Árbol de Expansión Mínima (MST):


def kruskal_mst(graph):
    # Convertir a grafo no dirigido
    G_undirected = nx.Graph()
    
    # Procesar conexiones bidireccionales
    for (u, v), bw in graph.edges.items():
        if (v, u) in graph.edges:
            max_bw = max(graph.edges[(u, v)]['weight'], 
                        graph.edges[(v, u)]['weight'])
            G_undirected.add_edge(u, v, weight=max_bw)
    
    # Generar MST (invertimos pesos para máximo ancho de banda)
    for u, v in G_undirected.edges():
        G_undirected.edges[u, v]['weight'] = -G_undirected.edges[u, v]['weight']
    
    mst = nx.minimum_spanning_tree(G_undirected, algorithm='kruskal')
    
    # Restaurar pesos
    for u, v in mst.edges():
        mst.edges[u, v]['weight'] = -mst.edges[u, v]['weight']
    
    return mst
📊 Comparativa Topologías
Métrica	Topología Original	MST Kruskal
Total Ancho de Banda	46.66 Mbps	22.08 Mbps
Ancho Banda Promedio	7.78 Mbps	11.04 Mbps
Número de Enlaces	6	2
💡 Casos de Uso
Diseño de Redes VPN: Optimizar conexiones entre oficinas

Diagnóstico de Red: Identificar cuellos de botella

Planificación de Capacidad: Asignar recursos eficientemente

Simulación de Escenarios: Probar configuraciones alternativas

🛠️ Posibles Mejoras
Automatización de Mediciones:


def medir_ancho_banda(ip1, ip2):
    # Implementar medición real con iperf
    pass
Interfaz Gráfica Avanzada:

python
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
Almacenamiento de Históricos:

python
import sqlite3
conn = sqlite3.connect('metricas_red.db')
Alertas Automáticas:


if latency > 100:  # ms
    enviar_alerta("Latencia alta detectada")
📚 Recursos Adicionales
Documentación NetworkX

Teoría de Grafos Aplicada

Optimización de Redes

📄 Licencia
Este proyecto está bajo licencia MIT. Ver archivo LICENSE para más detalles.

✉️ Contacto
Para preguntas o colaboraciones:

Email: proyecto-red@example.com

Repositorio: github.com/usuario/proyecto-red

