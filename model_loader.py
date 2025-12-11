# model_loader.py
import numpy as np
from point import Point

class Face:
    def __init__(self, indices):
        self.vertex_indices = indices
        self.normal_x = 0
        self.normal_y = 0
        self.normal_z = 0
    
    def calculate_normal(self, vertices):
        """Вычисление нормали грани"""
        if len(self.vertex_indices) < 3:
            return None
        
        # Берем первые три вершины
        v0 = vertices[self.vertex_indices[0]]
        v1 = vertices[self.vertex_indices[1]]
        v2 = vertices[self.vertex_indices[2]]
        
        # Векторы двух ребер
        edge1_x = v1.x - v0.x
        edge1_y = v1.y - v0.y
        edge1_z = v1.z - v0.z
        
        edge2_x = v2.x - v0.x
        edge2_y = v2.y - v0.y
        edge2_z = v2.z - v0.z
        
        # Векторное произведение
        normal_x = edge1_y * edge2_z - edge1_z * edge2_y
        normal_y = edge1_z * edge2_x - edge1_x * edge2_z
        normal_z = edge1_x * edge2_y - edge1_y * edge2_x
        
        # Нормализация
        length = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
        if length > 0:
            normal_x /= length
            normal_y /= length
            normal_z /= length
        
        self.normal_x = normal_x
        self.normal_y = normal_y
        self.normal_z = normal_z
        
        return (normal_x, normal_y, normal_z)
    
    def __repr__(self):
        return f"Face({self.vertex_indices})"

class Model3D:
    def __init__(self, vertices, faces):
        self.vertices = vertices
        self.faces = faces
        self.calculate_face_normals()
        self.calculate_vertex_normals()  # Добавляем расчет нормалей вершин
    
    def calculate_face_normals(self):
        """Вычисление нормалей для всех граней"""
        for face in self.faces:
            face.calculate_normal(self.vertices)
    
    def calculate_vertex_normals(self):
        """Вычисление нормалей вершин как среднее нормалей смежных граней"""
        # Инициализируем нормали вершин
        for vertex in self.vertices:
            vertex.normal_x = 0
            vertex.normal_y = 0
            vertex.normal_z = 0
        
        # Суммируем нормали граней для каждой вершины
        for face in self.faces:
            for idx in face.vertex_indices:
                if idx < len(self.vertices):
                    vertex = self.vertices[idx]
                    vertex.normal_x += face.normal_x
                    vertex.normal_y += face.normal_y
                    vertex.normal_z += face.normal_z
        
        # Нормализуем нормали вершин
        for vertex in self.vertices:
            length = np.sqrt(vertex.normal_x**2 + vertex.normal_y**2 + vertex.normal_z**2)
            if length > 0:
                vertex.normal_x /= length
                vertex.normal_y /= length
                vertex.normal_z /= length
    
    def apply_transform(self, matrix):
        """Применение матрицы преобразования с обновлением нормалей"""
        # Применяем преобразование к вершинам
        for vertex in self.vertices:
            vertex.transform(matrix)
        
        # После преобразования пересчитываем нормали граней и вершин
        self.recalculate_normals()
    
    def recalculate_normals(self):
        """Пересчет нормалей после преобразований"""
        self.calculate_face_normals()
        self.calculate_vertex_normals()
    
    def set_vertex_colors(self, colors):
        """Установка цветов для вершин"""
        for i, vertex in enumerate(self.vertices):
            if i < len(colors):
                vertex.color = colors[i]
    
    def __repr__(self):
        return f"Model3D(vertices={len(self.vertices)}, faces={len(self.faces)})"

def load_obj(filename):
    """Загрузка OBJ файла с нормализацией"""
    vertices = []
    faces = []
    
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if not parts:
                    continue
                
                if parts[0] == 'v':
                    if len(parts) >= 4:
                        x = float(parts[1])
                        y = float(parts[2])
                        z = float(parts[3])
                        vertices.append([x, y, z])
                
                elif parts[0] == 'f':
                    vertex_indices = []
                    for part in parts[1:]:
                        indices = part.split('/')
                        if indices[0]:
                            vertex_idx = int(indices[0]) - 1
                            if 0 <= vertex_idx:
                                vertex_indices.append(vertex_idx)
                    
                    if len(vertex_indices) >= 3:
                        faces.append(vertex_indices)
        
        # Нормализация модели
        if vertices:
            vertices_array = np.array(vertices)
            
            # Центрируем
            center = np.mean(vertices_array, axis=0)
            vertices_array = vertices_array - center
            
            # Масштабируем
            max_dist = np.max(np.abs(vertices_array))
            if max_dist > 0:
                vertices_array = vertices_array / max_dist * 0.6
        
        # Создаем точки (без нормалей, они вычислятся позже)
        points = [Point(v[0], v[1], v[2]) for v in vertices_array]
        
        # Создаем грани
        model_faces = [Face(indices) for indices in faces]
        
        model = Model3D(points, model_faces)
        print(f"✓ Загружено из {filename}: {len(points)} вершин, {len(faces)} граней")
        return model
    
    except Exception as e:
        print(f"✗ Ошибка загрузки {filename}: {e}")
        return None

def create_cube():
    """Создание куба с нормалями"""
    # Создаем вершины без нормалей (они вычислятся автоматически)
    vertices = [
        Point(-0.5, -0.5, -0.5),
        Point(0.5, -0.5, -0.5),
        Point(0.5, 0.5, -0.5),
        Point(-0.5, 0.5, -0.5),
        Point(-0.5, -0.5, 0.5),
        Point(0.5, -0.5, 0.5),
        Point(0.5, 0.5, 0.5),
        Point(-0.5, 0.5, 0.5),
    ]
    
    faces = [
        Face([0, 3, 2, 1]),  # Задняя
        Face([4, 5, 6, 7]),  # Передняя
        Face([0, 4, 7, 3]),  # Левая
        Face([1, 2, 6, 5]),  # Правая
        Face([0, 1, 5, 4]),  # Нижняя
        Face([2, 3, 7, 6]),  # Верхняя
    ]
    
    model = Model3D(vertices, faces)
    print(f"✓ Создан куб: {len(vertices)} вершин, {len(faces)} граней")
    return model