import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from scipy.interpolate import griddata, interp1d
import pandas as pd
import math
from datetime import datetime, timedelta

class MantaroRiverModel:
    def __init__(self):
        # Datos de las ciudades (km desde La Oroya, basura t/día)
        self.cities_data = {
            'Yauli (La Oroya)': {'distance': 0, 'waste': 27.1, 'color': '#FF4444'},
            'Jauja': {'distance': 53, 'waste': 10.5, 'color': '#FF8800'},
            'Concepción': {'distance': 81, 'waste': 38.8, 'color': '#FFBB00'},
            'Huancayo': {'distance': 103, 'waste': 382.5, 'color': '#FF0000'},
            'Chupaca': {'distance': 114, 'waste': 18.9, 'color': '#AA4444'}
        }
        
        # Parámetros del modelo
        self.k = 0.2  # constante de decaimiento
        self.river_length = 114  # km
        self.river_width_scale = 2  # escala del ancho para visualización
        self.resolution = 100
        
        # Crear el mesh del río
        self.create_river_mesh()
        
    def create_river_mesh(self):
        """Crear un mesh 3D realista del río con curvas naturales"""
        
        # Coordenadas longitudinales (x) del río
        self.x_river = np.linspace(0, self.river_length, self.resolution)
        
        # Crear curvas naturales del río (sinusoidal suave)
        curve_amplitude = 0.5  # km de amplitud de curva
        curve_frequency = 0.05  # frecuencia de las curvas
        
        # Coordenadas laterales (y) con curvas
        y_center = curve_amplitude * np.sin(curve_frequency * self.x_river * 2 * np.pi)
        
        # Ancho variable del río (20-50 metros escalado)
        river_width = (30 + 20 * np.sin(0.03 * self.x_river * 2 * np.pi)) * self.river_width_scale
        
        # Crear grid 2D
        self.y_river = np.linspace(-2, 2, 50)  # ancho normalizado
        self.X, self.Y = np.meshgrid(self.x_river, self.y_river)
        
        # Ajustar Y según el ancho variable y las curvas
        self.Y_adjusted = np.zeros_like(self.Y)
        for i in range(len(self.x_river)):
            width_factor = river_width[i] / (2 * self.river_width_scale)
            self.Y_adjusted[:, i] = self.Y[:, i] * width_factor + y_center[i]
        
        # Crear elevaciones del terreno (valle del Mantaro)
        self.create_terrain_elevation()
        
        # Crear superficie del agua
        self.create_water_surface()
        
    def create_terrain_elevation(self):
        """Crear elevaciones realistas del terreno"""
        
        # Elevación base del valle (descendente)
        base_elevation = 3200 - (self.X * 8)  # desciende 8m por km
        
        # Elevación del cauce del río (más bajo en el centro)
        river_depression = 2 * np.exp(-((self.Y_adjusted / 0.5) ** 2))
        
        # Elevaciones laterales del valle
        valley_slopes = 50 * np.abs(self.Y_adjusted) ** 1.5
        
        # Rugosidad del terreno
        roughness = 5 * np.sin(self.X * 0.1) * np.cos(self.Y_adjusted * 0.2)
        
        # Elevación final del terreno
        self.Z_terrain = base_elevation + valley_slopes - river_depression + roughness
        
        # Elevación del lecho del río
        self.Z_riverbed = base_elevation - river_depression - 2
        
    def create_water_surface(self):
        """Crear superficie del agua con pequeñas ondulaciones"""
        
        # Profundidad variable del agua (1-3 metros)
        water_depth = 1.5 + 0.5 * np.sin(self.X * 0.05)
        
        # Ondulaciones en la superficie
        surface_waves = 0.1 * np.sin(self.X * 0.3) * np.cos(self.Y_adjusted * 0.5)
        
        # Superficie del agua
        self.Z_water = self.Z_riverbed + water_depth + surface_waves
        
    def pollution_function(self, x, xi, Bi):
        """Función de dispersión de basura: C(x) = Bi * k * e^(-k(x-xi))"""
        if x < xi:
            return 0
        return Bi * self.k * np.exp(-self.k * (x - xi))
    
    def calculate_pollution_field(self, active_cities=None):
        """Calcular campo de concentración de basura acumulativo"""
        
        if active_cities is None:
            active_cities = list(self.cities_data.keys())
        
        # Inicializar campo de concentración
        pollution_field = np.zeros_like(self.X)
        
        # Contribución de cada ciudad
        for city, data in self.cities_data.items():
            if city in active_cities:
                xi = data['distance']
                Bi = data['waste']
                
                # Aplicar función de dispersión
                for i in range(self.resolution):
                    x = self.x_river[i]
                    concentration = self.pollution_function(x, xi, Bi)
                    
                    # Dispersión lateral (gaussiana)
                    for j in range(len(self.y_river)):
                        lateral_factor = np.exp(-((self.Y_adjusted[j, i]) ** 2) / 0.5)
                        pollution_field[j, i] += concentration * lateral_factor
        
        return pollution_field
    
    def create_flow_vectors(self):
        """Crear vectores de velocidad del flujo"""
        
        # Reducir resolución para vectores
        step = 10
        x_vec = self.X[::step, ::step]
        y_vec = self.Y_adjusted[::step, ::step]
        z_vec = self.Z_water[::step, ::step]
        
        # Velocidad en dirección x (río abajo)
        u = np.ones_like(x_vec) * 0.5
        
        # Velocidad en dirección y (corrientes laterales)
        v = 0.1 * np.sin(x_vec * 0.1) * np.cos(y_vec * 0.5)
        
        # Velocidad en dirección z (turbulencia vertical)
        w = 0.05 * np.sin(x_vec * 0.2) * np.sin(y_vec * 0.3)
        
        return x_vec, y_vec, z_vec, u, v, w
    
    def create_particles(self, n_particles=100):
        """Crear partículas animadas que siguen el flujo"""
        
        particles = []
        
        for i in range(n_particles):
            # Posición inicial aleatoria
            x_start = np.random.uniform(0, self.river_length)
            y_start = np.random.uniform(-0.5, 0.5)
            
            # Interpolar elevación del agua
            z_start = np.interp(x_start, self.x_river, 
                              np.mean(self.Z_water, axis=0)) + 0.1
            
            particles.append({
                'x': x_start,
                'y': y_start,
                'z': z_start,
                'age': 0
            })
        
        return particles
    
    def create_interactive_plot(self, active_cities=None):
        """Crear visualización 3D interactiva principal"""
        
        # Calcular campo de contaminación
        pollution_field = self.calculate_pollution_field(active_cities)
        
        # Crear figura con subplots
        fig = go.Figure()
        
        # 1. Superficie del terreno
        fig.add_trace(go.Surface(
            x=self.X,
            y=self.Y_adjusted,
            z=self.Z_terrain,
            colorscale='earth',
            showscale=False,
            name='Terreno',
            opacity=0.8
        ))
        
        # 2. Superficie del agua
        fig.add_trace(go.Surface(
            x=self.X,
            y=self.Y_adjusted,
            z=self.Z_water,
            colorscale='Blues',
            showscale=False,
            name='Agua',
            opacity=0.7
        ))
        
        # 3. Campo de contaminación (volumen 3D)
        # Crear isosuperficie de contaminación
        pollution_threshold = np.max(pollution_field) * 0.1
        
        fig.add_trace(go.Surface(
            x=self.X,
            y=self.Y_adjusted,
            z=self.Z_water + 0.5,
            surfacecolor=pollution_field,
            colorscale='Reds',
            showscale=True,
            name='Contaminación',
            opacity=0.6,
            colorbar=dict(title="Concentración (t/día·km)")
        ))
        
        # 4. Vectores de flujo
        x_vec, y_vec, z_vec, u, v, w = self.create_flow_vectors()
        
        fig.add_trace(go.Cone(
            x=x_vec.flatten(),
            y=y_vec.flatten(),
            z=z_vec.flatten(),
            u=u.flatten(),
            v=v.flatten(),
            w=w.flatten(),
            colorscale='Blues',
            showscale=False,
            name='Flujo',
            sizemode='absolute',
            sizeref=0.5
        ))
        
        # 5. Marcadores de ciudades
        for city, data in self.cities_data.items():
            if active_cities is None or city in active_cities:
                x_city = data['distance']
                y_city = 0
                z_city = np.interp(x_city, self.x_river, np.mean(self.Z_water, axis=0)) + 1
                
                fig.add_trace(go.Scatter3d(
                    x=[x_city],
                    y=[y_city],
                    z=[z_city],
                    mode='markers+text',
                    marker=dict(
                        size=max(5, data['waste'] / 20),
                        color=data['color'],
                        opacity=0.8
                    ),
                    text=[f"{city}<br>{data['waste']} t/día"],
                    textposition="top center",
                    name=city,
                    hovertemplate=f"<b>{city}</b><br>Distancia: {data['distance']} km<br>Basura: {data['waste']} t/día<extra></extra>"
                ))
        
        # 6. Configuración del layout
        fig.update_layout(
            title={
                'text': "Modelo 3D del Río Mantaro - Simulación de Flujo y Dispersión de Basura",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16}
            },
            scene=dict(
                xaxis_title="Distancia desde La Oroya (km)",
                yaxis_title="Ancho del río (km)",
                zaxis_title="Elevación (m)",
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.2)
                ),
                aspectmode='manual',
                aspectratio=dict(x=3, y=1, z=0.5)
            ),
            width=1200,
            height=800,
            showlegend=True
        )
        
        return fig
    
    def create_animation_frames(self, n_frames=20):
        """Crear frames de animación para partículas"""
        
        frames = []
        particles = self.create_particles(50)
        
        for frame in range(n_frames):
            # Actualizar posición de partículas
            for particle in particles:
                # Movimiento río abajo
                particle['x'] += 2.0  # km por frame
                particle['y'] += np.random.normal(0, 0.1)  # difusión lateral
                particle['age'] += 1
                
                # Reiniciar partículas que salen del dominio
                if particle['x'] > self.river_length:
                    particle['x'] = 0
                    particle['y'] = np.random.uniform(-0.5, 0.5)
                    particle['age'] = 0
            
            # Crear frame
            frame_data = []
            
            # Partículas
            x_particles = [p['x'] for p in particles]
            y_particles = [p['y'] for p in particles]
            z_particles = [np.interp(p['x'], self.x_river, np.mean(self.Z_water, axis=0)) + 0.2 
                          for p in particles]
            
            frame_data.append(go.Scatter3d(
                x=x_particles,
                y=y_particles,
                z=z_particles,
                mode='markers',
                marker=dict(
                    size=3,
                    color='red',
                    opacity=0.7
                ),
                name=f'Partículas t={frame}'
            ))
            
            frames.append(go.Frame(data=frame_data, name=f'frame_{frame}'))
        
        return frames
    
    def create_dashboard(self):
        """Crear dashboard interactivo completo"""
        
        # Crear figura principal
        main_fig = self.create_interactive_plot()
        
        # Añadir controles interactivos
        main_fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    buttons=list([
                        dict(
                            args=[{"visible": [True, True, True, True] + [True] * len(self.cities_data)}],
                            label="Mostrar Todo",
                            method="restyle"
                        ),
                        dict(
                            args=[{"visible": [True, True, False, False] + [False] * len(self.cities_data)}],
                            label="Solo Río",
                            method="restyle"
                        ),
                        dict(
                            args=[{"visible": [False, False, True, True] + [True] * len(self.cities_data)}],
                            label="Solo Contaminación",
                            method="restyle"
                        )
                    ]),
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.01,
                    xanchor="left",
                    y=1.02,
                    yanchor="top"
                ),
            ],
            annotations=[
                dict(text="Controles de Visualización:", showarrow=False,
                     x=0.01, y=1.08, xref="paper", yref="paper")
            ]
        )
        
        return main_fig

