import numpy as np

class Vertex:
    def __init__(self, position, normal=None, color=None):
        self.position = np.array(position, dtype=float)
        self.normal = np.array(normal if normal is not None else [0, 0, 0], dtype=float)
        self.color = color

class Triangle:
    def __init__(self, vertices):
        self.vertices = vertices
        self.normal = None
        self.calculate_normal()
    
    def calculate_normal(self):
        """Вычисление нормали грани"""
        if len(self.vertices) < 3:
            self.normal = np.array([0, 0, 1], dtype=float)
            return
            
        v1 = self.vertices[1].position - self.vertices[0].position
        v2 = self.vertices[2].position - self.vertices[0].position
        self.normal = np.cross(v1, v2)
        norm = np.linalg.norm(self.normal)
        if norm > 0:
            self.normal = self.normal / norm
        else:
            self.normal = np.array([0, 0, 1], dtype=float)
    
    def is_front_facing(self, camera_direction):
        """Проверка, является ли грань лицевой (backface culling)"""
        if self.normal is None:
            return True
        return np.dot(self.normal, camera_direction) < 0

class Mesh:
    def __init__(self):
        self.vertices = []
        self.triangles = []
        self.position = np.array([0.0, 0.0, 0.0])
        self.rotation = np.array([0.0, 0.0, 0.0])
        self.scale = np.array([1.0, 1.0, 1.0])
    
    def apply_transformations(self):
        """Применение аффинных преобразований"""
        transformation = self.get_transformation_matrix()
        
        # Сохраняем исходные позиции и нормали
        original_positions = [v.position.copy() for v in self.vertices]
        original_normals = [v.normal.copy() for v in self.vertices]
        
        for i, vertex in enumerate(self.vertices):
            # Преобразование позиции
            pos_homogeneous = np.append(original_positions[i], 1.0)
            transformed_pos = transformation @ pos_homogeneous
            vertex.position = transformed_pos[:3] / transformed_pos[3]
            
            # Преобразование нормали (только поворот)
            rotation_matrix = transformation[:3, :3]
            vertex.normal = rotation_matrix @ original_normals[i]
            
            # Нормализуем нормаль
            norm = np.linalg.norm(vertex.normal)
            if norm > 0:
                vertex.normal = vertex.normal / norm
        
        # Пересчитываем нормали граней
        for triangle in self.triangles:
            triangle.calculate_normal()
    
    def get_transformation_matrix(self):
        """Создание матрицы преобразования"""
        # Масштабирование
        S = np.diag([self.scale[0], self.scale[1], self.scale[2], 1.0])
        
        # Поворот
        Rx = self._rotation_matrix_x(self.rotation[0])
        Ry = self._rotation_matrix_y(self.rotation[1])
        Rz = self._rotation_matrix_z(self.rotation[2])
        R = Rz @ Ry @ Rx
        
        # Перенос
        T = np.eye(4)
        T[:3, 3] = self.position
        
        return T @ R @ S
    
    def _rotation_matrix_x(self, angle):
        c, s = np.cos(angle), np.sin(angle)
        return np.array([
            [1, 0, 0, 0],
            [0, c, -s, 0],
            [0, s, c, 0],
            [0, 0, 0, 1]
        ], dtype=float)
    
    def _rotation_matrix_y(self, angle):
        c, s = np.cos(angle), np.sin(angle)
        return np.array([
            [c, 0, s, 0],
            [0, 1, 0, 0],
            [-s, 0, c, 0],
            [0, 0, 0, 1]
        ], dtype=float)
    
    def _rotation_matrix_z(self, angle):
        c, s = np.cos(angle), np.sin(angle)
        return np.array([
            [c, -s, 0, 0],
            [s, c, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=float)
    
    def _calculate_vertex_normals(self):
        """Вычисление нормалей вершин как среднее нормалей смежных граней"""
        # Сбрасываем нормали
        for vertex in self.vertices:
            vertex.normal = np.array([0.0, 0.0, 0.0], dtype=float)
        
        # Суммируем нормали граней для каждой вершины
        for triangle in self.triangles:
            triangle.calculate_normal()  # Убедимся, что нормаль грани вычислена
            for vertex in triangle.vertices:
                vertex.normal += triangle.normal
        
        # Нормализуем
        for vertex in self.vertices:
            norm = np.linalg.norm(vertex.normal)
            if norm > 0:
                vertex.normal = vertex.normal / norm
            else:
                vertex.normal = np.array([0.0, 0.0, 1.0], dtype=float)