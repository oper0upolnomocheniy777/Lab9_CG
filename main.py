# main.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pygame
import numpy as np
from point import Point
from camera import Camera
from model_loader import Model3D, load_obj, create_cube
from renderer import Renderer
from ui import UI
from lighting import Light, LambertShader, GouraudShader

def create_transformation_matrices(angle_x, angle_y, angle_z, scale_factor=1.0):
    """Создает матрицу преобразования модели"""
    # Только вращение, без масштабирования здесь
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
    
    # Только вращение, масштаб уже в модели
    return rotation_z @ rotation_y @ rotation_x

def load_all_models():
    """Загрузка всех доступных моделей"""
    models = {}
    
    # Загружаем чайник
    teapot = load_obj("utah_teapot_lowpy.obj")
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
    
    # Создаем встроенный куб
    models["Куб (встр.)"] = create_cube()
    
    return models

def main():
    # Инициализация
    pygame.init()
    WIDTH, HEIGHT = 1024, 768
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("3D Renderer - Advanced OBJ Viewer")
    
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
        'show_wireframe': True,
        'show_filled': True,
        'backface_culling': True,
        'show_normals': False,
        'notification': None,
        'notification_time': 0,
    }
    
    # Сохраняем оригинальные вершины текущей модели
    if state['current_model']:
        state['original_vertices'] = [
            Point(v.x, v.y, v.z) for v in state['current_model'].vertices
        ]
    
    # Состояние нажатых клавиш
        # Состояние нажатых клавиш
        # Состояние нажатых клавиш (добавить перед while running)
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
                        state['original_vertices'] = [
                            Point(v.x, v.y, v.z) for v in state['current_model'].vertices
                        ]
                        state['angle_x'] = state['angle_y'] = state['angle_z'] = 0
                        camera.reset()
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
                    
                    elif event.key == pygame.K_c:  # Смена цвета
                        renderer.next_color()
                        state['notification'] = f"Цвет: {renderer.get_current_color_name()}"
                        state['notification_time'] = 1.0
                    
                    elif event.key == pygame.K_g:  # Переключение режима шейдинга
                        shading_mode = renderer.toggle_shading_mode()
                        state['notification'] = f"Режим шейдинга: {shading_mode}"
                        state['notification_time'] = 1.0

                    elif event.key == pygame.K_l:  # Показать/скрыть информацию об освещении
                        renderer.show_light_info = not renderer.show_light_info
                        state['notification'] = f"Инфо освещения: {'ВКЛ' if renderer.show_light_info else 'ВЫКЛ'}"
                        state['notification_time'] = 1.0

                    elif event.key == pygame.K_i:  # Увеличить интенсивность света
                        renderer.light.intensity = min(2.0, renderer.light.intensity + 0.1)
                        state['notification'] = f"Интенсивность света: {renderer.light.intensity:.1f}"
                        state['notification_time'] = 0.5

                    elif event.key == pygame.K_k:  # Уменьшить интенсивность света
                        renderer.light.intensity = max(0.1, renderer.light.intensity - 0.1)
                        state['notification'] = f"Интенсивность света: {renderer.light.intensity:.1f}"
                        state['notification_time'] = 0.5

                    elif event.key == pygame.K_o:  # Увеличить ambient
                        renderer.lambert_shader.ambient_intensity = min(1.0, renderer.lambert_shader.ambient_intensity + 0.05)
                        state['notification'] = f"Ambient освещение: {renderer.lambert_shader.ambient_intensity:.2f}"
                        state['notification_time'] = 0.5

                    elif event.key == pygame.K_p:  # Уменьшить ambient
                        renderer.lambert_shader.ambient_intensity = max(0.0, renderer.lambert_shader.ambient_intensity - 0.05)
                        state['notification'] = f"Ambient освещение: {renderer.lambert_shader.ambient_intensity:.2f}"
                        state['notification_time'] = 0.5
                    
                    elif event.key == pygame.K_h:  # Управление светом по X
                        if event.mod & pygame.KMOD_SHIFT:  # Shift+H
                            renderer.light.position[0] -= 0.1
                            state['notification'] = f"Свет X: {renderer.light.position[0]:.1f}"
                            state['notification_time'] = 0.5
                        else:  # Просто H
                            renderer.light.position[0] += 0.1
                            state['notification'] = f"Свет X: {renderer.light.position[0]:.1f}"
                            state['notification_time'] = 0.5
                    
                    elif event.key == pygame.K_j:  # Управление светом по Y
                        if event.mod & pygame.KMOD_SHIFT:  # Shift+J
                            renderer.light.position[1] -= 0.1
                            state['notification'] = f"Свет Y: {renderer.light.position[1]:.1f}"
                            state['notification_time'] = 0.5
                        else:  # Просто J
                            renderer.light.position[1] += 0.1
                            state['notification'] = f"Свет Y: {renderer.light.position[1]:.1f}"
                            state['notification_time'] = 0.5
                    
                    elif event.key == pygame.K_u:  # Управление светом по Z
                        if event.mod & pygame.KMOD_SHIFT:  # Shift+U
                            renderer.light.position[2] -= 0.1
                            state['notification'] = f"Свет Z: {renderer.light.position[2]:.1f}"
                            state['notification_time'] = 0.5
                        else:  # Просто U
                            renderer.light.position[2] += 0.1
                            state['notification'] = f"Свет Z: {renderer.light.position[2]:.1f}"
                            state['notification_time'] = 0.5
                    
                    elif event.key == pygame.K_r:
                        state['angle_x'] = state['angle_y'] = state['angle_z'] = 0
                        camera.reset()
                        state['notification'] = "Вращение и масштаб сброшены"
                        state['notification_time'] = 1.0
                    
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
            
            if keys_pressed[pygame.K_y]:
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
            if state['current_model']:
                transform_matrix = create_transformation_matrices(
                    state['angle_x'], 
                    state['angle_y'], 
                    state['angle_z']
                )
                
                # Применяем преобразование ко всей модели
                state['current_model'].apply_transform(transform_matrix)
                
            # Восстанавливаем и преобразуем вершины
            for i, vertex in enumerate(state['current_model'].vertices):
                    orig = state['original_vertices'][i]
                    vertex.x = orig.x
                    vertex.y = orig.y
                    vertex.z = orig.z
                    vertex.transform(transform_matrix)
                
            # Рендеринг модели
            if state['current_model']:
                visible, hidden = renderer.render(
                    screen, 
                    state['current_model'], 
                    camera,
                    show_wireframe=state['show_wireframe'],
                    show_filled=state['show_filled'],
                    backface_culling=state['backface_culling'],
                    show_normals=state['show_normals']  # Этот параметр теперь поддерживается
                )
                
                total_faces = visible + hidden
                visible_percent = (visible / total_faces * 100) if total_faces > 0 else 0
                
                # Информация для UI
                model_info = {
                    'name': state['current_model_name'],
                    'vertices': len(state['current_model'].vertices),
                    'faces': len(state['current_model'].faces),
                }
                
                stats = {
                    'visible': visible,
                    'hidden': hidden,
                    'visible_percent': visible_percent,
                }
                
                settings = {
                    'auto_rotate': state['auto_rotate'],
                    'wireframe': state['show_wireframe'],
                    'filled': state['show_filled'],
                    'culling': state['backface_culling'],
                    'normals': state['show_normals'],
                    'color': renderer.get_current_color_name(),
                    'gouraud': renderer.use_gouraud,
                    'light_intensity': renderer.light.intensity,
                    'ambient': renderer.lambert_shader.ambient_intensity,
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