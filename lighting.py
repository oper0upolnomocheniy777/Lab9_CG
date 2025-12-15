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
                        # ИСПРАВЛЕННАЯ СТРОКА: используем v2.color[1] вместо v2.color[2]
                        color = (
                            w0 * v0.color[0] + w1 * v1.color[0] + w2 * v2.color[0],
                            w0 * v0.color[1] + w1 * v1.color[1] + w2 * v2.color[1],  # Исправлено
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

class PhongShader:
    """Шейдинг Фонга с интерполяцией нормалей"""
    
    def __init__(self, light, ambient_intensity=0.2, specular_intensity=0.5, shininess=32):
        self.light = light
        self.ambient_intensity = ambient_intensity
        self.specular_intensity = specular_intensity
        self.shininess = shininess
        self.view_pos = np.array([0, 0, 3])  # Позиция камеры
    
    def set_view_pos(self, view_pos):
        """Установка позиции камеры"""
        self.view_pos = np.array(view_pos)
    
    def calculate_vertex_color(self, vertex, material_color, use_phong=True):
        """Вычисление цвета вершины по модели Фонга"""
        vertex_pos = np.array([vertex.x, vertex.y, vertex.z])
        normal = np.array([vertex.normal_x, vertex.normal_y, vertex.normal_z])
        
        # Направление света
        light_dir = self.light.position - vertex_pos
        light_len = np.linalg.norm(light_dir)
        
        if light_len > 0:
            light_dir = light_dir / light_len
        
        # Направление к камере
        view_dir = self.view_pos - vertex_pos
        view_len = np.linalg.norm(view_dir)
        
        if view_len > 0:
            view_dir = view_dir / view_len
        
        # Ambient составляющая
        ambient = self.ambient_intensity
        
        # Диффузная составляющая
        diffuse = max(0, np.dot(normal, light_dir))
        
        # Specular составляющая (только для Фонга)
        specular = 0
        if use_phong and diffuse > 0:
            # Вектор отражения
            reflect_dir = 2 * np.dot(normal, light_dir) * normal - light_dir
            reflect_dir = reflect_dir / np.linalg.norm(reflect_dir)
            
            # Косинус угла между отраженным лучом и направлением зрения
            spec_angle = max(0, np.dot(view_dir, reflect_dir))
            specular = self.specular_intensity * (spec_angle ** self.shininess)
        
        # Итоговая интенсивность
        intensity = ambient + diffuse * self.light.intensity + specular
        
        # Цвет вершины
        color = (
            material_color[0] * intensity * self.light.color[0],
            material_color[1] * intensity * self.light.color[1],
            material_color[2] * intensity * self.light.color[2]
        )
        
        return color
    
    def shade_triangle(self, screen, v0, v1, v2, p0, p1, p2, material_color):
        """Закраска треугольника методом Фонга с интерполяцией нормалей"""
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
        
        # Нормали вершин
        n0 = np.array([v0.normal_x, v0.normal_y, v0.normal_z])
        n1 = np.array([v1.normal_x, v1.normal_y, v1.normal_z])
        n2 = np.array([v2.normal_x, v2.normal_y, v2.normal_z])
        
        # Позиции вершин в пространстве
        pos0 = np.array([v0.x, v0.y, v0.z])
        pos1 = np.array([v1.x, v1.y, v1.z])
        pos2 = np.array([v2.x, v2.y, v2.z])
        
        # Растеризация с интерполяцией нормалей
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                # Барицентрические координаты
                w1 = ((p1[1] - p2[1]) * (x - p2[0]) + (p2[0] - p1[0]) * (y - p2[1])) * inv_area
                w2 = ((p2[1] - p0[1]) * (x - p2[0]) + (p0[0] - p2[0]) * (y - p2[1])) * inv_area
                w0 = 1 - w1 - w2
                
                # Проверка внутри треугольника
                if w0 >= -0.001 and w1 >= -0.001 and w2 >= -0.001:
                    # Интерполяция позиции и нормали
                    interp_pos = w0 * pos0 + w1 * pos1 + w2 * pos2
                    interp_normal = w0 * n0 + w1 * n1 + w2 * n2
                    
                    # Нормализация интерполированной нормали
                    normal_len = np.linalg.norm(interp_normal)
                    if normal_len > 0:
                        interp_normal = interp_normal / normal_len
                    
                    # Создаем виртуальную вершину для расчета цвета
                    class InterpolatedVertex:
                        def __init__(self, pos, normal):
                            self.x, self.y, self.z = pos
                            self.normal_x, self.normal_y, self.normal_z = normal
                    
                    interp_vertex = InterpolatedVertex(interp_pos, interp_normal)
                    
                    # Расчет цвета по модели Фонга
                    color_rgb = self.calculate_vertex_color(interp_vertex, material_color, use_phong=True)
                    
                    # Преобразование в формат Pygame
                    color = (
                        int(color_rgb[0] * 255),
                        int(color_rgb[1] * 255),
                        int(color_rgb[2] * 255)
                    )
                    
                    # Ограничение значений
                    color = (
                        max(0, min(255, color[0])),
                        max(0, min(255, color[1])),
                        max(0, min(255, color[2]))
                    )
                    
                    # Рисуем пиксель
                    screen.set_at((x, y), color)