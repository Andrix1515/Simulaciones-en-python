import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import math
import time
from datetime import datetime

class MantaroRiverAnimation:
    def __init__(self):
        # Datos de las ciudades (km desde La Oroya, basura t/día)
        self.cities_data = {
            'Yauli (La Oroya)': {
                'distance': 0, 'waste': 27.1, 'color': '#FF4444',
                'elevation': 3700, 'x_pos': 0, 'y_pos': 0
            },
            'Jauja': {
                'distance': 53, 'waste': 10.5, 'color': '#FF8800',
                'elevation': 3400, 'x_pos': 53, 'y_pos': 0
            },
            'Concepción': {
                'distance': 81, 'waste': 38.8, 'color': '#FFBB00',
                'elevation': 3300, 'x_pos': 81, 'y_pos': 0
            },
            'Huancayo': {
                'distance': 103, 'waste': 382.5, 'color': '#FF0000',
                'elevation': 3200, 'x_pos': 103, 'y_pos': 0
            },
            'Chupaca': {
                'distance': 114, 'waste': 18.9, 'color': '#AA4444',
                'elevation': 3100, 'x_pos': 114, 'y_pos': 0
            }
        }
        # Parámetros del río
        self.river_length = 144  # Alargado 30 km más para mostrar basura de Chupaca
        self.k = 0.2  # constante de decaimiento
        self.resolution = 200
        # Parámetros de animación
        self.animation_speed = 2.0  # km por frame
        self.n_frames = 60
        # Crear el río serpenteante
        self.create_river_path()
        # Inicializar partículas de basura
        self.waste_particles = []
        self.particle_id = 0
        
    def create_river_path(self):
        """Crear un río serpenteante realista desde La Oroya hasta Chupaca"""
        self.x_river = np.linspace(0, self.river_length, self.resolution)
        # Crear curvas naturales del río (más pronunciadas)
        curve1 = 8 * np.sin(0.02 * self.x_river * 2 * np.pi)  # Curva principal
        curve2 = 3 * np.sin(0.05 * self.x_river * 2 * np.pi + 1.5)  # Curva secundaria
        curve3 = 1.5 * np.sin(0.1 * self.x_river * 2 * np.pi + 3)  # Ondulaciones pequeñas
        self.y_river = curve1 + curve2 + curve3
        # Elevación del río (descendente desde La Oroya)
        self.z_river = 3700 - (self.x_river * 5.2)  # Desciende ~600m en 114km
        # Ancho del río variable
        self.river_width = 0.8 + 0.4 * np.sin(0.03 * self.x_river * 2 * np.pi)
        # Ajustar posiciones de ciudades al río serpenteante
        for city, data in self.cities_data.items():
            idx = int(data['distance'] * self.resolution / self.river_length)
            if idx >= len(self.y_river):
                idx = len(self.y_river) - 1  # Asegura que el índice esté dentro del rango
            if idx >= 0:
                data['y_pos'] = self.y_river[idx]
                data['z_pos'] = self.z_river[idx] + 20  # Elevada sobre el río
            else:
                print(f"[ADVERTENCIA] Ciudad '{city}' fuera del rango del río. No se asigna 'z_pos'.")

    def create_river_surface(self):
        """Crear la superficie del río para visualización"""
        
        # Crear bordes del río
        left_bank = []
        right_bank = []
        
        for i in range(len(self.x_river)):
            width = self.river_width[i]
            left_bank.append([self.x_river[i], self.y_river[i] - width, self.z_river[i]])
            right_bank.append([self.x_river[i], self.y_river[i] + width, self.z_river[i]])
        
        return np.array(left_bank), np.array(right_bank)
    
    def pollution_function(self, x, xi, Bi):
        """Función de dispersión de basura"""
        if x < xi:
            return 0
        return Bi * self.k * np.exp(-self.k * (x - xi))
    
    def add_waste_particles(self, current_x, frame):
        """Añadir partículas de basura desde las ciudades usando la función de dispersión"""
        for city, data in self.cities_data.items():
            city_x = data['distance']
            # Solo añadir basura cuando el "frente" de agua pasa por la ciudad
            if abs(current_x - city_x) < 2:  # 2 km de tolerancia
                # OPTIMIZACIÓN: Huancayo máximo 10 partículas, más pequeñas y opacas
                if city == 'Huancayo':
                    n_particles = min(10, max(1, int(round(data['waste'] / 40))))
                    particle_size = 0.5  # tamaño aún más pequeño para Huancayo
                    particle_opacity = 1.0
                else:
                    n_particles = max(1, int(round(data['waste'] / 3)))
                    particle_size = 40  # tamaño aumentado para otras ciudades
                    particle_opacity = 1.0  # opacidad aumentada para otras ciudades
                for i in range(n_particles):
                    delta_x = i * 0.5
                    px = city_x - delta_x
                    if px < 0:
                        px = city_x
                    idx = int(px * self.resolution / self.river_length)
                    if idx < len(self.y_river):
                        particle = {
                            'id': self.particle_id,
                            'x': px,
                            'y': self.y_river[idx],
                            'z': self.z_river[idx] + 1,
                            'age': 0,
                            'source_city': city,
                            'color': data['color'],
                            'size': particle_size,
                            'Bi': data['waste'],
                            'xi': city_x,
                            'opacity': particle_opacity
                        }
                        self.waste_particles.append(particle)
                        self.particle_id += 1
    
    def update_particles(self):
        """Actualizar posición de las partículas de basura usando la función de dispersión"""
        particles_to_remove = []
        for i, particle in enumerate(self.waste_particles):
            # Movimiento río abajo
            particle['x'] += self.animation_speed * 0.8
            particle['age'] += 1
            # Dispersión lateral (siguiendo el río)
            if particle['x'] < self.river_length:
                idx = int(particle['x'] * self.resolution / self.river_length)
                if idx < len(self.y_river):
                    target_y = self.y_river[idx]
                    particle['y'] += (target_y - particle['y']) * 0.1 + np.random.normal(0, 0.05)
                    particle['z'] = self.z_river[idx] + 1
            # Dispersión por función C(x)
            x_disp = particle['x'] - particle['xi']
            Cx = particle['Bi'] * self.k * np.exp(-self.k * x_disp)
            # Usar Cx para modificar el tamaño y opacidad (disminuyen progresivamente)
            if particle['source_city'] == 'Huancayo':
                particle['size'] = max(1, Cx * 0.5)  # tamaño mínimo y progresión más suave para Huancayo
            else:
                particle['size'] = max(20, Cx * 4)  # tamaño aumentado para otras ciudades
            particle['opacity'] = min(1.0, max(0.7, Cx / particle['Bi'])) if particle['source_city'] != 'Huancayo' else min(1.0, max(0.1, Cx / particle['Bi']))
            # Eliminar si C(x) es muy bajo (y <= 0.1)
            if Cx <= 0.1:
                particles_to_remove.append(i)
            # Remover partículas que salen del dominio o son muy viejas
            if particle['x'] > self.river_length or particle['age'] > 100:
                particles_to_remove.append(i)
        # Eliminar duplicados y ordenar en reversa
        for i in sorted(set(particles_to_remove), reverse=True):
            self.waste_particles.pop(i)
    
    def create_frame(self, frame_num):
        """Crear un frame de la animación"""
        
        # Posición actual del "frente" de agua
        current_x = frame_num * self.animation_speed
        
        # Añadir nuevas partículas de basura
        self.add_waste_particles(current_x, frame_num)
        # Modo loop: cada 10 frames, generar basura en cada ciudad
        if frame_num % 10 == 0:
            for city, data in self.cities_data.items():
                if city == 'Huancayo':
                    n_particles = min(10, max(1, int(round(data['waste'] / 40))))
                    particle_size = 18  # tamaño reducido para Huancayo
                    particle_opacity = 1.0
                else:
                    n_particles = max(1, int(round(data['waste'] / 3)))
                    particle_size = 80  # tamaño aumentado para otras ciudades
                    particle_opacity = 1.0  # opacidad aumentada para otras ciudades
                for i in range(n_particles):
                    delta_x = i * 0.5
                    px = data['distance'] - delta_x
                    if px < 0:
                        px = data['distance']
                    idx = int(px * self.resolution / self.river_length)
                    if idx < len(self.y_river):
                        particle = {
                            'id': self.particle_id,
                            'x': px,
                            'y': self.y_river[idx],
                            'z': self.z_river[idx] + 1,
                            'age': 0,
                            'source_city': city,
                            'color': data['color'],
                            'size': particle_size,
                            'Bi': data['waste'],
                            'xi': data['distance'],
                            'opacity': particle_opacity
                        }
                        self.waste_particles.append(particle)
                        self.particle_id += 1
        # Limitar el número total de partículas para optimización
        if len(self.waste_particles) > 200:
            self.waste_particles = self.waste_particles[-200:]
        
        # Actualizar partículas existentes
        self.update_particles()
        
        # Crear trazos para este frame
        traces = []
        
        # 1. Río base (línea central)
        traces.append(go.Scatter3d(
            x=self.x_river,
            y=self.y_river,
            z=self.z_river,
            mode='lines',
            line=dict(color='lightblue', width=6),
            name='Río Mantaro',
            showlegend=True if frame_num == 0 else False
        ))
        
        # 2. Bordes del río
        left_bank, right_bank = self.create_river_surface()
        
        traces.append(go.Scatter3d(
            x=left_bank[:, 0],
            y=left_bank[:, 1],
            z=left_bank[:, 2],
            mode='lines',
            line=dict(color='saddlebrown', width=3),
            name='Orilla izquierda',
            showlegend=True if frame_num == 0 else False
        ))
        
        traces.append(go.Scatter3d(
            x=right_bank[:, 0],
            y=right_bank[:, 1],
            z=right_bank[:, 2],
            mode='lines',
            line=dict(color='saddlebrown', width=3),
            name='Orilla derecha',
            showlegend=True if frame_num == 0 else False
        ))
        
        # 3. Ciudades (siempre visibles)
        for city, data in self.cities_data.items():
            if 'z_pos' in data:
                # Colores más simples para los cuadros de información
                cuadro_color = 'white' if city != 'Huancayo' else 'mistyrose'
                # Eliminar la propiedad 'opacity' del hoverlabel (no es válida en Plotly)
                traces.append(go.Scatter3d(
                    x=[data['x_pos']],
                    y=[data['y_pos']],
                    z=[data['z_pos']],
                    mode='markers+text',
                    marker=dict(
                        size=max(10, data['waste'] / 20),
                        color=data['color'],
                        symbol='diamond',
                        line=dict(width=2, color='black')
                    ),
                    text=[f"{city}<br>{data['waste']} t/día"],
                    textposition="top center",
                    textfont=dict(size=12, color='black'),
                    name=city,
                    showlegend=True if frame_num == 0 else False,
                    hoverinfo='text',
                    hoverlabel=dict(bgcolor=cuadro_color, bordercolor='black', font=dict(color='black'))
                ))
                # Texto flotante especial para Huancayo
                if city == 'Huancayo':
                    traces.append(go.Scatter3d(
                        x=[data['x_pos']+2],
                        y=[data['y_pos']+2],
                        z=[data['z_pos']+30],
                        mode='text',
                        text=[f"¡Mayor contaminación!<br>{data['waste']} t/día"],
                        textfont=dict(size=18, color='red'),
                        showlegend=False
                    ))
        
        # 4. Partículas de basura (usando opacidad y tamaño por C(x))
        if self.waste_particles:
            city_particles = {}
            for particle in self.waste_particles:
                city = particle['source_city']
                if city not in city_particles:
                    city_particles[city] = {'x': [], 'y': [], 'z': [], 'color_rgba': [], 'size': []}
                idx = int(particle['x'] * self.resolution / self.river_length)
                if idx < len(self.y_river):
                    city_particles[city]['x'].append(self.x_river[idx])
                    city_particles[city]['y'].append(self.y_river[idx])
                    city_particles[city]['z'].append(self.z_river[idx] + 1)
                    # Convertir color hex a RGBA con opacidad individual
                    hex_color = particle.get('color', '#888888')
                    opacity = particle.get('opacity', 0.95)
                    # Convertir hex a r,g,b
                    hex_color = hex_color.lstrip('#')
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    city_particles[city]['color_rgba'].append(f'rgba({r},{g},{b},{opacity})')
                    city_particles[city]['size'].append(particle.get('size', 20))
            for city, particles in city_particles.items():
                sizes = particles['size']
                colors_rgba = particles['color_rgba']
                traces.append(go.Scatter3d(
                    x=particles['x'],
                    y=particles['y'],
                    z=particles['z'],
                    mode='markers',
                    marker=dict(
                        size=sizes,
                        color=colors_rgba,
                        symbol='circle',
                        line=dict(width=3, color='black')
                    ),
                    name=f'Basura de {city}',
                    showlegend=True if frame_num == 0 else False
                ))
        # 5. Frente de agua (indicador visual)
        if current_x <= self.river_length:
            idx = int(current_x * self.resolution / self.river_length)
            if idx < len(self.y_river):
                traces.append(go.Scatter3d(
                    x=[current_x],
                    y=[self.y_river[idx]],
                    z=[self.z_river[idx] + 5],
                    mode='markers',
                    marker=dict(
                        size=20,
                        color='deepskyblue',
                        symbol='circle-open',  # aro tamaño partícula
                        line=dict(width=10, color='blue')
                    ),
                    name='Frente de agua',
                    showlegend=True if frame_num == 0 else False
                ))
        
        return traces
    
    def create_animation(self):
        """Crear la animación completa"""
        
        # Crear frames de animación
        frames = []
        
        for frame_num in range(self.n_frames):
            frame_traces = self.create_frame(frame_num)
            frames.append(go.Frame(data=frame_traces, name=f'frame_{frame_num}'))
        
        # Crear figura inicial
        initial_traces = self.create_frame(0)
        
        fig = go.Figure(data=initial_traces, frames=frames)
        
        # Configurar animación
        fig.update_layout(
            title={
                'text': 'Río Mantaro - Simulación de Flujo y Dispersión de Basura Doméstica',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'darkblue'}
            },
            scene=dict(
                xaxis_title="Distancia desde La Oroya (km)",
                yaxis_title="Desviación lateral (km)",
                zaxis_title="Elevación (m)",
                camera=dict(
                    eye=dict(x=1.8, y=1.8, z=1.2)
                ),
                aspectmode='manual',
                aspectratio=dict(x=3, y=1, z=0.8),
                bgcolor='lightcyan'
            ),
            updatemenus=[{
                'type': 'buttons',
                'buttons': [
                    {
                        'label': '▶️ Play',
                        'method': 'animate',
                        'args': [None, {
                            'frame': {'duration': 200, 'redraw': True},
                            'fromcurrent': True,
                            'transition': {'duration': 100}
                        }]
                    },
                    {
                        'label': '⏸️ Pause',
                        'method': 'animate',
                        'args': [[None], {
                            'frame': {'duration': 0, 'redraw': False},
                            'mode': 'immediate',
                            'transition': {'duration': 0}
                        }]
                    },
                    {
                        'label': '🔄 Restart',
                        'method': 'animate',
                        'args': [None, {
                            'frame': {'duration': 200, 'redraw': True},
                            'fromcurrent': False,
                            'transition': {'duration': 100}
                        }]
                    }
                ],
                'direction': 'left',
                'pad': {'r': 10, 't': 10},
                'showactive': False,
                'x': 0.1,
                'xanchor': 'right',
                'y': 0,
                'yanchor': 'top'
            }],
            sliders=[{
                'active': 0,
                'yanchor': 'top',
                'xanchor': 'left',
                'currentvalue': {
                    'font': {'size': 20},
                    'prefix': 'Tiempo: ',
                    'visible': True,
                    'xanchor': 'right'
                },
                'transition': {'duration': 300, 'easing': 'cubic-in-out'},
                'pad': {'b': 10, 't': 50},
                'len': 0.9,
                'x': 0.1,
                'y': 0,
                'steps': [
                    {
                        'args': [[f'frame_{i}'], {
                            'frame': {'duration': 300, 'redraw': True},
                            'mode': 'immediate',
                            'transition': {'duration': 300}
                        }],
                        'label': f'{i * self.animation_speed:.1f} km',
                        'method': 'animate'
                    } for i in range(self.n_frames)
                ]
            }],
            width=1400,
            height=900,
            showlegend=True
        )
        
        return fig
    
    def create_dashboard(self):
        """Crear dashboard informativo"""
        
        # Crear la animación principal
        main_fig = self.create_animation()
        
        # Añadir información textual
        info_text = f"""
        <b>Simulación del Río Mantaro</b><br>
        📏 Longitud total: {self.river_length} km<br>
        🏔️ Elevación inicial (La Oroya): 3,700 m<br>
        🏞️ Elevación final (Chupaca): 3,100 m<br>
        📉 Pendiente promedio: 5.2 m/km<br>
        <br>
        <b>Generación de Basura por Ciudad:</b><br>
        🔴 Huancayo: 382.5 t/día (Mayor contaminante)<br>
        🟡 Concepción: 38.8 t/día<br>
        🟠 La Oroya: 27.1 t/día<br>
        🟤 Chupaca: 18.9 t/día<br>
        🟡 Jauja: 10.5 t/día<br>
        <br>
        <b>Función de Dispersión:</b><br>
        C(x) = B_i × k × e^(-k(x-x_i))<br>
        donde k = 0.2 (constante de decaimiento)
        """
        
        main_fig.add_annotation(
            text=info_text,
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            showarrow=False,
            align="left",
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="black",
            borderwidth=1,
            font=dict(size=12)
        )
        
        return main_fig

