# texture.py
import pygame
import numpy as np

class Texture:
    def __init__(self, width=256, height=256):
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height))
        self.generate_default_texture()
    
    def generate_default_texture(self):
        """Создание текстуры по умолчанию (шахматная доска)"""
        for y in range(self.height):
            for x in range(self.width):
                # Шахматный паттерн
                if (x // 32 + y // 32) % 2 == 0:
                    color = (200, 100, 100)  # Красный
                else:
                    color = (255, 255, 200)  # Светло-желтый
                
                # Добавляем градиент для визуализации
                gradient = int(128 + 127 * np.sin(x * 0.05) * np.cos(y * 0.05))
                color = (
                    min(255, color[0] + gradient // 3),
                    min(255, color[1] + gradient // 3),
                    min(255, color[2] + gradient // 3)
                )
                
                self.surface.set_at((x, y), color)
    
    def generate_checkerboard(self, size=32):
        """Создание шахматной текстуры"""
        for y in range(self.height):
            for x in range(self.width):
                if ((x // size) + (y // size)) % 2 == 0:
                    color = (255, 255, 255)  # Белый
                else:
                    color = (100, 100, 100)  # Серый
                self.surface.set_at((x, y), color)
    
    def generate_gradient(self):
        """Создание градиентной текстуры"""
        for y in range(self.height):
            for x in range(self.width):
                r = int(128 + 127 * np.sin(x * 0.02))
                g = int(128 + 127 * np.cos(y * 0.02))
                b = int(128 + 127 * np.sin((x + y) * 0.01))
                self.surface.set_at((x, y), (r, g, b))
    
    def get_color(self, u, v):
        """Получение цвета из текстуры по координатам (u, v)"""
        # Обрезаем координаты до [0, 1]
        u = max(0, min(1, u))
        v = max(0, min(1, v))
        
        # Конвертируем в координаты пикселей
        x = int(u * (self.width - 1))
        y = int((1 - v) * (self.height - 1))  # Инвертируем v для правильной ориентации
        
        return self.surface.get_at((x, y))
    
    def get_color_bilinear(self, u, v):
        """Билинейная фильтрация текстуры"""
        u = max(0, min(1, u))
        v = max(0, min(1, v))
        
        # Координаты в текселях
        x = u * (self.width - 1)
        y = (1 - v) * (self.height - 1)
        
        # Ближайшие пиксели
        x0 = int(np.floor(x))
        x1 = min(self.width - 1, x0 + 1)
        y0 = int(np.floor(y))
        y1 = min(self.height - 1, y0 + 1)
        
        # Дроби
        a = x - x0
        b = y - y0
        
        # Цвета соседних пикселей
        c00 = self.surface.get_at((x0, y0))
        c01 = self.surface.get_at((x0, y1))
        c10 = self.surface.get_at((x1, y0))
        c11 = self.surface.get_at((x1, y1))
        
        # Билинейная интерполяция
        r = (1 - a) * (1 - b) * c00[0] + a * (1 - b) * c10[0] + (1 - a) * b * c01[0] + a * b * c11[0]
        g = (1 - a) * (1 - b) * c00[1] + a * (1 - b) * c10[1] + (1 - a) * b * c01[1] + a * b * c11[1]
        b_val = (1 - a) * (1 - b) * c00[2] + a * (1 - b) * c10[2] + (1 - a) * b * c01[2] + a * b * c11[2]
        
        return (int(r), int(g), int(b_val))