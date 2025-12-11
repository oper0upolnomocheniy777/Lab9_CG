# camera.py
import numpy as np

class Camera:
    def __init__(self, position, target, up, aspect_ratio=1.0):
        self.position = np.array(position)
        self.target = np.array(target)
        self.up = np.array(up)
        self.aspect_ratio = aspect_ratio
        self.scale = 0.8
        
        # Ручное вращение (углы в радианах)
        self.rotation_x = 0
        self.rotation_y = 0
        self.rotation_z = 0
        
        # Скорость вращения
        self.rotation_speed = 0.02
    
    def get_view_projection_matrix(self):
        """Матрица вида-проекции с учетом вращения камеры"""
        # Матрица вращения
        rx = self.rotation_x
        ry = self.rotation_y
        rz = self.rotation_z
        
        # Матрицы вращения по осям
        if rx != 0:
            c, s = np.cos(rx), np.sin(rx)
            rot_x = np.array([
                [1, 0, 0, 0],
                [0, c, -s, 0],
                [0, s, c, 0],
                [0, 0, 0, 1]
            ])
        else:
            rot_x = np.eye(4)
        
        if ry != 0:
            c, s = np.cos(ry), np.sin(ry)
            rot_y = np.array([
                [c, 0, s, 0],
                [0, 1, 0, 0],
                [-s, 0, c, 0],
                [0, 0, 0, 1]
            ])
        else:
            rot_y = np.eye(4)
        
        if rz != 0:
            c, s = np.cos(rz), np.sin(rz)
            rot_z = np.array([
                [c, -s, 0, 0],
                [s, c, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])
        else:
            rot_z = np.eye(4)
        
        # Комбинированное вращение
        rotation = rot_z @ rot_y @ rot_x
        
        # Матрица проекции с масштабом
        proj_matrix = np.array([
            [self.scale/self.aspect_ratio, 0, 0, 0],
            [0, self.scale, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        return proj_matrix @ rotation
    
    def rotate(self, axis, angle):
        """Вращение камеры по указанной оси"""
        if axis == 'x':
            self.rotation_x += angle
        elif axis == 'y':
            self.rotation_y += angle
        elif axis == 'z':
            self.rotation_z += angle
    
    def zoom_in(self, amount=0.1):
        """Увеличить масштаб"""
        self.scale = min(2.0, self.scale + amount)
    
    def zoom_out(self, amount=0.1):
        """Уменьшить масштаб"""
        self.scale = max(0.1, self.scale - amount)
    
    def reset(self):
        """Сброс камеры"""
        self.rotation_x = 0
        self.rotation_y = 0
        self.rotation_z = 0
        self.scale = 0.8
    
    def get_rotation_angles_degrees(self):
        """Получить углы вращения в градусах"""
        return (
            np.degrees(self.rotation_x),
            np.degrees(self.rotation_y),
            np.degrees(self.rotation_z)
        )