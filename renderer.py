# renderer.py
import numpy as np
import pygame
from lighting import Light, LambertShader, GouraudShader, PhongShader

class Renderer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.half_width = width / 2
        self.half_height = height / 2
        
        # Цвета для моделей
        self.colors = [
            (200, 100, 100),  # Красный
            (100, 200, 100),  # Зеленый
            (100, 100, 200),  # Синий
            (200, 200, 100),  # Желтый
            (200, 100, 200),  # Фиолетовый
            (100, 200, 200),  # Голубой
        ]
        self.current_color_idx = 0
        
        # Освещение
        self.light = Light(position=[3, 3, 3], color=(1.0, 1.0, 1.0), intensity=0.8)
        self.lambert_shader = LambertShader(self.light, ambient_intensity=0.3)
        self.gouraud_shader = GouraudShader(self.lambert_shader)
        self.phong_shader = PhongShader(self.lambert_shader)  # Добавляем шейдер Фонга
        
        # Режимы рендеринга (0=Flat, 1=Gouraud, 2=Phong)
        self.shading_mode = 1  # Изначально Гуро
        self.show_light_info = True
        
        # Фон
        self.bg_color = (20, 25, 35)
        
        # Кэш для цветов вершин (чтобы не пересчитывать каждый кадр)
        self.vertex_colors_cache = {}
        self.last_transform_hash = None
    
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
        
        # Берем первые три вершины грани
        v0 = vertices[face.vertex_indices[0]]
        v1 = vertices[face.vertex_indices[1]]
        v2 = vertices[face.vertex_indices[2]]
        
        # Векторы двух ребер
        edge1 = np.array([v1.x - v0.x, v1.y - v0.y, v1.z - v0.z])
        edge2 = np.array([v2.x - v0.x, v2.y - v0.y, v2.z - v0.z])
        
        # Векторное произведение дает нормаль к плоскости грани
        normal = np.cross(edge1, edge2)
        
        # Нормализация
        length = np.linalg.norm(normal)
        if length > 0:
            normal = normal / length
        
        # Для ортографической проекции проверяем Z-компоненту нормали
        # Камера смотрит по -Z, поэтому грань видима когда normal.z < 0
        return normal[2] < 0
    
    def calculate_vertex_colors(self, model, material_color, transform_hash):
        """Вычисление цветов вершин по модели Ламберта с кэшированием"""
        # Проверяем кэш
        if transform_hash in self.vertex_colors_cache:
            vertex_colors, colors_dict = self.vertex_colors_cache[transform_hash]
            # Восстанавливаем цвета в вершинах
            for i, vertex in enumerate(model.vertices):
                if i < len(vertex_colors):
                    vertex.color = vertex_colors[i]
            return vertex_colors
        
        material_color_rgb = (
            material_color[0] / 255.0,
            material_color[1] / 255.0,
            material_color[2] / 255.0
        )
        
        vertex_colors = []
        colors_dict = {}
        
        for i, vertex in enumerate(model.vertices):
            # Если у вершины нет нормалей, устанавливаем простую
            if not hasattr(vertex, 'normal_x'):
                vertex.normal_x = 0
                vertex.normal_y = 0
                vertex.normal_z = 1
            elif not hasattr(vertex, 'normal'):
                # Нормализуем нормаль
                normal_len = np.sqrt(vertex.normal_x**2 + vertex.normal_y**2 + vertex.normal_z**2)
                if normal_len > 0:
                    vertex.normal_x /= normal_len
                    vertex.normal_y /= normal_len
                    vertex.normal_z /= normal_len
            
            color = self.lambert_shader.calculate_vertex_color(vertex, material_color_rgb)
            
            # Преобразование в формат Pygame
            vertex_color = (
                int(color[0] * 255),
                int(color[1] * 255),
                int(color[2] * 255)
            )
            
            # Ограничиваем значения
            vertex_color = (
                max(0, min(255, vertex_color[0])),
                max(0, min(255, vertex_color[1])),
                max(0, min(255, vertex_color[2]))
            )
            
            vertex.color = vertex_color
            vertex_colors.append(vertex_color)
            colors_dict[i] = vertex_color
        
        # Сохраняем в кэш
        self.vertex_colors_cache[transform_hash] = (vertex_colors, colors_dict)
        self.last_transform_hash = transform_hash
        
        return vertex_colors
    
    def get_transform_hash(self, model, camera, base_color_idx):
        """Создает хэш для текущего состояния преобразований"""
        # Простой хэш на основе углов, цвета и позиции камеры
        return hash((
            id(model),
            base_color_idx,
            camera.rotation_x, camera.rotation_y, camera.rotation_z,
            camera.scale
        ))
    
    def render_triangle_gouraud(self, screen, v0, v1, v2, p0, p1, p2):
        """Рендеринг треугольника с Гуро шейдингом"""
        self.gouraud_shader.shade_triangle(screen, v0, v1, v2, p0, p1, p2)
    
    def render_triangle_phong(self, screen, v0, v1, v2, p0, p1, p2, material_color):
        """Рендеринг треугольника с Фонг шейдингом"""
        self.phong_shader.shade_triangle_phong(screen, v0, v1, v2, p0, p1, p2, material_color)
    
    def render_triangle_flat(self, screen, face_points, color):
        """Рендеринг треугольника с плоским затенением"""
        pygame.draw.polygon(screen, color, face_points)
    
    def next_color(self):
        """Переключение на следующий цвет"""
        self.current_color_idx = (self.current_color_idx + 1) % len(self.colors)
        # Очищаем кэш при смене цвета
        self.vertex_colors_cache.clear()
    
    def get_current_color_name(self):
        """Название текущего цвета"""
        color_names = ["Красный", "Зеленый", "Синий", "Желтый", "Фиолетовый", "Голубой"]
        return color_names[self.current_color_idx]
    
    def toggle_shading_mode(self):
        """Переключение режима шейдинга"""
        self.shading_mode = (self.shading_mode + 1) % 3
        modes = ["Плоский", "Гуро", "Фонг"]
        return modes[self.shading_mode]
    
    def get_shading_mode_name(self):
        """Получить название текущего режима шейдинга"""
        modes = ["Плоский", "Гуро", "Фонг"]
        return modes[self.shading_mode]
    
    def render(self, screen, model, camera, show_wireframe=True, 
               show_filled=True, backface_culling=True, show_normals=False):
        """Основной метод рендеринга"""
        screen.fill(self.bg_color)
        
        view_proj_matrix = camera.get_view_projection_matrix()
        
        # Проецируем все вершины
        projected = []
        for vertex in model.vertices:
            projected.append(self.project_point(vertex, view_proj_matrix))
        
        # Создаем хэш для текущего состояния
        transform_hash = self.get_transform_hash(model, camera, self.current_color_idx)
        
        # Вычисляем цвета вершин по модели Ламберта (с кэшированием)
        base_color = self.colors[self.current_color_idx]
        
        # Преобразуем цвет материала в формат для шейдеров (0-1)
        material_color_rgb = (
            base_color[0] / 255.0,
            base_color[1] / 255.0,
            base_color[2] / 255.0
        )
        
        vertex_colors = self.calculate_vertex_colors(model, base_color, transform_hash)
        
        visible = 0
        hidden = 0
        
        # Рендерим грани
        for face in model.faces:
            # Отсечение нелицевых граней
            is_visible = True
            if backface_culling:
                is_visible = self.is_face_visible(face, model.vertices)
                if not is_visible:
                    hidden += 1
                    continue
            
            visible += 1
            
            # Координаты грани
            face_points = []
            face_vertices = []
            for idx in face.vertex_indices:
                if 0 <= idx < len(projected):
                    face_points.append(projected[idx])
                    if idx < len(model.vertices):
                        face_vertices.append(model.vertices[idx])
            
            if len(face_points) < 3:
                continue
            
            # Заполнение
            if show_filled and is_visible:
                if len(face_vertices) >= 3:
                    if self.shading_mode == 0:  # Flat shading
                        face_vertex_colors = []
                        for idx in face.vertex_indices:
                            if idx < len(vertex_colors):
                                face_vertex_colors.append(vertex_colors[idx])
                        
                        if face_vertex_colors:
                            avg_color = (
                                sum(c[0] for c in face_vertex_colors) // len(face_vertex_colors),
                                sum(c[1] for c in face_vertex_colors) // len(face_vertex_colors),
                                sum(c[2] for c in face_vertex_colors) // len(face_vertex_colors)
                            )
                            self.render_triangle_flat(screen, face_points, avg_color)
                    
                    elif self.shading_mode == 1:  # Gouraud shading
                        if len(face_vertices) == 3:
                            self.render_triangle_gouraud(
                                screen, 
                                face_vertices[0], face_vertices[1], face_vertices[2],
                                face_points[0], face_points[1], face_points[2]
                            )
                        elif len(face_vertices) == 4:
                            # Разбиваем четырехугольник на два треугольника
                            self.render_triangle_gouraud(
                                screen,
                                face_vertices[0], face_vertices[1], face_vertices[2],
                                face_points[0], face_points[1], face_points[2]
                            )
                            self.render_triangle_gouraud(
                                screen,
                                face_vertices[0], face_vertices[2], face_vertices[3],
                                face_points[0], face_points[2], face_points[3]
                            )
                    
                    elif self.shading_mode == 2:  # Phong shading
                        if len(face_vertices) == 3:
                            self.render_triangle_phong(
                                screen, 
                                face_vertices[0], face_vertices[1], face_vertices[2],
                                face_points[0], face_points[1], face_points[2],
                                material_color_rgb
                            )
                        elif len(face_vertices) == 4:
                            # Разбиваем четырехугольник на два треугольника
                            self.render_triangle_phong(
                                screen,
                                face_vertices[0], face_vertices[1], face_vertices[2],
                                face_points[0], face_points[1], face_points[2],
                                material_color_rgb
                            )
                            self.render_triangle_phong(
                                screen,
                                face_vertices[0], face_vertices[2], face_vertices[3],
                                face_points[0], face_points[2], face_points[3],
                                material_color_rgb
                            )
            
            # Каркас
            if show_wireframe:
                line_color = (100, 100, 100) if not is_visible else (255, 255, 255)
                pygame.draw.polygon(screen, line_color, face_points, 1)
            
            # Нормали
            if show_normals and is_visible and len(face.vertex_indices) >= 3:
                # Вычисляем нормаль грани
                v0 = model.vertices[face.vertex_indices[0]]
                v1 = model.vertices[face.vertex_indices[1]]
                v2 = model.vertices[face.vertex_indices[2]]
                
                edge1 = np.array([v1.x - v0.x, v1.y - v0.y, v1.z - v0.z])
                edge2 = np.array([v2.x - v0.x, v2.y - v0.y, v2.z - v0.z])
                
                normal = np.cross(edge1, edge2)
                length = np.linalg.norm(normal)
                if length > 0:
                    normal = normal / length
                
                # Центр грани
                center_x = sum(p[0] for p in face_points) / len(face_points)
                center_y = sum(p[1] for p in face_points) / len(face_points)
                
                # Отображение нормали
                scale = 20
                end_x = center_x + normal[0] * scale
                end_y = center_y - normal[1] * scale
                
                pygame.draw.line(screen, (255, 255, 0), 
                               (center_x, center_y), (end_x, end_y), 2)
                pygame.draw.circle(screen, (255, 200, 0), (int(center_x), int(center_y)), 3)
        
        # Отображение информации об освещении
        if self.show_light_info:
            self.draw_light_info(screen)
        
        return visible, hidden
    
    def draw_light_info(self, screen):
        """Отображение информации об освещении"""
        font = pygame.font.Font(None, 24)
        
        info_lines = [
            f"Режим шейдинга: {self.get_shading_mode_name()} (G)",
            f"Источник света: ({self.light.position[0]:.1f}, {self.light.position[1]:.1f}, {self.light.position[2]:.1f})",
            f"Интенсивность: {self.light.intensity:.1f}",
            f"Ambient: {self.lambert_shader.ambient_intensity:.1f}",
        ]
        
        # Фон для информации
        info_bg = pygame.Surface((300, 100), pygame.SRCALPHA)
        info_bg.fill((0, 0, 0, 150))
        screen.blit(info_bg, (10, self.height - 110))
        
        for i, line in enumerate(info_lines):
            text = font.render(line, True, (200, 255, 200))
            screen.blit(text, (20, self.height - 100 + i * 25))