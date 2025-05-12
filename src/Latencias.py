import subprocess
import re
import networkx as nx
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import time
from queue import Queue

class NetworkTransferApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Transferencia de Archivos Optimizada")
        
        # Datos de la red
        self.ips = {
            'KRPM': '25.59.202.144',
            'DAVID': '25.59.199.229',
            'IVAN': '25.59.204.21'
        }
        
        self.ancho_banda = {
            ('KRPM', 'IVAN'): 15.9,
            ('IVAN', 'KRPM'): 15.7,
            ('KRPM', 'DAVID'): 6.18,
            ('DAVID', 'KRPM'): 5.95
        }
        
        # Construir el grafo de red
        self.G = self.construir_grafo_red()
        
        # Variables de la GUI
        self.selected_files = []
        self.transfer_queue = Queue()
        self.transfer_in_progress = False
        
        # Crear widgets
        self.create_widgets()
        
        # Iniciar hilo para procesar transferencias
        self.start_transfer_thread()
    
    def construir_grafo_red(self):
        """Construye el grafo de red con latencias y anchos de banda."""
        G = nx.DiGraph()
        
        for name1, ip1 in self.ips.items():
            for name2, ip2 in self.ips.items():
                if name1 != name2:
                    latencia = self.ping_latency(ip2)
                    bw = self.ancho_banda.get((name1, name2), None)
                    G.add_edge(name1, name2, latencia=latencia, ancho_banda=bw)
        
        return G
    
    def ping_latency(self, ip):
        """Mide la latencia mediante ping."""
        try:
            result = subprocess.run(["ping", ip, "-n", "4"], capture_output=True, text=True, encoding='cp1252')
            output = result.stdout
            
            match = re.search(r"(Average|Promedio|Media)[^\d]*(\d+)\s*ms", output)
            return int(match.group(2)) if match else 1000  # Valor alto si falla
        except:
            return 1000
    
    def encontrar_ruta_optima(self, origen, destino, criterio='latencia'):
        """Encuentra la ruta óptima usando Dijkstra según el criterio especificado."""
        if criterio == 'latencia':
            # Usar latencia como peso (minimizar)
            return nx.dijkstra_path(self.G, origen, destino, weight='latencia')
        elif criterio == 'ancho_banda':
            # Usar ancho de banda inverso como peso (maximizar ancho de banda)
            # Creamos un grafo temporal con pesos inversos
            temp_G = self.G.copy()
            for u, v, d in temp_G.edges(data=True):
                if d['ancho_banda']:
                    d['weight'] = 1 / d['ancho_banda']
                else:
                    d['weight'] = float('inf')  # Valor muy alto si no hay ancho de banda
            return nx.dijkstra_path(temp_G, origen, destino, weight='weight')
    
    def estimar_tiempo_transferencia(self, ruta, tamaño_archivo):
        """Estima el tiempo de transferencia para la ruta dada."""
        ancho_minimo = float('inf')
        latencia_total = 0
        
        # Calcular el cuello de botella de ancho de banda y latencia total
        for i in range(len(ruta)-1):
            u, v = ruta[i], ruta[i+1]
            bw = self.G[u][v]['ancho_banda']
            if bw and bw < ancho_minimo:
                ancho_minimo = bw
            
            latencia_total += self.G[u][v]['latencia']
        
        if ancho_minimo == float('inf'):
            return float('inf')
        
        # Tiempo = tamaño/velocidad + latencia (simplificado)
        tiempo = (tamaño_archivo * 8) / (ancho_minimo * 1e6) + (latencia_total / 1000)
        return tiempo
    
    def transferir_archivo(self, origen, destino, ruta, archivo):
        """Simula la transferencia de un archivo a través de la ruta óptima."""
        tamaño = os.path.getsize(archivo) / (1024 * 1024)  # Tamaño en MB
        tiempo_estimado = self.estimar_tiempo_transferencia(ruta, tamaño)
        
        # Simular transferencia (en una aplicación real aquí se implementaría la transferencia real)
        tiempo_inicio = time.time()
        for i in range(101):
            time.sleep(tiempo_estimado / 100)
            self.transfer_queue.put(('progress', i, os.path.basename(archivo), ruta))
        
        self.transfer_queue.put(('complete', os.path.basename(archivo), ruta, tiempo_estimado))
    
    def create_widgets(self):
        """Crea los elementos de la interfaz gráfica."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Selección de archivos
        ttk.Label(main_frame, text="Archivos a transferir:").grid(row=0, column=0, sticky=tk.W)
        self.file_listbox = tk.Listbox(main_frame, height=5, selectmode=tk.MULTIPLE)
        self.file_listbox.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Button(main_frame, text="Agregar archivos", 
                  command=self.add_files).grid(row=2, column=0, sticky=tk.W)
        ttk.Button(main_frame, text="Quitar seleccionados", 
                  command=self.remove_files).grid(row=2, column=1, sticky=tk.W)
        
        # Selección de destino
        ttk.Label(main_frame, text="Destino:").grid(row=3, column=0, sticky=tk.W)
        self.destino_var = tk.StringVar()
        destino_menu = ttk.OptionMenu(main_frame, self.destino_var, *list(self.ips.keys()))
        destino_menu.grid(row=3, column=1, sticky=tk.W)
        
        # Criterio de optimización
        ttk.Label(main_frame, text="Criterio de optimización:").grid(row=4, column=0, sticky=tk.W)
        self.criterio_var = tk.StringVar(value='latencia')
        ttk.Radiobutton(main_frame, text="Minimizar latencia", variable=self.criterio_var, 
                        value='latencia').grid(row=5, column=0, sticky=tk.W)
        ttk.Radiobutton(main_frame, text="Maximizar ancho de banda", variable=self.criterio_var, 
                        value='ancho_banda').grid(row=5, column=1, sticky=tk.W)
        
        # Botón de transferencia
        ttk.Button(main_frame, text="Iniciar Transferencia", 
                  command=self.start_transfer).grid(row=6, column=0, columnspan=2, pady=10)
        
        # Barra de progreso
        self.progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress_bar.grid(row=7, column=0, columnspan=2, pady=5)
        
        # Área de información
        self.info_text = tk.Text(main_frame, height=10, width=50, state=tk.DISABLED)
        self.info_text.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Configurar expansión de columnas
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Mostrar grafo de red
        self.mostrar_grafo_red()
    
    def add_files(self):
        """Abre diálogo para agregar archivos a la lista."""
        files = filedialog.askopenfilenames(title="Seleccionar archivos para transferir")
        if files:
            for f in files:
                self.file_listbox.insert(tk.END, f)
            self.selected_files = list(self.file_listbox.get(0, tk.END))
    
    def remove_files(self):
        """Elimina archivos seleccionados de la lista."""
        selected_indices = self.file_listbox.curselection()
        for i in reversed(selected_indices):
            self.file_listbox.delete(i)
        self.selected_files = list(self.file_listbox.get(0, tk.END))
    
    def start_transfer(self):
        """Inicia el proceso de transferencia."""
        if not self.selected_files:
            messagebox.showerror("Error", "No hay archivos seleccionados para transferir")
            return
        
        destino = self.destino_var.get()
        if not destino:
            messagebox.showerror("Error", "No se ha seleccionado un destino")
            return
        
        # Obtener el nombre del host local (simplificado - en realidad habría que detectarlo)
        origen = list(self.ips.keys())[0]  # Esto es una simplificación
        
        criterio = self.criterio_var.get()
        
        # Encontrar ruta óptima para cada archivo y encolar transferencias
        for archivo in self.selected_files:
            try:
                ruta = self.encontrar_ruta_optima(origen, destino, criterio)
                if not ruta:
                    messagebox.showerror("Error", f"No se encontró ruta para {archivo}")
                    continue
                
                # Mostrar información de la ruta
                self.log_info(f"Transferencia: {os.path.basename(archivo)}")
                self.log_info(f"Ruta óptima ({criterio}): {' -> '.join(ruta)}")
                
                # Encolar transferencia
                threading.Thread(target=self.transferir_archivo, 
                                args=(origen, destino, ruta, archivo), daemon=True).start()
                
            except Exception as e:
                self.log_info(f"Error al transferir {archivo}: {str(e)}")
    
    def start_transfer_thread(self):
        """Inicia el hilo que procesa las actualizaciones de transferencia."""
        def process_transfer_queue():
            while True:
                try:
                    item = self.transfer_queue.get_nowait()
                    if item[0] == 'progress':
                        _, progress, filename, _ = item
                        self.update_progress(progress, filename)
                    elif item[0] == 'complete':
                        _, filename, ruta, tiempo = item
                        self.log_info(f"Transferencia completada: {filename}")
                        self.log_info(f"Tiempo estimado: {tiempo:.2f} segundos")
                        self.update_progress(0, "")
                except:
                    pass
                
                self.root.update()
                time.sleep(0.1)
        
        threading.Thread(target=process_transfer_queue, daemon=True).start()
    
    def update_progress(self, value, filename):
        """Actualiza la barra de progreso."""
        self.progress_bar['value'] = value
        if value > 0:
            self.root.title(f"Transferencia de Archivos Optimizada - {filename} ({value}%)")
        else:
            self.root.title("Transferencia de Archivos Optimizada")
    
    def log_info(self, message):
        """Agrega un mensaje al área de información."""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, message + "\n")
        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)
    
    def mostrar_grafo_red(self):
        """Muestra el grafo de red en una ventana aparte."""
        # Crear etiquetas para las aristas
        edge_labels = {
            (u, v): f"{d['latencia']}ms / {d['ancho_banda'] if d['ancho_banda'] else 'N/A'}Mbps"
            for u, v, d in self.G.edges(data=True)
        }
        
        # Dibujar grafo en una nueva ventana
        graph_window = tk.Toplevel(self.root)
        graph_window.title("Grafo de Red")
        
        fig, ax = plt.subplots(figsize=(8, 6))
        pos = nx.spring_layout(self.G)
        nx.draw(self.G, pos, with_labels=True, node_size=2000, 
                node_color='lightblue', font_size=10, font_weight='bold', ax=ax)
        nx.draw_networkx_edge_labels(self.G, pos, edge_labels=edge_labels, 
                                    font_size=8, ax=ax)
        ax.set_title("Grafo de Latencia y Ancho de Banda")
        
        # Integrar matplotlib con Tkinter
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Iniciar aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkTransferApp(root)
    root.mainloop()