# Crear y ejecutar la animación
if __name__ == "__main__":
    print("🌊 Iniciando simulación del Río Mantaro...")
    print("=" * 60)
    
    # Crear modelo
    model = MantaroRiverAnimation()
    
    # Información del modelo
    print("📊 CONFIGURACIÓN DEL MODELO:")
    print(f"   • Longitud del río: {model.river_length} km")
    print(f"   • Resolución: {model.resolution} puntos")
    print(f"   • Frames de animación: {model.n_frames}")
    print(f"   • Velocidad: {model.animation_speed} km/frame")
    
    print("\n🏙️ CIUDADES MODELADAS:")
    for city, data in model.cities_data.items():
        print(f"   • {city}: {data['distance']} km, {data['waste']} t/día, {data['elevation']} m")
    
    print("\n🎮 CONTROLES DE ANIMACIÓN:")
    print("   • ▶️ Play: Iniciar animación")
    print("   • ⏸️ Pause: Pausar animación")
    print("   • 🔄 Restart: Reiniciar desde el inicio")
    print("   • 🎚️ Slider: Navegar manualmente")
    
    # Crear dashboard
    fig = model.create_dashboard()
    
    print("\n🚀 Abriendo visualización...")
    print("   La animación mostrará:")
    print("   ✓ Río serpenteante desde La Oroya hasta Chupaca")
    print("   ✓ Descenso de 3,700m a 3,100m de elevación")
    print("   ✓ Aparición de basura en cada ciudad")
    print("   ✓ Dispersión de contaminantes río abajo")
    print("   ✓ Partículas coloreadas por ciudad de origen")
    
    # Mostrar la animación
    fig.show()
    
    print("\n🎯 ¡Animación lista!")
    print("   Observa cómo la basura aparece en cada ciudad")
    print("   y se dispersa siguiendo el flujo del río.")
    print("=" * 60)