# ui.py
import pygame

class UI:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 20)
        
        # Цвета
        self.bg_color = (0, 0, 0, 200)
        self.text_color = (255, 255, 255)
        self.highlight_color = (255, 200, 100)
        self.warning_color = (255, 100, 100)
        self.success_color = (100, 255, 100)
        self.info_color = (100, 200, 255)
    
    def draw_menu(self, screen, options, selected_index, current_model=None):
        """Рисует меню выбора модели"""
        # Полупрозрачный фон
        menu_bg = pygame.Surface((450, 350), pygame.SRCALPHA)
        menu_bg.fill((20, 20, 40, 240))
        screen.blit(menu_bg, (self.width//2 - 225, self.height//2 - 175))
        
        # Заголовок
        title = self.title_font.render("3D МОДЕЛЬ ВИЗУАЛИЗАТОР", True, self.highlight_color)
        screen.blit(title, (self.width//2 - title.get_width()//2, self.height//2 - 150))
        
        # Текущая модель
        if current_model:
            current_text = self.font.render(f"Текущая: {current_model}", True, self.success_color)
            screen.blit(current_text, (self.width//2 - current_text.get_width()//2, self.height//2 - 110))
        
        # Варианты моделей
        sub_title = self.font.render("ВЫБЕРИТЕ НОВУЮ МОДЕЛЬ:", True, self.text_color)
        screen.blit(sub_title, (self.width//2 - sub_title.get_width()//2, self.height//2 - 70))
        
        for i, option in enumerate(options):
            color = self.highlight_color if i == selected_index else self.text_color
            text = self.font.render(option, True, color)
            screen.blit(text, (self.width//2 - text.get_width()//2, 
                             self.height//2 - 30 + i * 40))
        
        # Инструкция
        inst1 = self.small_font.render("СТРЕЛКИ - выбор модели | ENTER - загрузить | ESC - вернуться", 
                                      True, (200, 200, 255))
        screen.blit(inst1, (self.width//2 - inst1.get_width()//2, self.height//2 + 130))
    
    def draw_main_ui(self, screen, model_info, stats, settings, camera_info):
        """Основной UI при рендеринге - ВЕРТИКАЛЬНОЕ РАСПОЛОЖЕНИЕ"""
        # Верхняя панель - информация о модели
        top_panel = pygame.Surface((self.width - 20, 120), pygame.SRCALPHA)
        top_panel.fill(self.bg_color)
        screen.blit(top_panel, (10, 10))
        
        # Средняя панель - настройки
        middle_panel = pygame.Surface((self.width - 20, 120), pygame.SRCALPHA)
        middle_panel.fill(self.bg_color)
        screen.blit(middle_panel, (10, 140))
        
        # Нижняя панель - управление
        bottom_panel = pygame.Surface((self.width - 20, 180), pygame.SRCALPHA)
        bottom_panel.fill(self.bg_color)
        screen.blit(bottom_panel, (10, self.height - 190))
        
        # Информация о модели (верхняя панель)
        model_title = self.font.render("МОДЕЛЬ", True, self.highlight_color)
        screen.blit(model_title, (20, 15))
        
        model_lines = [
            f"Название: {model_info['name']}",
            f"Вершин: {model_info['vertices']}, Граней: {model_info['faces']}",
            f"Видимых: {stats['visible']}, Скрытых: {stats['hidden']} ({stats['visible_percent']:.1f}%)",
        ]
        
        for i, line in enumerate(model_lines):
            text = self.font.render(line, True, self.text_color)
            screen.blit(text, (20, 45 + i * 25))
        
        # Настройки (средняя панель)
        settings_title = self.font.render("НАСТРОЙКИ", True, self.highlight_color)
        screen.blit(settings_title, (20, 145))
        
        # Разделяем настройки на 3 колонки
        col1_x, col2_x, col3_x = 20, 250, 480
        
        settings_col1 = [
            f"Автовращение: {'ВКЛ' if settings['auto_rotate'] else 'ВЫКЛ'} (SPACE)",
            f"Каркас: {'ВКЛ' if settings['wireframe'] else 'ВЫКЛ'} (W)",
            f"Заливка: {'ВКЛ' if settings['filled'] else 'ВЫКЛ'} (F)",
        ]
        
        settings_col2 = [
            f"Отсечение: {'ВКЛ' if settings['culling'] else 'ВЫКЛ'} (B)",
            f"Нормали: {'ВКЛ' if settings['normals'] else 'ВЫКЛ'} (N)",
            f"Цвет: {settings['color']} (C)",
        ]
        
        settings_col3 = [
            f"Шейдинг: {'Гуро' if settings['gouraud'] else 'Плоский'} (G)",
            f"Интенсивность: {settings['light_intensity']:.1f} (I/K)",
            f"Ambient: {settings['ambient']:.2f} (O/P)",
        ]
        
        for i, line in enumerate(settings_col1):
            text = self.font.render(line, True, self.text_color)
            screen.blit(text, (col1_x, 175 + i * 25))
        
        for i, line in enumerate(settings_col2):
            text = self.font.render(line, True, self.text_color)
            screen.blit(text, (col2_x, 175 + i * 25))
        
        for i, line in enumerate(settings_col3):
            text = self.font.render(line, True, self.text_color)
            screen.blit(text, (col3_x, 175 + i * 25))
        
        # Управление (нижняя панель)
        control_title = self.font.render("УПРАВЛЕНИЕ", True, self.highlight_color)
        screen.blit(control_title, (20, self.height - 180))
        
        # 4 колонки управления
        controls = [
            # Колонка 1
            ["Модели:", "M - Меню", "Стрелки - Выбор", "ENTER - Загрузить", ""],
            # Колонка 2  
            ["Рендеринг:", "W - Каркас", "F - Заливка", "B - Отсечение", "N - Нормали", "C - Цвет"],
            # Колонка 3
            ["Освещение:", "G - Шейдинг", "L - Инфо света", "I/K - Интенсивность", "O/P - Ambient", "H/J/U - Свет +/-"],
            # Колонка 4
            ["Камера:", "R - Сброс", "Q/E - Зум", "X/Y/Z - Вращение", "+/- - Скорость", "ESC - Выход"],
        ]
        
        col_positions = [20, 180, 340, 500]
        
        for col_idx, col_controls in enumerate(controls):
            x_pos = col_positions[col_idx]
            for i, control in enumerate(col_controls):
                color = self.highlight_color if ":" in control else self.text_color
                text = self.small_font.render(control, True, color)
                screen.blit(text, (x_pos, self.height - 155 + i * 20))
    
    def draw_rotation_controls(self, screen, x, y):
        """Рисует элементы управления вращением"""
        panel = pygame.Surface((200, 100), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 150))
        screen.blit(panel, (x, y))
        
        title = self.small_font.render("РУЧНОЕ ВРАЩЕНИЕ:", True, self.highlight_color)
        screen.blit(title, (x + 10, y + 10))
        
        controls = [
            "X/Y/Z - зажать",
            "+/- - скорость",
            "R - сброс",
        ]
        
        for i, control in enumerate(controls):
            text = self.small_font.render(control, True, self.text_color)
            screen.blit(text, (x + 10, y + 35 + i * 20))
    
    def draw_notification(self, screen, message, color, duration=2.0):
        """Временное уведомление"""
        notification = pygame.Surface((400, 40), pygame.SRCALPHA)
        notification.fill((0, 0, 0, 200))
        screen.blit(notification, (self.width//2 - 200, self.height - 60))
        
        text = self.font.render(message, True, color)
        screen.blit(text, (self.width//2 - text.get_width()//2, self.height - 50))