# model_loader.py
import numpy as np
from point import Point

class Face:
    def __init__(self, indices):
        self.vertex_indices = indices
        self.normal = None  # Нормаль грани будет вычисляться при рендеринге
    
    def __str__(self):
        return f"Face({self.vertex_indices})"
    
    def __repr__(self):
        return self.__str__()

class Model3D:
    def __init__(self, vertices, faces):
        self.vertices = vertices
        self.faces = faces
        self.calculate_vertex_normals()
    
    def calculate_vertex_normals(self):
        """Вычисление нормалей вершин как среднее нормалей смежных граней"""
        # Инициализируем нормали вершин
        for vertex in self.vertices:
            vertex.normal_x = 0
            vertex.normal_y = 0
            vertex.normal_z = 0
        
        # Для каждой грани вычисляем нормаль и добавляем к вершинам
        for face in self.faces:
            if len(face.vertex_indices) >= 3:
                # Вычисляем нормаль грани
                v0 = self.vertices[face.vertex_indices[0]]
                v1 = self.vertices[face.vertex_indices[1]]
                v2 = self.vertices[face.vertex_indices[2]]
                
                edge1 = np.array([v1.x - v0.x, v1.y - v0.y, v1.z - v0.z])
                edge2 = np.array([v2.x - v0.x, v2.y - v0.y, v2.z - v0.z])
                
                normal = np.cross(edge1, edge2)
                length = np.linalg.norm(normal)
                
                if length > 0:
                    normal = normal / length
                    
                    # Добавляем ко всем вершинам грани
                    for idx in face.vertex_indices:
                        vertex = self.vertices[idx]
                        vertex.normal_x += normal[0]
                        vertex.normal_y += normal[1]
                        vertex.normal_z += normal[2]
        
        # Нормализуем нормали вершин
        for vertex in self.vertices:
            length = np.sqrt(vertex.normal_x**2 + vertex.normal_y**2 + vertex.normal_z**2)
            if length > 0:
                vertex.normal_x /= length
                vertex.normal_y /= length
                vertex.normal_z /= length
    
    def apply_transform(self, matrix):
        """Применение преобразования к модели"""
        for vertex in self.vertices:
            vertex.transform(matrix)
            vertex.transform_normal(matrix)
    
    def recalculate_normals(self):
        """Пересчет нормалей после преобразований"""
        self.calculate_vertex_normals()

def load_obj(filename):
    """Загрузка OBJ файла"""
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
                
                if parts[0] == 'v':  # Вершины
                    if len(parts) >= 4:
                        x = float(parts[1])
                        y = float(parts[2])
                        z = float(parts[3])
                        vertices.append([x, y, z])
                
                elif parts[0] == 'f':  # Грани
                    vertex_indices = []
                    for part in parts[1:]:
                        indices = part.split('/')
                        if indices[0]:
                            vertex_idx = int(indices[0]) - 1
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
                vertices_array = vertices_array / max_dist * 0.7
        
        # Создаем точки
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
    """Создание куба"""
    # 8 вершин куба
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
    
    # 6 граней (каждая по 4 вершины)
    faces = [
        [0, 3, 2, 1],  # Задняя грань
        [4, 5, 6, 7],  # Передняя грань
        [0, 4, 7, 3],  # Левая грань
        [1, 2, 6, 5],  # Правая грань
        [0, 1, 5, 4],  # Нижняя грань
        [2, 3, 7, 6],  # Верхняя грань
    ]
    
    model_faces = [Face(indices) for indices in faces]
    model = Model3D(vertices, model_faces)
    print(f"✓ Создан куб: {len(vertices)} вершин, {len(faces)} граней")
    return model

def create_sphere(segments=16, rings=12):
    """Создание сферы с правильными нормалями"""
    vertices = []
    faces = []
    
    # Создаем вершины
    for i in range(rings + 1):
        phi = np.pi * i / rings
        y = np.cos(phi) * 0.5
        r = np.sin(phi) * 0.5
        
        for j in range(segments):
            theta = 2 * np.pi * j / segments
            x = r * np.cos(theta)
            z = r * np.sin(theta)
            
            # Нормаль = нормализованный вектор от центра к поверхности
            # Для сферы нормаль = (x, y, z) * 2 (так как радиус = 0.5)
            length = np.sqrt(x*x + y*y + z*z)
            if length > 0:
                normal_x = x / length
                normal_y = y / length
                normal_z = z / length
            else:
                normal_x, normal_y, normal_z = 0, 1, 0
            
            vertices.append(Point(x, y, z, normal_x, normal_y, normal_z))
    
    # Создаем грани
    for i in range(rings):
        for j in range(segments):
            a = i * segments + j
            b = i * segments + (j + 1) % segments
            c = (i + 1) * segments + (j + 1) % segments
            d = (i + 1) * segments + j
            
            # Важно: порядок вершин должен быть против часовой стрелки
            # для правильного вычисления нормали
            faces.append([a, b, c, d])
    
    model_faces = [Face(indices) for indices in faces]
    model = Model3D(vertices, model_faces)
    print(f"✓ Создана сфера: {len(vertices)} вершин, {len(faces)} граней")
    return model