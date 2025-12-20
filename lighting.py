# lighting.py
import numpy as np
import pygame

class Light:
    def __init__(self, position, color=(1.0, 1.0, 1.0), intensity=1.0):
        self.position = np.array(position, dtype=float)
        self.color = np.array(color, dtype=float)
        self.intensity = intensity

class LambertShader:
    """Модель освещения Ламберта"""
    
    def __init__(self, light, ambient_intensity=0.2):
        self.light = light
        self.ambient_intensity = ambient_intensity
    
    def calculate_vertex_color(self, vertex, material_color):
        """Вычисление цвета вершины по модели Ламберта"""
        # Позиция вершины
        vertex_pos = np.array([vertex.x, vertex.y, vertex.z], dtype=float)
        
        # Направление к свету
        light_dir = self.light.position - vertex_pos
        
        # Нормализация направления света
        light_len = np.linalg.norm(light_dir)
        if light_len > 0:
            light_dir = light_dir / light_len
        
        # Нормаль вершины
        normal = np.array([vertex.normal_x, vertex.normal_y, vertex.normal_z], dtype=float)
        
        # Нормализуем нормаль (на всякий случай)
        normal_len = np.linalg.norm(normal)
        if normal_len > 0:
            normal = normal / normal_len
        
        # Диффузная составляющая (cos угла между нормалью и светом)
        diffuse = max(0.0, np.dot(normal, light_dir))
        
        # Итоговая интенсивность
        intensity = self.ambient_intensity + diffuse * self.light.intensity
        intensity = max(0.0, min(1.0, intensity))
        
        # Цвет вершины
        color = (
            material_color[0] * intensity,
            material_color[1] * intensity,
            material_color[2] * intensity
        )
        
        # Ограничиваем значения
        color = (
            max(0.0, min(1.0, color[0])),
            max(0.0, min(1.0, color[1])),
            max(0.0, min(1.0, color[2]))
        )
        
        return color

