# point.py
import numpy as np

class Point:
    def __init__(self, x, y, z, normal_x=0, normal_y=0, normal_z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.normal_x = float(normal_x)
        self.normal_y = float(normal_y)
        self.normal_z = float(normal_z)
    
    def __str__(self):
        return f"Point({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"
    
    def __repr__(self):
        return self.__str__()
    
    def to_array(self):
        """Преобразование в массив numpy"""
        return np.array([self.x, self.y, self.z])
    
    def to_homogeneous(self):
        """Преобразование в однородные координаты"""
        return np.array([self.x, self.y, self.z, 1.0])
    
    def copy(self):
        """Создание копии точки"""
        return Point(self.x, self.y, self.z, 
                    self.normal_x, self.normal_y, self.normal_z)
    
    def transform(self, matrix):
        """Применение матрицы преобразования к точке"""
        homogeneous = self.to_homogeneous()
        transformed = matrix @ homogeneous
        
        # Перспективное деление
        if transformed[3] != 0:
            transformed = transformed / transformed[3]
        
        self.x = transformed[0]
        self.y = transformed[1]
        self.z = transformed[2]
        return self
    
    def transform_normal(self, matrix):
        """Преобразование нормали"""
        # Используем только вращательную часть матрицы (3x3)
        rotation_matrix = matrix[:3, :3]
        normal_vec = np.array([self.normal_x, self.normal_y, self.normal_z])
        transformed_normal = rotation_matrix @ normal_vec
        
        # Нормализация
        length = np.linalg.norm(transformed_normal)
        if length > 0:
            transformed_normal = transformed_normal / length
        
        self.normal_x = transformed_normal[0]
        self.normal_y = transformed_normal[1]
        self.normal_z = transformed_normal[2]
        return self
    
    def normalize(self):
        """Нормализация вектора нормали"""
        length = np.sqrt(self.normal_x**2 + self.normal_y**2 + self.normal_z**2)
        if length > 0:
            self.normal_x /= length
            self.normal_y /= length
            self.normal_z /= length
    
    @staticmethod
    def from_array(arr):
        """Создание точки из массива"""
        return Point(arr[0], arr[1], arr[2])
    
    @staticmethod
    def from_homogeneous(homogeneous_arr):
        """Создание точки из однородных координат"""
        if homogeneous_arr[3] != 0:
            arr = homogeneous_arr / homogeneous_arr[3]
        else:
            arr = homogeneous_arr
        return Point(arr[0], arr[1], arr[2])
    
    def distance_to(self, other):
        """Расстояние до другой точки"""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return np.sqrt(dx*dx + dy*dy + dz*dz)