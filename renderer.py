# renderer.py
import numpy as np
import pygame
from lighting import Light, LambertShader, GouraudShader, PhongShader
from texture_renderer import TexturedRenderer

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
        self.phong_shader = PhongShader(
            self.light,
            ambient_intensity=0.3,
            specular_intensity=0.5,
            shininess=32
        )
        
        # Текстурирование
        self.textured_renderer = TexturedRenderer(width, height)
        self.textured_renderer.set_light(self.light)
        
        # Режимы рендеринга
        self.use_gouraud = True
        self.use_phong = False
        self.show_light_info = True
        self.texture_enabled = False
        
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
        """Отсечение нелицевых граней"""
        return face.normal_z < 0
    
    def render_triangle_flat(self, screen, face_points, color):
        """Рендеринг треугольника с плоским затенением"""
        pygame.draw.polygon(screen, color, face_points)
    
    def render_triangle_gouraud(self, screen, v0, v1, v2, p0, p1, p2):
        """Рендеринг треугольника с Гуро шейдингом"""
        self.gouraud_shader.shade_triangle(screen, v0, v1, v2, p0, p1, p2)
    
    def render_triangle_phong(self, screen, v0, v1, v2, p0, p1, p2, material_color):
        """Рендеринг треугольника с шейдингом Фонга"""
        # Устанавливаем позицию камеры для Phong шейдера
        self.phong_shader.set_view_pos([0, 0, 3])
        
        # Рендерим с интерполяцией нормалей
        self.phong_shader.shade_triangle(
            screen, v0, v1, v2, p0, p1, p2,
            (material_color[0]/255.0, material_color[1]/255.0, material_color[2]/255.0)
        )
    
    def render_triangle_textured(self, screen, v0, v1, v2, p0, p1, p2):
        """Рендеринг текстурированного треугольника"""
        self.textured_renderer.set_view_pos([0, 0, 3])
        self.textured_renderer.render_textured_triangle(
            screen, v0, v1, v2, p0, p1, p2,
            self.textured_renderer.current_texture
        )
    
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
    
    def render(self, screen, model, camera, show_wireframe=True, 
               show_filled=True, backface_culling=True, show_normals=False,
               texture_enabled=False):
        """Основной метод рендеринга с поддержкой текстурирования"""
        screen.fill(self.bg_color)
        
        view_proj_matrix = camera.get_view_projection_matrix()
        
        # Проецируем все вершины
        projected = []
        for vertex in model.vertices:
            projected.append(self.project_point(vertex, view_proj_matrix))
        
        # Вычисляем цвета вершин
        base_color = self.colors[self.current_color_idx]
        
        # Создаем список цветов для каждой вершины
        vertex_colors = []
        material_color_rgb = (
            base_color[0] / 255.0,
            base_color[1] / 255.0,
            base_color[2] / 255.0
        )
        
        for vertex in model.vertices:
            if self.use_phong:
                color = self.phong_shader.calculate_vertex_color(vertex, material_color_rgb, use_phong=True)
            else:
                color = self.lambert_shader.calculate_vertex_color(vertex, material_color_rgb)
            
            vertex_color = (
                int(color[0] * 255),
                int(color[1] * 255),
                int(color[2] * 255)
            )
            vertex.color = vertex_color
            vertex_colors.append(vertex_color)
        
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
            for idx in face.vertex_indices:
                if 0 <= idx < len(projected):
                    face_points.append(projected[idx])
                    face_vertices.append(model.vertices[idx])
            
            if len(face_points) < 3:
                continue
            
            # Заполнение
            if show_filled and is_visible:
                if texture_enabled and hasattr(face_vertices[0], 'tex_u'):
                    # Текстурирование
                    if len(face_vertices) == 3:
                        self.render_triangle_textured(
                            screen,
                            face_vertices[0], face_vertices[1], face_vertices[2],
                            face_points[0], face_points[1], face_points[2]
                        )
                    elif len(face_vertices) == 4:
                        # Разбиваем четырехугольник на два треугольника
                        self.render_triangle_textured(
                            screen,
                            face_vertices[0], face_vertices[1], face_vertices[2],
                            face_points[0], face_points[1], face_points[2]
                        )
                        self.render_triangle_textured(
                            screen,
                            face_vertices[0], face_vertices[2], face_vertices[3],
                            face_points[0], face_points[2], face_points[3]
                        )
                elif self.use_phong:
                    # Phong шейдинг
                    if len(face_vertices) == 3:
                        self.render_triangle_phong(
                            screen,
                            face_vertices[0], face_vertices[1], face_vertices[2],
                            face_points[0], face_points[1], face_points[2],
                            base_color
                        )
                    elif len(face_vertices) == 4:
                        self.render_triangle_phong(
                            screen,
                            face_vertices[0], face_vertices[1], face_vertices[2],
                            face_points[0], face_points[1], face_points[2],
                            base_color
                        )
                        self.render_triangle_phong(
                            screen,
                            face_vertices[0], face_vertices[2], face_vertices[3],
                            face_points[0], face_points[2], face_points[3],
                            base_color
                        )
                elif self.use_gouraud:
                    # Гуро шейдинг
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
                    # Плоское затенение - средний цвет вершин грани
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
        
        # Отображение информации
        if self.show_light_info:
            self.draw_light_info(screen, texture_enabled)
        
        return visible, hidden
    
    def draw_light_info(self, screen, texture_enabled):
        """Отображение информации об освещении и текстурировании"""
        font = pygame.font.Font(None, 24)
        
        shading_mode = "Phong" if self.use_phong else "Gouraud" if self.use_gouraud else "Flat"
        
        info_lines = [
            f"Шейдинг: {shading_mode} (P)",
            f"Текстура: {'ВКЛ' if texture_enabled else 'ВЫКЛ'} (T)",
            f"Источник света: ({self.light.position[0]:.1f}, {self.light.position[1]:.1f}, {self.light.position[2]:.1f})",
            f"Интенсивность: {self.light.intensity:.1f} (I/K)",
            f"Ambient: {self.lambert_shader.ambient_intensity:.2f} (O/P)",
        ]
        
        # Фон для информации
        info_bg = pygame.Surface((350, 125), pygame.SRCALPHA)
        info_bg.fill((0, 0, 0, 150))
        screen.blit(info_bg, (10, self.height - 135))
        
        for i, line in enumerate(info_lines):
            text = font.render(line, True, (200, 255, 200))
            screen.blit(text, (20, self.height - 125 + i * 25))