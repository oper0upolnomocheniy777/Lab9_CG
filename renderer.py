# renderer.py
import numpy as np
import pygame
from lighting import Light, LambertShader, GouraudShader
from texture import Texture  # Импортируем класс текстуры

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
        
        # Режимы рендеринга
        self.use_gouraud = True
        self.show_light_info = True
        self.use_texture = True  # Включить текстурирование по умолчанию
        self.texture_mode = 0  # 0 - шахматная, 1 - градиент, 2 - цветная
        
        # Текстура
        self.texture = Texture()
        
        # Фон
        self.bg_color = (20, 25, 35)
    
    def project_point(self, point, view_proj_matrix):
        """Проецирование 3D точки в 2D"""
        homogeneous = point.to_homogeneous()
        transformed = view_proj_matrix @ homogeneous
        
        # Координаты экрана (ортографическая проекция)
        x = transformed[0] * self.half_width + self.half_width
        y = -transformed[1] * self.half_height + self.half_height
        
        return (x, y)
    
    def is_face_visible(self, face):
        """Правильное отсечение нелицевых граней"""
        return face.normal_z < 0
    
    def calculate_vertex_colors(self, model, material_color):
        """Вычисление цветов вершин по модели Ламберта"""
        vertex_colors = []
        material_color_rgb = (
            material_color[0] / 255.0,
            material_color[1] / 255.0,
            material_color[2] / 255.0
        )
        
        for vertex in model.vertices:
            color = self.lambert_shader.calculate_vertex_color(
                vertex, material_color_rgb
            )
            
            # Преобразование в формат Pygame
            vertex_color = (
                int(color[0] * 255),
                int(color[1] * 255),
                int(color[2] * 255)
            )
            vertex.color = vertex_color
            vertex_colors.append(vertex_color)
        
        return vertex_colors
    
    def render_triangle_gouraud(self, screen, v0, v1, v2, p0, p1, p2):
        """Рендеринг треугольника с Гуро шейдингом"""
        self.gouraud_shader.shade_triangle(screen, v0, v1, v2, p0, p1, p2)
    
    def render_triangle_flat(self, screen, face_points, color):
        """Рендеринг треугольника с плоским затенением"""
        pygame.draw.polygon(screen, color, face_points)
    
    def render_textured_triangle(self, screen, v0, v1, v2, p0, p1, p2, t0, t1, t2):
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
        
        # Растеризация с интерполяцией текстурных координат
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                # Барицентрические координаты
                w1 = ((p1[1] - p2[1]) * (x - p2[0]) + (p2[0] - p1[0]) * (y - p2[1])) * inv_area
                w2 = ((p2[1] - p0[1]) * (x - p2[0]) + (p0[0] - p2[0]) * (y - p2[1])) * inv_area
                w0 = 1 - w1 - w2
                
                # Проверка внутри треугольника
                if w0 >= -0.001 and w1 >= -0.001 and w2 >= -0.001:
                    # Интерполяция текстурных координат
                    u = w0 * t0[0] + w1 * t1[0] + w2 * t2[0]
                    v = w0 * t0[1] + w1 * t1[1] + w2 * t2[1]
                    
                    # Получаем цвет из текстуры
                    texture_color = self.texture.get_color_bilinear(u, v)
                    
                    # Рисуем пиксель
                    screen.set_at((x, y), texture_color)
    
    def render_textured_quad(self, screen, vertices, points, tex_coords):
        """Рендеринг текстурированного четырехугольника (разбивается на 2 треугольника)"""
        if len(points) >= 3:
            # Первый треугольник
            self.render_textured_triangle(
                screen,
                vertices[0], vertices[1], vertices[2],
                points[0], points[1], points[2],
                tex_coords[0], tex_coords[1], tex_coords[2]
            )
        
        if len(points) >= 4:
            # Второй треугольник
            self.render_textured_triangle(
                screen,
                vertices[0], vertices[2], vertices[3],
                points[0], points[2], points[3],
                tex_coords[0], tex_coords[2], tex_coords[3]
            )
    
    # ДОБАВЬТЕ ЭТИ МЕТОДЫ, ЕСЛИ ИХ НЕТ:
    
    def next_color(self):
        """Переключение на следующий цвет"""
        self.current_color_idx = (self.current_color_idx + 1) % len(self.colors)
    
    def get_current_color_name(self):
        """Название текущего цвета"""
        color_names = ["Красный", "Зеленый", "Синий", "Желтый", "Фиолетовый", "Голубой"]
        return color_names[self.current_color_idx]
    
    def toggle_shading_mode(self):
        """Переключение режима шейдинга"""
        self.use_gouraud = not self.use_gouraud
        return "Гуро" if self.use_gouraud else "Плоский"
    
    def toggle_texture_mode(self):
        """Переключение режима текстуры"""
        self.texture_mode = (self.texture_mode + 1) % 3
        
        if self.texture_mode == 0:
            self.texture.generate_default_texture()
            return "Шахматная текстура"
        elif self.texture_mode == 1:
            self.texture.generate_gradient()
            return "Градиентная текстура"
        else:
            self.texture.generate_checkerboard()
            return "Простая шахматка"
    
    def toggle_texturing(self):
        """Включение/выключение текстурирования"""
        self.use_texture = not self.use_texture
        return "ВКЛ" if self.use_texture else "ВЫКЛ"
    
    def render(self, screen, model, camera, show_wireframe=True, 
               show_filled=True, backface_culling=True, show_normals=False):
        """Основной метод рендеринга с поддержкой текстурирования"""
        screen.fill(self.bg_color)
        
        view_proj_matrix = camera.get_view_projection_matrix()
        
        # Проецируем все вершины
        projected = []
        for vertex in model.vertices:
            projected.append(self.project_point(vertex, view_proj_matrix))
        
        # Вычисляем цвета вершин по модели Ламберта
        base_color = self.colors[self.current_color_idx]
        vertex_colors = self.calculate_vertex_colors(model, base_color)
        
        visible = 0
        hidden = 0
        
        # Рендерим грани
        for i, face in enumerate(model.faces):
            # Отсечение нелицевых граней
            is_visible = True
            if backface_culling:
                is_visible = self.is_face_visible(face)
                if not is_visible:
                    hidden += 1
                    continue
            
            visible += 1
            
            # Координаты грани
            face_points = []
            face_vertices = []
            face_tex_coords = []
            
            for idx, vertex_idx in enumerate(face.vertex_indices):
                if 0 <= vertex_idx < len(projected):
                    face_points.append(projected[vertex_idx])
                    face_vertices.append(model.vertices[vertex_idx])
                    
                    # Получаем текстурные координаты для этой вершины
                    if (model.has_texture_coords() and 
                        idx < len(face.tex_indices) and 
                        face.tex_indices[idx] < len(model.tex_coords)):
                        tex_idx = face.tex_indices[idx]
                        face_tex_coords.append(model.tex_coords[tex_idx])
                    else:
                        # Если нет текстурных координат, используем координаты вершин
                        # как простую проекцию
                        vertex = model.vertices[vertex_idx]
                        u = (vertex.x + 0.5)  # Преобразуем из [-0.5, 0.5] в [0, 1]
                        v = (vertex.y + 0.5)
                        face_tex_coords.append([u, v])
            
            if len(face_points) < 3:
                continue
            
            # ЗАПОЛНЕНИЕ С ТЕКСТУРОЙ
            if show_filled and is_visible and self.use_texture:
                if len(face_points) == 3:
                    # Треугольник
                    self.render_textured_triangle(
                        screen,
                        face_vertices[0], face_vertices[1], face_vertices[2],
                        face_points[0], face_points[1], face_points[2],
                        face_tex_coords[0], face_tex_coords[1], face_tex_coords[2]
                    )
                elif len(face_points) >= 4:
                    # Четырехугольник (разбиваем на треугольники)
                    self.render_textured_quad(
                        screen,
                        face_vertices[:4],
                        face_points[:4],
                        face_tex_coords[:4]
                    )
            elif show_filled and is_visible and not self.use_texture:
                # Старый код для заливки без текстуры
                if self.use_gouraud and len(face_vertices) >= 3:
                    if len(face_vertices) == 3:
                        self.render_triangle_gouraud(
                            screen, 
                            face_vertices[0], face_vertices[1], face_vertices[2],
                            face_points[0], face_points[1], face_points[2]
                        )
                    elif len(face_vertices) == 4:
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
                else:
                    # Плоское затенение
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
                        pygame.draw.polygon(screen, avg_color, face_points)
            
            # Каркас
            if show_wireframe:
                line_color = (100, 100, 100) if not is_visible else (255, 255, 255)
                pygame.draw.polygon(screen, line_color, face_points, 1)
            
            # Нормали
            if show_normals and is_visible:
                center_x = sum(p[0] for p in face_points) / len(face_points)
                center_y = sum(p[1] for p in face_points) / len(face_points)
                
                scale = 15
                end_x = center_x + face.normal_x * scale
                end_y = center_y - face.normal_y * scale
                
                pygame.draw.line(screen, (255, 255, 0), 
                               (center_x, center_y), (end_x, end_y), 2)
                pygame.draw.circle(screen, (255, 200, 0), (int(center_x), int(center_y)), 3)
        
        # Отображение информации об освещении
        if self.show_light_info:
            self.draw_light_info(screen)
        
        # Отображение информации о текстуре
        self.draw_texture_info(screen)
        
        return visible, hidden
    
    def draw_light_info(self, screen):
        """Отображение информации об освещении"""
        font = pygame.font.Font(None, 24)
        
        info_lines = [
            f"Режим шейдинга: {'Гуро' if self.use_gouraud else 'Плоский'} (G)",
            f"Текстура: {'ВКЛ' if self.use_texture else 'ВЫКЛ'} (T)",
            f"Источник света: ({self.light.position[0]:.1f}, {self.light.position[1]:.1f}, {self.light.position[2]:.1f})",
            f"Интенсивность: {self.light.intensity:.1f}",
        ]
        
        # Фон для информации
        info_bg = pygame.Surface((300, 100), pygame.SRCALPHA)
        info_bg.fill((0, 0, 0, 150))
        screen.blit(info_bg, (10, self.height - 110))
        
        for i, line in enumerate(info_lines):
            text = font.render(line, True, (200, 255, 200))
            screen.blit(text, (20, self.height - 100 + i * 25))
    
    def draw_texture_info(self, screen):
        """Отображение информации о текстуре"""
        if not self.use_texture:
            return
        
        font = pygame.font.Font(None, 22)
        
        # Миниатюра текстуры
        tex_preview = pygame.transform.scale(self.texture.surface, (80, 80))
        screen.blit(tex_preview, (self.width - 90, 10))
        
        # Рамка вокруг миниатюры
        pygame.draw.rect(screen, (255, 255, 255), (self.width - 92, 8, 84, 84), 2)
        
        # Информация
        info = font.render("Текстура активна (T - выкл, Y - сменить)", True, (255, 255, 200))
        screen.blit(info, (self.width - 280, 95))