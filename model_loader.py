# model_loader.py
import numpy as np
from point import Point

class Face:
    def __init__(self, indices, tex_indices=None):
        self.vertex_indices = indices
        self.tex_indices = tex_indices if tex_indices else []
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
        return f"Face({self.vertex_indices}, tex={self.tex_indices})"

class Model3D:
    def __init__(self, vertices, faces, tex_coords=None):
        self.vertices = vertices
        self.faces = faces
        self.tex_coords = tex_coords if tex_coords else []
        self.calculate_face_normals()
        self.calculate_vertex_normals()
    
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
        
        # После преобразования пересчитываем нормали
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
        return f"Model3D(vertices={len(self.vertices)}, faces={len(self.faces)}, tex_coords={len(self.tex_coords)})"

def load_obj(filename):
    """Загрузка OBJ файла с текстурными координатами"""
    vertices = []
    tex_coords = []
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
                
                elif parts[0] == 'vt':
                    if len(parts) >= 3:
                        u = float(parts[1])
                        v = float(parts[2])
                        tex_coords.append([u, v])
                
                elif parts[0] == 'f':
                    vertex_indices = []
                    tex_indices = []
                    
                    for part in parts[1:]:
                        indices = part.split('/')
                        if indices[0]:
                            # Индекс вершины
                            vertex_idx = int(indices[0]) - 1
                            if 0 <= vertex_idx:
                                vertex_indices.append(vertex_idx)
                            
                            # Индекс текстурной координаты (если есть)
                            if len(indices) > 1 and indices[1]:
                                tex_idx = int(indices[1]) - 1
                                if 0 <= tex_idx < len(tex_coords):
                                    tex_indices.append(tex_idx)
                                else:
                                    tex_indices.append(-1)  # Отметка об отсутствии
                            else:
                                tex_indices.append(-1)
                    
                    if len(vertex_indices) >= 3:
                        faces.append(Face(vertex_indices, tex_indices))
        
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
        
        # Создаем точки
        points = [Point(v[0], v[1], v[2]) for v in vertices_array]
        
        model = Model3D(points, faces, tex_coords)
        print(f"✓ Загружено из {filename}: {len(points)} вершин, {len(faces)} граней, {len(tex_coords)} текстурных координат")
        return model
    
    except Exception as e:
        print(f"✗ Ошибка загрузки {filename}: {e}")
        return None

def create_cube_with_texture():
    """Создание куба с текстурными координатами"""
    # Вершины куба
    vertices = [
        Point(-0.5, -0.5, -0.5),  # 0
        Point(0.5, -0.5, -0.5),   # 1
        Point(0.5, 0.5, -0.5),    # 2
        Point(-0.5, 0.5, -0.5),   # 3
        Point(-0.5, -0.5, 0.5),   # 4
        Point(0.5, -0.5, 0.5),    # 5
        Point(0.5, 0.5, 0.5),     # 6
        Point(-0.5, 0.5, 0.5),    # 7
    ]
    
    # Текстурные координаты для куба
    tex_coords = [
        [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],  # Для каждой грани
        [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],
        [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],
        [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],
        [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],
        [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],
    ]
    
    # Грани куба с текстурными координатами
    # Каждая грань: (индексы вершин, индексы текстурных координат)
    faces = [
        Face([0, 3, 2, 1], [0, 1, 2, 3]),  # Задняя грань
        Face([4, 5, 6, 7], [4, 5, 6, 7]),  # Передняя грань
        Face([0, 4, 7, 3], [8, 9, 10, 11]),  # Левая грань
        Face([1, 2, 6, 5], [12, 13, 14, 15]),  # Правая грань
        Face([0, 1, 5, 4], [16, 17, 18, 19]),  # Нижняя грань
        Face([2, 3, 7, 6], [20, 21, 22, 23]),  # Верхняя грань
    ]
    
    model = Model3D(vertices, faces, tex_coords)
    print(f"✓ Создан куб с текстурой: {len(vertices)} вершин, {len(faces)} граней")
    return model

def create_cube():
    """Создание куба без текстуры (для обратной совместимости)"""
    return create_cube_with_texture()