# Crear y ejecutar el modelo
if __name__ == "__main__":
    # Inicializar modelo
    model = MantaroRiverModel()
    
    # Crear dashboard interactivo
    fig = model.create_dashboard()
    
    # Mostrar información del modelo
    print("=" * 60)
    print("MODELO 3D DEL RÍO MANTARO")
    print("=" * 60)
    print(f"Longitud del río: {model.river_length} km")
    print(f"Resolución del mesh: {model.resolution} puntos")
    print(f"Constante de decaimiento: {model.k}")
    print("\nCiudades incluidas:")
    for city, data in model.cities_data.items():
        print(f"- {city}: {data['distance']} km, {data['waste']} t/día")
    
    print("\nCaracterísticas del modelo:")
    print("✓ Mesh 3D realista del río con curvas naturales")
    print("✓ Función de dispersión exponencial de basura")
    print("✓ Visualización interactiva con Plotly")
    print("✓ Vectores de flujo y partículas animadas")
    print("✓ Superficie del agua con transparencia")
    print("✓ Marcadores de ciudades proporcionales")
    print("✓ Controles interactivos de visualización")
    
    # Mostrar la figura
    fig.show()
    
    # Crear análisis adicional
    print("\n" + "=" * 60)
    print("ANÁLISIS DE CONTAMINACIÓN")
    print("=" * 60)
    
    # Calcular concentración máxima en diferentes puntos
    analysis_points = [20, 50, 80, 100, 114]
    pollution_field = model.calculate_pollution_field()
    
    print("Concentración de basura en puntos clave:")
    for point in analysis_points:
        idx = int(point * model.resolution / model.river_length)
        if idx < model.resolution:
            max_concentration = np.max(pollution_field[:, idx])
            print(f"- Km {point}: {max_concentration:.2f} t/día·km")
    
    print("\nCiudad con mayor impacto:", max(model.cities_data.items(), key=lambda x: x[1]['waste'])[0])
    print("Total de basura generada:", sum(data['waste'] for data in model.cities_data.values()), "t/día")