class GouraudShader:
    """Правильная реализация шейдинга Гуро с scanline алгоритмом"""
    
    def __init__(self, lambert_shader):
        self.lambert_shader = lambert_shader
    
    def scanline_triangle(self, screen, p0, p1, p2, c0, c1, c2):
        """Scanline алгоритм для заливки треугольника с интерполяцией цветов"""
        # Сортируем вершины по Y
        points = [(p0, c0), (p1, c1), (p2, c2)]
        points.sort(key=lambda p: p[0][1])
        
        (pt_top, c_top), (pt_mid, c_mid), (pt_bot, c_bot) = points
        
        # Проверка на вырожденный треугольник
        if abs(pt_top[1] - pt_bot[1]) < 0.5:
            return
        
        # Преобразуем в numpy для быстрых вычислений
        pt_top_np = np.array(pt_top, dtype=float)
        pt_mid_np = np.array(pt_mid, dtype=float)
        pt_bot_np = np.array(pt_bot, dtype=float)
        
        # Функция линейной интерполяции
        def lerp(a, b, t):
            return a + t * (b - a)
        
        # Функция интерполяции вдоль ребра
        def interpolate_edge(p_start, p_end, c_start, c_end, y):
            if abs(p_end[1] - p_start[1]) < 0.5:
                return p_start[0], c_start
            
            t = (y - p_start[1]) / (p_end[1] - p_start[1])
            t = max(0.0, min(1.0, t))
            
            x = lerp(p_start[0], p_end[0], t)
            r = lerp(c_start[0], c_end[0], t)
            g = lerp(c_start[1], c_end[1], t)
            b = lerp(c_start[2], c_end[2], t)
            
            return x, (int(r), int(g), int(b))
        
        # Верхняя половина треугольника (от top до mid)
        if pt_mid[1] > pt_top[1]:
            y_start = int(pt_top[1])
            y_end = int(pt_mid[1])
            
            for y in range(y_start, y_end + 1):
                if y < 0 or y >= screen.get_height():
                    continue
                
                # Интерполяция по левому и правому краям
                if abs(pt_mid[1] - pt_top[1]) > 0.5:
                    t1 = (y - pt_top[1]) / (pt_mid[1] - pt_top[1])
                else:
                    t1 = 0.0
                
                if abs(pt_bot[1] - pt_top[1]) > 0.5:
                    t2 = (y - pt_top[1]) / (pt_bot[1] - pt_top[1])
                else:
                    t2 = 0.0
                
                t1 = max(0.0, min(1.0, t1))
                t2 = max(0.0, min(1.0, t2))
                
                x1 = lerp(pt_top[0], pt_mid[0], t1)
                x2 = lerp(pt_top[0], pt_bot[0], t2)
                
                # Интерполяция цветов
                r1 = lerp(c_top[0], c_mid[0], t1)
                g1 = lerp(c_top[1], c_mid[1], t1)
                b1 = lerp(c_top[2], c_mid[2], t1)
                
                r2 = lerp(c_top[0], c_bot[0], t2)
                g2 = lerp(c_top[1], c_bot[1], t2)
                b2 = lerp(c_top[2], c_bot[2], t2)
                
                color1 = (int(r1), int(g1), int(b1))
                color2 = (int(r2), int(g2), int(b2))
                
                # Убедимся, что x1 слева, x2 справа
                if x1 > x2:
                    x1, x2 = x2, x1
                    color1, color2 = color2, color1
                
                # Рисуем горизонтальную линию
                x_start = max(0, int(x1))
                x_end = min(screen.get_width() - 1, int(x2))
                
                if x_end > x_start:
                    # Линейная интерполяция цвета вдоль линии
                    for x in range(x_start, x_end + 1):
                        if x2 != x1:
                            t_line = (x - x1) / (x2 - x1)
                        else:
                            t_line = 0.0
                        
                        t_line = max(0.0, min(1.0, t_line))
                        
                        r = lerp(color1[0], color2[0], t_line)
                        g = lerp(color1[1], color2[1], t_line)
                        b = lerp(color1[2], color2[2], t_line)
                        
                        color = (int(r), int(g), int(b))
                        screen.set_at((x, y), color)
        
        # Нижняя половина треугольника (от mid до bot)
        if pt_bot[1] > pt_mid[1]:
            y_start = int(pt_mid[1])
            y_end = int(pt_bot[1])
            
            for y in range(y_start, y_end + 1):
                if y < 0 or y >= screen.get_height():
                    continue
                
                # Интерполяция по левому и правому краям
                if abs(pt_bot[1] - pt_mid[1]) > 0.5:
                    t1 = (y - pt_mid[1]) / (pt_bot[1] - pt_mid[1])
                else:
                    t1 = 0.0
                
                if abs(pt_bot[1] - pt_top[1]) > 0.5:
                    t2 = (y - pt_top[1]) / (pt_bot[1] - pt_top[1])
                else:
                    t2 = 0.0
                
                t1 = max(0.0, min(1.0, t1))
                t2 = max(0.0, min(1.0, t2))
                
                x1 = lerp(pt_mid[0], pt_bot[0], t1)
                x2 = lerp(pt_top[0], pt_bot[0], t2)
                
                # Интерполяция цветов
                r1 = lerp(c_mid[0], c_bot[0], t1)
                g1 = lerp(c_mid[1], c_bot[1], t1)
                b1 = lerp(c_mid[2], c_bot[2], t1)
                
                r2 = lerp(c_top[0], c_bot[0], t2)
                g2 = lerp(c_top[1], c_bot[1], t2)
                b2 = lerp(c_top[2], c_bot[2], t2)
                
                color1 = (int(r1), int(g1), int(b1))
                color2 = (int(r2), int(g2), int(b2))
                
                # Убедимся, что x1 слева, x2 справа
                if x1 > x2:
                    x1, x2 = x2, x1
                    color1, color2 = color2, color1
                
                # Рисуем горизонтальную линию
                x_start = max(0, int(x1))
                x_end = min(screen.get_width() - 1, int(x2))
                
                if x_end > x_start:
                    # Линейная интерполяция цвета вдоль линии
                    for x in range(x_start, x_end + 1):
                        if x2 != x1:
                            t_line = (x - x1) / (x2 - x1)
                        else:
                            t_line = 0.0
                        
                        t_line = max(0.0, min(1.0, t_line))
                        
                        r = lerp(color1[0], color2[0], t_line)
                        g = lerp(color1[1], color2[1], t_line)
                        b = lerp(color1[2], color2[2], t_line)
                        
                        color = (int(r), int(g), int(b))
                        screen.set_at((x, y), color)
    
    def shade_triangle(self, screen, v0, v1, v2, p0, p1, p2):
        """Закраска треугольника методом Гуро"""
        # Получаем цвета вершин
        c0 = v0.color if hasattr(v0, 'color') and v0.color else (128, 128, 128)
        c1 = v1.color if hasattr(v1, 'color') and v1.color else (128, 128, 128)
        c2 = v2.color if hasattr(v2, 'color') and v2.color else (128, 128, 128)
        
        # Используем scanline алгоритм
        self.scanline_triangle(screen, p0, p1, p2, c0, c1, c2)