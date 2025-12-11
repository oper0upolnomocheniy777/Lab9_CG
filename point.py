# point.py
import numpy as np

class Point:
    def __init__(self, x, y, z, normal_x=0, normal_y=0, normal_z=0, color=None):
        self.x = x
        self.y = y
        self.z = z
        self.normal_x = normal_x
        self.normal_y = normal_y
        self.normal_z = normal_z
        self.color = color  # Цвет вершины для Гуро шейдинга
    
    def to_array(self):
        return np.array([self.x, self.y, self.z])
    
    def to_homogeneous(self):
        return np.array([self.x, self.y, self.z, 1.0])
    
    def transform(self, matrix):
        homogeneous = self.to_homogeneous()
        transformed = matrix @ homogeneous
        if transformed[3] != 0:
            self.x = transformed[0] / transformed[3]
            self.y = transformed[1] / transformed[3]
            self.z = transformed[2] / transformed[3]
    
    def normalize(self):
        """Нормализация вектора"""
        length = np.sqrt(self.normal_x**2 + self.normal_y**2 + self.normal_z**2)
        if length > 0:
            self.normal_x /= length
            self.normal_y /= length
            self.normal_z /= length
    
    def dot(self, other):
        """Скалярное произведение с другим вектором"""
        return self.normal_x * other.normal_x + self.normal_y * other.normal_y + self.normal_z * other.normal_z
    
    def __repr__(self):
        return f"Point({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"