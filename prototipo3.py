import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import random
from scipy.interpolate import CubicSpline
import matplotlib.patches as patches

class RioMantaroSimulator:
    def __init__(self):
        # Parámetros del río
        self.longitud_rio = 150  # km
        self.ancho_rio = 2.0     # km (exagerado para visualización)
        self.puntos_cauce = 300
        
        # Zonas contaminantes con sus rangos (km)
        self.zonas = {
            'La Oroya': {'inicio': 0, 'fin': 25, 'color': 'red', 'factor_contaminacion': 1.5},
            'El Tambo': {'inicio': 40, 'fin': 70, 'color': 'orange', 'factor_contaminacion': 1.2},
            'Chilca': {'inicio': 80, 'fin': 100, 'color': 'yellow', 'factor_contaminacion': 1.0},
            'Huancayo': {'inicio': 110, 'fin': 140, 'color': 'lightcoral', 'factor_contaminacion': 1.3}
        }
        
        # Generar cauce del río
        self.generar_cauce()
        
        # Partículas de basura
        self.particulas = []
        self.max_particulas = 1000
        
        # Configuración de visualización
        self.fig = plt.figure(figsize=(15, 10))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Variables de control
        self.pausado = False
        self.tiempo = 0
        
    def generar_cauce(self):
        """Genera un cauce realista del río usando funciones matemáticas"""
        # Coordenadas a lo largo del río
        t = np.linspace(0, self.longitud_rio, self.puntos_cauce)
        
        # Generar curvas suaves para el cauce
        # X: meandros del río
        x_base = t * 0.8 + 10 * np.sin(t * 0.1) + 5 * np.cos(t * 0.05) + 2 * np.sin(t * 0.3)
        
        # Y: elevación del terreno (descendente)
        y_base = 4000 - t * 15 + 200 * np.sin(t * 0.08) + 100 * np.cos(t * 0.12)
        
        # Z: desplazamiento lateral
        z_base = 20 * np.sin(t * 0.06) + 15 * np.cos(t * 0.15) + 5 * np.sin(t * 0.4)
        
        # Interpolar para suavizar
        cs_x = CubicSpline(t, x_base)
        cs_y = CubicSpline(t, y_base)
        cs_z = CubicSpline(t, z_base)
        
        t_smooth = np.linspace(0, self.longitud_rio, self.puntos_cauce * 2)
        
        self.cauce_x = cs_x(t_smooth)
        self.cauce_y = cs_y(t_smooth)
        self.cauce_z = cs_z(t_smooth)
        self.cauce_t = t_smooth
        
        # Calcular vectores de dirección para el flujo
        self.direcciones = self.calcular_direcciones()
        
    def calcular_direcciones(self):
        """Calcula vectores de dirección del flujo en cada punto"""
        direcciones = []
        for i in range(len(self.cauce_x) - 1):
            dx = self.cauce_x[i+1] - self.cauce_x[i]
            dy = self.cauce_y[i+1] - self.cauce_y[i]
            dz = self.cauce_z[i+1] - self.cauce_z[i]
            
            # Normalizar
            mag = np.sqrt(dx**2 + dy**2 + dz**2)
            if mag > 0:
                direcciones.append([dx/mag, dy/mag, dz/mag])
            else:
                direcciones.append([1, 0, 0])
        
        # Agregar última dirección
        direcciones.append(direcciones[-1])
        return np.array(direcciones)
    
    def generar_superficie_rio(self):
        """Genera la superficie del río para visualización"""
        n_puntos = len(self.cauce_x)
        superficie_x = []
        superficie_y = []
        superficie_z = []
        
        for i in range(n_puntos):
            # Crear puntos perpendiculares al cauce
            if i < len(self.direcciones):
                dir_x, dir_y, dir_z = self.direcciones[i]
                
                # Vector perpendicular
                perp_x = -dir_z
                perp_z = dir_x
                perp_y = 0
                
                # Normalizar
                mag = np.sqrt(perp_x**2 + perp_z**2)
                if mag > 0:
                    perp_x /= mag
                    perp_z /= mag
                
                # Crear puntos del ancho del río
                for j in range(-10, 11):
                    factor = j / 10.0 * self.ancho_rio
                    superficie_x.append(self.cauce_x[i] + perp_x * factor)
                    superficie_y.append(self.cauce_y[i])
                    superficie_z.append(self.cauce_z[i] + perp_z * factor)
        
        return np.array(superficie_x), np.array(superficie_y), np.array(superficie_z)
    
    def crear_particula(self, zona, kg_basura):
        """Crea una partícula de basura en la zona especificada"""
        zona_info = self.zonas[zona]
        
        # Encontrar índice del cauce correspondiente a la zona
        inicio_idx = int((zona_info['inicio'] / self.longitud_rio) * len(self.cauce_x))
        fin_idx = int((zona_info['fin'] / self.longitud_rio) * len(self.cauce_x))
        
        # Posición inicial aleatoria dentro de la zona
        idx = random.randint(inicio_idx, min(fin_idx, len(self.cauce_x) - 1))
        
        # Posición en el río con algo de dispersión lateral
        offset_lateral = random.uniform(-self.ancho_rio/2, self.ancho_rio/2)
        
        if idx < len(self.direcciones):
            dir_x, dir_y, dir_z = self.direcciones[idx]
            perp_x = -dir_z
            perp_z = dir_x
            
            # Normalizar
            mag = np.sqrt(perp_x**2 + perp_z**2)
            if mag > 0:
                perp_x /= mag
                perp_z /= mag
        else:
            perp_x, perp_z = 0, 0
        
        x = self.cauce_x[idx] + perp_x * offset_lateral
        y = self.cauce_y[idx] + random.uniform(-0.1, 0.1)
        z = self.cauce_z[idx] + perp_z * offset_lateral
        
        # Determinar color basado en concentración
        concentracion = kg_basura / 1000  # Normalizar
        if concentracion > 0.8:
            color = 'red'
        elif concentracion > 0.5:
            color = 'orange'
        elif concentracion > 0.2:
            color = 'yellow'
        else:
            color = 'lightgreen'
        
        particula = {
            'x': x, 'y': y, 'z': z,
            'idx_cauce': idx,
            'velocidad': random.uniform(0.5, 1.5) * zona_info['factor_contaminacion'],
            'oscilacion_y': random.uniform(0, 2 * np.pi),
            'oscilacion_z': random.uniform(0, 2 * np.pi),
            'color': color,
            'tamaño': random.uniform(0.3, 0.8),
            'zona': zona
        }
        
        return particula
    
    def actualizar_particulas(self):
        """Actualiza posición de todas las partículas"""
        particulas_activas = []
        
        for particula in self.particulas:
            # Mover a lo largo del cauce
            particula['idx_cauce'] += particula['velocidad']
            
            # Verificar si la partícula sale del río
            if particula['idx_cauce'] >= len(self.cauce_x) - 1:
                continue
            
            # Actualizar posición
            idx = int(particula['idx_cauce'])
            if idx < len(self.cauce_x):
                particula['x'] = self.cauce_x[idx]
                particula['z'] = self.cauce_z[idx]
                
                # Oscilación vertical (flotación)
                particula['oscilacion_y'] += 0.1
                particula['y'] = self.cauce_y[idx] + 0.2 * np.sin(particula['oscilacion_y'])
                
                # Oscilación lateral leve
                particula['oscilacion_z'] += 0.05
                offset = 0.1 * np.sin(particula['oscilacion_z'])
                if idx < len(self.direcciones):
                    dir_x, dir_y, dir_z = self.direcciones[idx]
                    perp_x = -dir_z
                    perp_z = dir_x
                    mag = np.sqrt(perp_x**2 + perp_z**2)
                    if mag > 0:
                        particula['x'] += (perp_x/mag) * offset
                        particula['z'] += (perp_z/mag) * offset
                
                particulas_activas.append(particula)
        
        self.particulas = particulas_activas
    
    def agregar_basura(self, zona, kg_basura):
        """Agrega basura a una zona específica"""
        # Calcular número de partículas basado en kg
        num_particulas = min(int(kg_basura / 10), 200)  # Máximo 200 partículas por zona
        
        for _ in range(num_particulas):
            if len(self.particulas) < self.max_particulas:
                particula = self.crear_particula(zona, kg_basura)
                self.particulas.append(particula)
    
    def configurar_visualizacion(self):
        """Configura la visualización 3D"""
        self.ax.clear()
        
        # Dibujar superficie del río
        sup_x, sup_y, sup_z = self.generar_superficie_rio()
        self.ax.scatter(sup_x[::50], sup_y[::50], sup_z[::50], 
                       c='lightblue', alpha=0.3, s=5)
        
        # Dibujar cauce principal
        self.ax.plot(self.cauce_x, self.cauce_y, self.cauce_z, 
                    'b-', linewidth=3, alpha=0.7, label='Cauce del Río Mantaro')
        
        # Dibujar partículas de basura
        if self.particulas:
            x_particles = [p['x'] for p in self.particulas]
            y_particles = [p['y'] for p in self.particulas]
            z_particles = [p['z'] for p in self.particulas]
            colors = [p['color'] for p in self.particulas]
            sizes = [p['tamaño'] * 50 for p in self.particulas]
            
            self.ax.scatter(x_particles, y_particles, z_particles,
                          c=colors, s=sizes, alpha=0.8, edgecolors='black', linewidth=0.5)
        
        # Marcar zonas contaminantes
        for zona, info in self.zonas.items():
            inicio_idx = int((info['inicio'] / self.longitud_rio) * len(self.cauce_x))
            fin_idx = int((info['fin'] / self.longitud_rio) * len(self.cauce_x))
            
            if inicio_idx < len(self.cauce_x) and fin_idx < len(self.cauce_x):
                mid_idx = (inicio_idx + fin_idx) // 2
                self.ax.text(self.cauce_x[mid_idx], self.cauce_y[mid_idx] + 50, 
                           self.cauce_z[mid_idx], zona, 
                           fontsize=10, weight='bold', color=info['color'])
        
        # Configurar ejes
        self.ax.set_xlabel('X (km)', fontsize=12)
        self.ax.set_ylabel('Elevación (m)', fontsize=12)
        self.ax.set_zlabel('Z (km)', fontsize=12)
        self.ax.set_title('Simulación del Río Mantaro - Flujo de Contaminantes', 
                         fontsize=14, weight='bold')
        
        # Leyenda
        leyenda_elementos = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', 
                      markersize=10, label='Alta contaminación'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', 
                      markersize=10, label='Media contaminación'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='yellow', 
                      markersize=10, label='Baja contaminación'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgreen', 
                      markersize=10, label='Muy baja contaminación')
        ]
        self.ax.legend(handles=leyenda_elementos, loc='upper right')
        
        # Información de estadísticas
        total_particulas = len(self.particulas)
        info_text = f'Partículas activas: {total_particulas}\nTiempo: {self.tiempo:.1f}s'
        self.ax.text2D(0.02, 0.98, info_text, transform=self.ax.transAxes, 
                      fontsize=10, verticalalignment='top',
                      bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    def animar(self, frame):
        """Función de animación"""
        if not self.pausado:
            self.tiempo += 0.1
            self.actualizar_particulas()
            
            # Agregar nuevas partículas ocasionalmente
            if frame % 50 == 0:  # Cada 50 frames
                zona_random = random.choice(list(self.zonas.keys()))
                kg_random = random.uniform(100, 500)
                self.agregar_basura(zona_random, kg_random)
        
        self.configurar_visualizacion()
        return []
    
    def ejecutar_simulacion(self):
        """Ejecuta la simulación principal"""
        print("=== SIMULADOR DEL RÍO MANTARO ===")
        print("Zonas disponibles:")
        for zona in self.zonas.keys():
            print(f"- {zona}")
        
        # Configuración inicial
        while True:
            try:
                zona = input("\nSeleccione una zona contaminante: ").strip()
                if zona in self.zonas:
                    break
                print("Zona no válida. Intente nuevamente.")
            except KeyboardInterrupt:
                return
        
        while True:
            try:
                kg_basura = float(input(f"Ingrese kg de basura para {zona}: "))
                if kg_basura > 0:
                    break
                print("Debe ser un número positivo.")
            except (ValueError, KeyboardInterrupt):
                print("Ingrese un número válido.")
        
        # Agregar basura inicial
        self.agregar_basura(zona, kg_basura)
        
        # Crear animación
        self.configurar_visualizacion()
        
        print("\nControles:")
        print("- Cerrar ventana para terminar")
        print("- La simulación se ejecuta automáticamente")
        
        ani = FuncAnimation(self.fig, self.animar, frames=1000, 
                          interval=50, blit=False, repeat=True)
        
        plt.tight_layout()
        plt.show()
        
        return ani

def main():
    """Función principal"""
    try:
        simulator = RioMantaroSimulator()
        animation = simulator.ejecutar_simulacion()
    except KeyboardInterrupt:
        print("\nSimulación terminada por el usuario.")
    except Exception as e:
        print(f"Error en la simulación: {e}")

if __name__ == "__main__":
    main()