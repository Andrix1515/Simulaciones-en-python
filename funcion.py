import numpy as np
import matplotlib.pyplot as plt

# Parámetros
k = 0.1  # coeficiente de decaimiento
x = np.linspace(0, 100, 1000)  # tramo del río (0 a 100 km)

# Datos de cada zona
puntos = {
    "La Oroya": {"x_i": 0, "B": 1.5},
    "El Tambo": {"x_i": 50, "B": 150},
    "Chilca": {"x_i": 55, "B": 50},
    "Huancayo": {"x_i": 58, "B": 120}
}

# Heaviside escalón (para que cada función comience en su punto de vertido)
def H(x):
    return np.where(x >= 0, 1, 0)

# Crear cada función y sumarlas
C_total = np.zeros_like(x)
for nombre, datos in puntos.items():
    x_i = datos["x_i"]
    B = datos["B"]
    C_i = B * k * np.exp(-k * (x - x_i)) * H(x - x_i)
    C_total += C_i
    plt.plot(x, C_i, label=f"{nombre}")

# Graficar la función total
plt.plot(x, C_total, label="Total", color='black', linewidth=2, linestyle="--")

# Gráfico
plt.title("Concentración de Basura a lo Largo del Río Mantaro")
plt.xlabel("Distancia desde La Oroya (km)")
plt.ylabel("Concentración estimada (t/km)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
