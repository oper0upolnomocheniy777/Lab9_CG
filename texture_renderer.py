# texture_renderer.py
import numpy as np
import pygame
from lighting import PhongShader

class Texture:
    """Класс для работы с текстурами"""
    
    def __init__(self, width, height, color=(255, 255, 255)):
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height))
        self.surface.fill(color)
    
    def create_checkerboard(self, tile_size=16):
        """Создание шахматной текстуры"""
        for y in range(0, self.height, tile_size):
            for x in range(0, self.width, tile_size):
                color = (200, 200, 200) if ((x // tile_size) + (y // tile_size)) % 2 == 0 else (100, 100, 100)
                rect = pygame.Rect(x, y, tile_size, tile_size)
                pygame.draw.rect(self.surface, color, rect)
    
    def load_from_file(self, filename):
        """Загрузка текстуры из файла"""
        try:
            self.surface = pygame.image.load(filename).convert()
            self.width = self.surface.get_width()
            self.height = self.surface.get_height()
            print(f"✓ Текстура загружена: {filename} ({self.width}x{self.height})")
            return True
        except Exception as e:
            print(f"✗ Ошибка загрузки текстуры {filename}: {e}")
            return False
    
    def get_color(self, u, v, interpolation='nearest'):
        """Получение цвета текстуры по координатам (u, v)"""
        # Приведение координат к диапазону [0, 1]
        u = u % 1.0
        v = v % 1.0
        
        # Преобразование в координаты текстуры
        tex_x = int(u * (self.width - 1))
        tex_y = int(v * (self.height - 1))
        
        # Ограничение индексов
        tex_x = max(0, min(self.width - 1, tex_x))
        tex_y = max(0, min(self.height - 1, tex_y))
        
        # Получение цвета
        if interpolation == 'bilinear':
            # Билинейная интерполяция
            x0 = int(np.floor(u * (self.width - 1)))
            y0 = int(np.floor(v * (self.height - 1)))
            x1 = min(self.width - 1, x0 + 1)
            y1 = min(self.height - 1, y0 + 1)
            
            # Коэффициенты интерполяции
            a = u * (self.width - 1) - x0
            b = v * (self.height - 1) - y0
            
            # Цвета угловых пикселей
            c00 = self.surface.get_at((x0, y0))
            c01 = self.surface.get_at((x0, y1))
            c10 = self.surface.get_at((x1, y0))
            c11 = self.surface.get_at((x1, y1))
            
            # Линейная интерполяция
            c0 = (
                c00[0] * (1 - b) + c01[0] * b,
                c00[1] * (1 - b) + c01[1] * b,
                c00[2] * (1 - b) + c01[2] * b
            )
            
            c1 = (
                c10[0] * (1 - b) + c11[0] * b,
                c10[1] * (1 - b) + c11[1] * b,
                c10[2] * (1 - b) + c11[2] * b
            )
            
            color = (
                int(c0[0] * (1 - a) + c1[0] * a),
                int(c0[1] * (1 - a) + c1[1] * a),
                int(c0[2] * (1 - a) + c1[2] * a)
            )
        else:
            # Метод ближайшего соседа
            color = self.surface.get_at((tex_x, tex_y))
        
        return color[:3]  # Возвращаем только RGB

class TexturedRenderer:
    """Рендерер с поддержкой текстурирования"""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.half_width = width / 2
        self.half_height = height / 2
        
        # Текстуры
        self.textures = {
            'checkerboard': Texture(256, 256),
            'test': Texture(128, 128, (200, 100, 100))
        }
        self.textures['checkerboard'].create_checkerboard()
        self.current_texture = self.textures['checkerboard']
        
        # Освещение
        self.phong_shader = PhongShader(
            light=None,
            ambient_intensity=0.3,
            specular_intensity=0.5,
            shininess=32
        )
        
        # Фон
        self.bg_color = (20, 25, 35)
    
    def set_light(self, light):
        """Установка источника света"""
        self.phong_shader.light = light
    
    def set_view_pos(self, view_pos):
        """Установка позиции камеры"""
        self.phong_shader.set_view_pos(view_pos)
    
    def project_point(self, point, view_proj_matrix):
        """Проецирование 3D точки в 2D"""
        homogeneous = point.to_homogeneous()
        transformed = view_proj_matrix @ homogeneous
        
        # Координаты экрана (ортографическая проекция)
        x = transformed[0] * self.half_width + self.half_width
        y = -transformed[1] * self.half_height + self.half_height
        
        return (x, y)
    
    def is_face_visible(self, face, vertices):
        """Отсечение нелицевых граней"""
        if len(face.vertex_indices) < 3:
            return False
        
        # Векторы грани
        v0 = vertices[face.vertex_indices[0]]
        v1 = vertices[face.vertex_indices[1]]
        v2 = vertices[face.vertex_indices[2]]
        
        # Векторы двух ребер
        edge1 = np.array([v1.x - v0.x, v1.y - v0.y, v1.z - v0.z])
        edge2 = np.array([v2.x - v0.x, v2.y - v0.y, v2.z - v0.z])
        
        # Нормаль грани
        normal = np.cross(edge1, edge2)
        normal_len = np.linalg.norm(normal)
        
        if normal_len > 0:
            normal = normal / normal_len
        
        # Вектор к камере (камера смотрит по -Z)
        view_dir = np.array([0, 0, -1])
        
        # Грань видима, если угол меньше 90 градусов
        return np.dot(normal, view_dir) < 0
    
    def render_textured_triangle(self, screen, v0, v1, v2, p0, p1, p2, texture):
        """Рендеринг текстурированного треугольника"""
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
        
        # Текстурные координаты вершин
        tex0 = (v0.tex_u, v0.tex_v) if hasattr(v0, 'tex_u') else (0, 0)
        tex1 = (v1.tex_u, v1.tex_v) if hasattr(v1, 'tex_u') else (0, 0)
        tex2 = (v2.tex_u, v2.tex_v) if hasattr(v2, 'tex_u') else (0, 0)
        
        # Нормали вершин
        n0 = np.array([v0.normal_x, v0.normal_y, v0.normal_z])
        n1 = np.array([v1.normal_x, v1.normal_y, v1.normal_z])
        n2 = np.array([v2.normal_x, v2.normal_y, v2.normal_z])
        
        # Позиции вершин в пространстве
        pos0 = np.array([v0.x, v0.y, v0.z]) if hasattr(v0, 'x') else np.array([0, 0, 0])
        pos1 = np.array([v1.x, v1.y, v1.z]) if hasattr(v1, 'x') else np.array([0, 0, 0])
        pos2 = np.array([v2.x, v2.y, v2.z]) if hasattr(v2, 'x') else np.array([0, 0, 0])
        
        # Растеризация с интерполяцией текстурных координат и нормалей
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                # Барицентрические координаты
                w1 = ((p1[1] - p2[1]) * (x - p2[0]) + (p2[0] - p1[0]) * (y - p2[1])) * inv_area
                w2 = ((p2[1] - p0[1]) * (x - p2[0]) + (p0[0] - p2[0]) * (y - p2[1])) * inv_area
                w0 = 1 - w1 - w2
                
                # Проверка внутри треугольника
                if w0 >= -0.001 and w1 >= -0.001 and w2 >= -0.001:
                    # ИНТЕРПОЛЯЦИЯ ТЕКСТУРНЫХ КООРДИНАТ
                    tex_u = w0 * tex0[0] + w1 * tex1[0] + w2 * tex2[0]
                    tex_v = w0 * tex0[1] + w1 * tex1[1] + w2 * tex2[1]
                    
                    # Интерполяция позиции и нормали
                    interp_pos = w0 * pos0 + w1 * pos1 + w2 * pos2
                    interp_normal = w0 * n0 + w1 * n1 + w2 * n2
                    
                    # Нормализация интерполированной нормали
                    normal_len = np.linalg.norm(interp_normal)
                    if normal_len > 0:
                        interp_normal = interp_normal / normal_len
                    
                    # Создаем виртуальную вершину для расчета освещения
                    class InterpolatedVertex:
                        def __init__(self, pos, normal):
                            self.x, self.y, self.z = pos
                            self.normal_x, self.normal_y, self.normal_z = normal
                    
                    interp_vertex = InterpolatedVertex(interp_pos, interp_normal)
                    
                    # Получение цвета текстуры
                    tex_color = texture.get_color(tex_u, tex_v, interpolation='bilinear')
                    
                    # Преобразование цвета текстуры в диапазон [0, 1]
                    tex_color_normalized = (
                        tex_color[0] / 255.0,
                        tex_color[1] / 255.0,
                        tex_color[2] / 255.0
                    )
                    
                    # Расчет освещения по модели Фонга
                    lit_color = self.phong_shader.calculate_vertex_color(
                        interp_vertex,
                        tex_color_normalized,
                        use_phong=True
                    )
                    
                    # Преобразование обратно в RGB
                    final_color = (
                        int(lit_color[0] * 255),
                        int(lit_color[1] * 255),
                        int(lit_color[2] * 255)
                    )
                    
                    # Ограничение значений
                    final_color = (
                        max(0, min(255, final_color[0])),
                        max(0, min(255, final_color[1])),
                        max(0, min(255, final_color[2]))
                    )
                    
                    # Рисуем пиксель
                    screen.set_at((x, y), final_color)