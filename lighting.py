# lighting.py
import numpy as np

class Light:
    def __init__(self, position, color=(1.0, 1.0, 1.0), intensity=1.0):
        self.position = np.array(position)
        self.color = np.array(color)
        self.intensity = intensity

class LambertShader:
    """Модель освещения Ламберта"""
    
    def __init__(self, light, ambient_intensity=0.2):
        self.light = light
        self.ambient_intensity = ambient_intensity
    
    def calculate_vertex_color(self, vertex, material_color):
        """Вычисление цвета вершины по модели Ламберта"""
        # Направление от вершины к источнику света
        light_x = self.light.position[0] - vertex.x
        light_y = self.light.position[1] - vertex.y
        light_z = self.light.position[2] - vertex.z
        
        # Нормализуем направление света
        light_len = np.sqrt(light_x**2 + light_y**2 + light_z**2)
        if light_len > 0:
            light_x /= light_len
            light_y /= light_len
            light_z /= light_len
        
        # Нормаль вершины уже нормализована
        normal_x = vertex.normal_x
        normal_y = vertex.normal_y
        normal_z = vertex.normal_z
        
        # Диффузная составляющая (cos угла между нормалью и направлением света)
        diffuse = max(0, normal_x * light_x + normal_y * light_y + normal_z * light_z)
        
        # Ambient составляющая
        ambient = self.ambient_intensity
        
        # Итоговая интенсивность
        intensity = ambient + diffuse * self.light.intensity
        
        # Цвет вершины (умножаем на цвет материала)
        color = (
            material_color[0] * intensity * self.light.color[0],
            material_color[1] * intensity * self.light.color[1],
            material_color[2] * intensity * self.light.color[2]
        )
        
        return color

class GouraudShader:
    """Шейдинг Гуро с интерполяцией цветов вершин"""
    
    def __init__(self, lambert_shader):
        self.lambert_shader = lambert_shader
    
    def shade_triangle(self, screen, v0, v1, v2, p0, p1, p2):
        """Закраска треугольника методом Гуро с билинейной интерполяцией"""
        # Находим ограничивающий прямоугольник
        x_coords = [p0[0], p1[0], p2[0]]
        y_coords = [p0[1], p1[1], p2[1]]
        
        min_x = max(0, int(min(x_coords)))
        max_x = min(screen.get_width() - 1, int(max(x_coords)))
        min_y = max(0, int(min(y_coords)))
        max_y = min(screen.get_height() - 1, int(max(y_coords)))
        
        if min_x >= max_x or min_y >= max_y:
            return
        
        # Предварительные вычисления для барицентрических координат
        area = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
        if abs(area) < 1e-6:
            return
        
        inv_area = 1.0 / area
        
        # Растеризация с интерполяцией цветов
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                # Барицентрические координаты
                w1 = ((p1[1] - p2[1]) * (x - p2[0]) + (p2[0] - p1[0]) * (y - p2[1])) * inv_area
                w2 = ((p2[1] - p0[1]) * (x - p2[0]) + (p0[0] - p2[0]) * (y - p2[1])) * inv_area
                w0 = 1 - w1 - w2
                
                # Проверка внутри треугольника
                if w0 >= -0.001 and w1 >= -0.001 and w2 >= -0.001:
                    # Интерполяция цвета
                    if v0.color and v1.color and v2.color:
                        color = (
                            w0 * v0.color[0] + w1 * v1.color[0] + w2 * v2.color[0],
                            w0 * v0.color[1] + w1 * v1.color[1] + w2 * v2.color[1],
                            w0 * v0.color[2] + w1 * v1.color[2] + w2 * v2.color[2]
                        )
                        
                        # Ограничение значений
                        color = (
                            max(0, min(255, int(color[0]))),
                            max(0, min(255, int(color[1]))),
                            max(0, min(255, int(color[2])))
                        )
                        
                        # Рисуем пиксель
                        screen.set_at((x, y), color)