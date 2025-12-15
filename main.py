# main.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pygame
import numpy as np
from point import Point
from camera import Camera
from model_loader import Model3D, load_obj, create_cube_with_texture, create_cube
from renderer import Renderer
from ui import UI
from lighting import Light, LambertShader, GouraudShader, PhongShader

def create_transformation_matrices(angle_x, angle_y, angle_z, scale_factor=1.0):
    """Создает матрицы преобразования модели"""
    # Матрица масштабирования
    scale_matrix = np.array([
        [scale_factor * 0.6, 0, 0, 0],
        [0, scale_factor * 0.6, 0, 0],
        [0, 0, scale_factor * 0.6, 0],
        [0, 0, 0, 1]
    ], dtype=float)
    
    # Матрицы вращения
    c1, s1 = np.cos(angle_x), np.sin(angle_x)
    c2, s2 = np.cos(angle_y), np.sin(angle_y)
    c3, s3 = np.cos(angle_z), np.sin(angle_z)
    
    rotation_x = np.array([
        [1, 0, 0, 0],
        [0, c1, -s1, 0],
        [0, s1, c1, 0],
        [0, 0, 0, 1]
    ], dtype=float)
    
    rotation_y = np.array([
        [c2, 0, s2, 0],
        [0, 1, 0, 0],
        [-s2, 0, c2, 0],
        [0, 0, 0, 1]
    ], dtype=float)
    
    rotation_z = np.array([
        [c3, -s3, 0, 0],
        [s3, c3, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ], dtype=float)
    
    # Комбинируем преобразования
    return rotation_z @ rotation_y @ rotation_x @ scale_matrix

def load_all_models():
    """Загрузка всех доступных моделей"""
    models = {}
    
    # Загружаем чайник
    teapot = load_obj("utah_teapot_lowpoly.obj")
    if teapot:
        models["Чайник"] = teapot
    
    # Загружаем куб из файла
    cube_file = load_obj("cube.obj")
    if cube_file:
        models["Куб (файл)"] = cube_file
    
    # Загружаем сферу
    sphere = load_obj("sphere.obj")
    if sphere:
        models["Сфера"] = sphere
    
    # Создаем встроенный куб с текстурой
    models["Куб (текстурный)"] = create_cube_with_texture()
    
    # Создаем встроенный куб без текстуры
    models["Куб (простой)"] = create_cube()
    
    return models

def main():
    # Инициализация
    pygame.init()
    WIDTH, HEIGHT = 1024, 768
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("3D Renderer - Phong Shading & Texturing")
    
    # Создаем компоненты
    camera = Camera(
        position=[0, 0, 3],
        target=[0, 0, 0],
        up=[0, 1, 0],
        aspect_ratio=WIDTH/HEIGHT
    )
    
    renderer = Renderer(WIDTH, HEIGHT)
    ui = UI(WIDTH, HEIGHT)
    
    # Загружаем все модели
    all_models = load_all_models()
    model_names = list(all_models.keys())
    
    if not all_models:
        print("Не удалось загрузить ни одну модель!")
        return
    
    # Состояние программы
    state = {
        'in_model_menu': False,
        'selected_model_idx': 0,
        'current_model_name': model_names[0],
        'current_model': all_models[model_names[0]],
        'original_vertices': None,
        'angle_x': 0,
        'angle_y': 0,
        'angle_z': 0,
        'auto_rotate': True,
        'rotate_speed': 0.02,
        'show_wireframe': False,
        'show_filled': True,
        'backface_culling': True,
        'show_normals': False,
        'notification': None,
        'notification_time': 0,
        'shading_mode': 'gouraud',  # gouraud, phong, flat
        'texture_enabled': False,
        'material_color_idx': 0,
        'show_light_controls': True,
    }
    
    # Сохраняем оригинальные вершины текущей модели
    if state['current_model']:
        state['original_vertices'] = [
            Point(v.x, v.y, v.z, v.normal_x, v.normal_y, v.normal_z, 
                  getattr(v, 'color', None), 
                  getattr(v, 'tex_u', 0), 
                  getattr(v, 'tex_v', 0)) 
            for v in state['current_model'].vertices
        ]
    
    # Состояние нажатых клавиш
    keys_pressed = {
        pygame.K_x: False,  # Вращение по X
        pygame.K_y: False,  # Вращение по Y
        pygame.K_z: False,  # Вращение по Z
        pygame.K_q: False,  # Зум -
        pygame.K_e: False,  # Зум +
        pygame.K_PLUS: False,  # Увеличить скорость
        pygame.K_MINUS: False, # Уменьшить скорость
    }
    
    # Основные параметры
    clock = pygame.time.Clock()
    running = True
    
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time в секундах
        
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state['in_model_menu']:
                        state['in_model_menu'] = False
                    else:
                        running = False
                
                elif event.key == pygame.K_m:
                    state['in_model_menu'] = not state['in_model_menu']
                    if state['in_model_menu']:
                        state['notification'] = "Меню моделей открыто"
                        state['notification_time'] = 2.0
                
                elif state['in_model_menu']:
                    # Управление в меню моделей
                    if event.key == pygame.K_DOWN:
                        state['selected_model_idx'] = (state['selected_model_idx'] + 1) % len(model_names)
                    elif event.key == pygame.K_UP:
                        state['selected_model_idx'] = (state['selected_model_idx'] - 1) % len(model_names)
                    elif event.key == pygame.K_RETURN:
                        # Загрузка выбранной модели
                        selected_name = model_names[state['selected_model_idx']]
                        state['current_model_name'] = selected_name
                        state['current_model'] = all_models[selected_name]
                        
                        # Сохраняем оригинальные вершины
                        state['original_vertices'] = [
                            Point(v.x, v.y, v.z, v.normal_x, v.normal_y, v.normal_z,
                                  getattr(v, 'color', None),
                                  getattr(v, 'tex_u', 0),
                                  getattr(v, 'tex_v', 0))
                            for v in state['current_model'].vertices
                        ]
                        
                        # Сброс параметров
                        state['angle_x'] = state['angle_y'] = state['angle_z'] = 0
                        camera.reset()
                        state['texture_enabled'] = False  # Выключить текстурирование при смене модели
                        state['in_model_menu'] = False
                        state['notification'] = f"Загружена модель: {selected_name}"
                        state['notification_time'] = 2.0
                
                else:
                    # Управление в режиме просмотра
                    if event.key == pygame.K_SPACE:
                        state['auto_rotate'] = not state['auto_rotate']
                        state['notification'] = f"Автовращение: {'ВКЛ' if state['auto_rotate'] else 'ВЫКЛ'}"
                        state['notification_time'] = 1.0
                    
                    elif event.key == pygame.K_w:
                        state['show_wireframe'] = not state['show_wireframe']
                        state['notification'] = f"Каркас: {'ВКЛ' if state['show_wireframe'] else 'ВЫКЛ'}"
                        state['notification_time'] = 1.0
                    
                    elif event.key == pygame.K_f:
                        state['show_filled'] = not state['show_filled']
                        state['notification'] = f"Заливка: {'ВКЛ' if state['show_filled'] else 'ВЫКЛ'}"
                        state['notification_time'] = 1.0
                    
                    elif event.key == pygame.K_b:
                        state['backface_culling'] = not state['backface_culling']
                        state['notification'] = f"Отсечение граней: {'ВКЛ' if state['backface_culling'] else 'ВЫКЛ'}"
                        state['notification_time'] = 1.0
                    
                    elif event.key == pygame.K_n:
                        state['show_normals'] = not state['show_normals']
                        state['notification'] = f"Нормали: {'ВКЛ' if state['show_normals'] else 'ВЫКЛ'}"
                        state['notification_time'] = 1.0
                    
                    elif event.key == pygame.K_c:
                        renderer.next_color()
                        state['material_color_idx'] = renderer.current_color_idx
                        state['notification'] = f"Цвет материала: {renderer.get_current_color_name()}"
                        state['notification_time'] = 1.0
                    
                    elif event.key == pygame.K_p:  # Переключение режима шейдинга
                        shading_modes = ['flat', 'gouraud', 'phong']
                        current_idx = shading_modes.index(state['shading_mode'])
                        state['shading_mode'] = shading_modes[(current_idx + 1) % len(shading_modes)]
                        
                        # Применяем режим к рендереру
                        if state['shading_mode'] == 'phong':
                            renderer.use_phong = True
                            renderer.use_gouraud = False
                        elif state['shading_mode'] == 'gouraud':
                            renderer.use_phong = False
                            renderer.use_gouraud = True
                        else:  # flat
                            renderer.use_phong = False
                            renderer.use_gouraud = False
                        
                        state['notification'] = f"Режим шейдинга: {state['shading_mode'].upper()}"
                        state['notification_time'] = 1.0
                    
                    elif event.key == pygame.K_t:  # Включение/выключение текстурирования
                        # Проверяем, есть ли у модели текстурные координаты
                        if state['current_model'] and hasattr(state['current_model'], 'tex_coords'):
                            if state['current_model'].tex_coords and len(state['current_model'].tex_coords) > 0:
                                state['texture_enabled'] = not state['texture_enabled']
                                state['notification'] = f"Текстурирование: {'ВКЛ' if state['texture_enabled'] else 'ВЫКЛ'}"
                            else:
                                state['notification'] = "У этой модели нет текстурных координат"
                        else:
                            state['notification'] = "Текстурирование не поддерживается"
                        state['notification_time'] = 1.0

                    elif event.key == pygame.K_l:  # Показать/скрыть информацию об освещении
                        renderer.show_light_info = not renderer.show_light_info
                        state['show_light_controls'] = renderer.show_light_info
                        state['notification'] = f"Инфо освещения: {'ВКЛ' if renderer.show_light_info else 'ВЫКЛ'}"
                        state['notification_time'] = 1.0

                    elif event.key == pygame.K_i:  # Увеличить интенсивность света
                        renderer.light.intensity = min(2.0, renderer.light.intensity + 0.1)
                        renderer.phong_shader.light.intensity = renderer.light.intensity
                        state['notification'] = f"Интенсивность света: {renderer.light.intensity:.1f}"
                        state['notification_time'] = 0.5

                    elif event.key == pygame.K_k:  # Уменьшить интенсивность света
                        renderer.light.intensity = max(0.1, renderer.light.intensity - 0.1)
                        renderer.phong_shader.light.intensity = renderer.light.intensity
                        state['notification'] = f"Интенсивность света: {renderer.light.intensity:.1f}"
                        state['notification_time'] = 0.5

                    elif event.key == pygame.K_o:  # Увеличить ambient
                        renderer.lambert_shader.ambient_intensity = min(1.0, renderer.lambert_shader.ambient_intensity + 0.05)
                        renderer.phong_shader.ambient_intensity = renderer.lambert_shader.ambient_intensity
                        state['notification'] = f"Ambient освещение: {renderer.lambert_shader.ambient_intensity:.2f}"
                        state['notification_time'] = 0.5

                    elif event.key == pygame.K_u:  # Уменьшить ambient
                        renderer.lambert_shader.ambient_intensity = max(0.0, renderer.lambert_shader.ambient_intensity - 0.05)
                        renderer.phong_shader.ambient_intensity = renderer.lambert_shader.ambient_intensity
                        state['notification'] = f"Ambient освещение: {renderer.lambert_shader.ambient_intensity:.2f}"
                        state['notification_time'] = 0.5
                    
                    elif event.key == pygame.K_h:  # Управление светом по X
                        if event.mod & pygame.KMOD_SHIFT:  # Shift+H
                            renderer.light.position[0] -= 0.1
                            renderer.phong_shader.light.position[0] = renderer.light.position[0]
                            state['notification'] = f"Свет X: {renderer.light.position[0]:.1f}"
                        else:  # Просто H
                            renderer.light.position[0] += 0.1
                            renderer.phong_shader.light.position[0] = renderer.light.position[0]
                            state['notification'] = f"Свет X: {renderer.light.position[0]:.1f}"
                        state['notification_time'] = 0.5
                    
                    elif event.key == pygame.K_j:  # Управление светом по Y
                        if event.mod & pygame.KMOD_SHIFT:  # Shift+J
                            renderer.light.position[1] -= 0.1
                            renderer.phong_shader.light.position[1] = renderer.light.position[1]
                            state['notification'] = f"Свет Y: {renderer.light.position[1]:.1f}"
                        else:  # Просто J
                            renderer.light.position[1] += 0.1
                            renderer.phong_shader.light.position[1] = renderer.light.position[1]
                            state['notification'] = f"Свет Y: {renderer.light.position[1]:.1f}"
                        state['notification_time'] = 0.5
                    
                    elif event.key == pygame.K_y:  # Управление светом по Z (используем Y для управления светом по Z)
                        if event.mod & pygame.KMOD_SHIFT:  # Shift+Y
                            renderer.light.position[2] -= 0.1
                            renderer.phong_shader.light.position[2] = renderer.light.position[2]
                            state['notification'] = f"Свет Z: {renderer.light.position[2]:.1f}"
                        else:  # Просто Y
                            renderer.light.position[2] += 0.1
                            renderer.phong_shader.light.position[2] = renderer.light.position[2]
                            state['notification'] = f"Свет Z: {renderer.light.position[2]:.1f}"
                        state['notification_time'] = 0.5
                        keys_pressed[pygame.K_y] = False  # Отключаем вращение по Y
                    
                    elif event.key == pygame.K_r:
                        # Сброс вращения и камеры
                        state['angle_x'] = state['angle_y'] = state['angle_z'] = 0
                        camera.reset()
                        
                        # Сброс освещения
                        renderer.light.position = [3, 3, 3]
                        renderer.phong_shader.light.position = renderer.light.position.copy()
                        renderer.light.intensity = 0.8
                        renderer.phong_shader.light.intensity = renderer.light.intensity
                        renderer.lambert_shader.ambient_intensity = 0.3
                        renderer.phong_shader.ambient_intensity = 0.3
                        renderer.phong_shader.specular_intensity = 0.5
                        renderer.phong_shader.shininess = 32
                        
                        state['notification'] = "Все настройки сброшены"
                        state['notification_time'] = 1.0
                    
                    elif event.key == pygame.K_s:  # Управление параметрами Фонга
                        if event.mod & pygame.KMOD_SHIFT:  # Shift+S - уменьшить бликовость
                            renderer.phong_shader.shininess = max(1, renderer.phong_shader.shininess - 4)
                            state['notification'] = f"Бликовость: {renderer.phong_shader.shininess}"
                        else:  # S - увеличить бликовость
                            renderer.phong_shader.shininess = min(256, renderer.phong_shader.shininess + 4)
                            state['notification'] = f"Бликовость: {renderer.phong_shader.shininess}"
                        state['notification_time'] = 0.5
                    
                    elif event.key == pygame.K_d:  # Управление specular интенсивностью
                        if event.mod & pygame.KMOD_SHIFT:  # Shift+D - уменьшить specular
                            renderer.phong_shader.specular_intensity = max(0, renderer.phong_shader.specular_intensity - 0.1)
                            state['notification'] = f"Specular: {renderer.phong_shader.specular_intensity:.1f}"
                        else:  # D - увеличить specular
                            renderer.phong_shader.specular_intensity = min(2.0, renderer.phong_shader.specular_intensity + 0.1)
                            state['notification'] = f"Specular: {renderer.phong_shader.specular_intensity:.1f}"
                        state['notification_time'] = 0.5
                    
                    elif event.key in keys_pressed:
                        keys_pressed[event.key] = True
            
            elif event.type == pygame.KEYUP:
                if event.key in keys_pressed:
                    keys_pressed[event.key] = False
        
        # Обновление состояния нажатых клавиш
        if not state['in_model_menu']:
            # Вращение камеры при зажатых клавишах
            rotation_amount = camera.rotation_speed * dt * 60
            
            if keys_pressed[pygame.K_x]:
                camera.rotate('x', rotation_amount)
            
            if keys_pressed[pygame.K_y] and not pygame.key.get_mods() & pygame.KMOD_SHIFT:
                camera.rotate('y', rotation_amount)
            
            if keys_pressed[pygame.K_z]:
                camera.rotate('z', rotation_amount)
            
            # Зум при зажатых клавишах
            if keys_pressed[pygame.K_q]:
                camera.zoom_out(0.05)
            
            if keys_pressed[pygame.K_e]:
                camera.zoom_in(0.05)
            
            # Изменение скорости
            if keys_pressed[pygame.K_PLUS]:
                state['rotate_speed'] = min(0.1, state['rotate_speed'] + 0.001)
                camera.rotation_speed = min(0.05, camera.rotation_speed + 0.001)
            
            if keys_pressed[pygame.K_MINUS]:
                state['rotate_speed'] = max(0.001, state['rotate_speed'] - 0.001)
                camera.rotation_speed = max(0.001, camera.rotation_speed - 0.001)
        
        # Обновление состояния
        if state['notification_time'] > 0:
            state['notification_time'] -= dt
        
        # Автоматическое вращение модели
        if state['auto_rotate'] and not state['in_model_menu']:
            state['angle_x'] += state['rotate_speed'] * 0.5
            state['angle_y'] += state['rotate_speed'] * 0.7
            state['angle_z'] += state['rotate_speed'] * 0.3
        
        # Очистка экрана
        screen.fill(renderer.bg_color)
        
        if state['in_model_menu']:
            # Рендеринг меню выбора модели
            ui.draw_menu(
                screen, 
                model_names, 
                state['selected_model_idx'],
                state['current_model_name']
            )
        
        else:
            # Применение преобразований к модели
            if state['current_model'] and state['original_vertices']:
                transform_matrix = create_transformation_matrices(
                    state['angle_x'], 
                    state['angle_y'], 
                    state['angle_z']
                )
                
                # Восстанавливаем и преобразуем вершины
                for i, vertex in enumerate(state['current_model'].vertices):
                    orig = state['original_vertices'][i]
                    
                    # Восстанавливаем оригинальные значения
                    vertex.x = orig.x
                    vertex.y = orig.y
                    vertex.z = orig.z
                    vertex.normal_x = orig.normal_x
                    vertex.normal_y = orig.normal_y
                    vertex.normal_z = orig.normal_z
                    vertex.color = orig.color
                    
                    # Сохраняем текстурные координаты
                    if hasattr(orig, 'tex_u'):
                        vertex.tex_u = orig.tex_u
                    if hasattr(orig, 'tex_v'):
                        vertex.tex_v = orig.tex_v
                    
                    # Применяем преобразование
                    vertex.transform(transform_matrix)
                
                # Пересчитываем нормали после преобразования
                state['current_model'].recalculate_normals()
            
            # Рендеринг модели
            if state['current_model']:
                # Устанавливаем позицию камеры для Phong шейдера
                renderer.phong_shader.set_view_pos(camera.position)
                
                visible, hidden = renderer.render(
                    screen, 
                    state['current_model'], 
                    camera,
                    show_wireframe=state['show_wireframe'],
                    show_filled=state['show_filled'],
                    backface_culling=state['backface_culling'],
                    show_normals=state['show_normals'],
                    texture_enabled=state['texture_enabled']
                )
                
                total_faces = visible + hidden
                visible_percent = (visible / total_faces * 100) if total_faces > 0 else 0
                
                # Информация для UI
                model_info = {
                    'name': state['current_model_name'],
                    'vertices': len(state['current_model'].vertices),
                    'faces': len(state['current_model'].faces),
                    'has_texture': hasattr(state['current_model'], 'tex_coords') and 
                                   len(state['current_model'].tex_coords) > 0,
                }
                
                stats = {
                    'visible': visible,
                    'hidden': hidden,
                    'visible_percent': visible_percent,
                }
                
                # Текущие настройки
                current_shading = state['shading_mode'].upper()
                if current_shading == 'PHONG':
                    shading_info = f"Phong (P)"
                elif current_shading == 'GOURAUD':
                    shading_info = f"Gouraud (P)"
                else:
                    shading_info = f"Flat (P)"
                
                settings = {
                    'auto_rotate': state['auto_rotate'],
                    'wireframe': state['show_wireframe'],
                    'filled': state['show_filled'],
                    'culling': state['backface_culling'],
                    'normals': state['show_normals'],
                    'color': renderer.get_current_color_name(),
                    'shading_mode': shading_info,
                    'texture': 'ВКЛ' if state['texture_enabled'] else 'ВЫКЛ',
                    'light_intensity': renderer.light.intensity,
                    'ambient': renderer.lambert_shader.ambient_intensity,
                    'specular': renderer.phong_shader.specular_intensity,
                    'shininess': renderer.phong_shader.shininess,
                    'light_x': renderer.light.position[0],
                    'light_y': renderer.light.position[1],
                    'light_z': renderer.light.position[2],
                }
                
                rot_x, rot_y, rot_z = camera.get_rotation_angles_degrees()
                camera_info = {
                    'pos_x': camera.position[0],
                    'pos_y': camera.position[1],
                    'pos_z': camera.position[2],
                    'target_x': camera.target[0],
                    'target_y': camera.target[1],
                    'target_z': camera.target[2],
                    'scale': camera.scale,
                    'angle_x': rot_x,
                    'angle_y': rot_y,
                    'angle_z': rot_z,
                }
                
                # Рендеринг UI
                ui.draw_main_ui(screen, model_info, stats, settings, camera_info)
                
                # Элементы управления ручным вращением
                ui.draw_rotation_controls(screen, WIDTH - 210, HEIGHT - 120)
            
            # Уведомление
            if state['notification'] and state['notification_time'] > 0:
                ui.draw_notification(
                    screen, 
                    state['notification'], 
                    ui.success_color if "загружена" in state['notification'].lower() else ui.highlight_color
                )
        
        # Обновление экрана
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()