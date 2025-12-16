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
    
    def has_texture_coords(self):
        """Проверка, есть ли у модели текстурные координаты"""
        return len(self.tex_coords) > 0
    
    def __repr__(self):
        has_tex = "с текстурой" if self.has_texture_coords() else "без текстуры"
        return f"Model3D(vertices={len(self.vertices)}, faces={len(self.faces)}, {has_tex})"

def load_obj(filename):
    """Загрузка OBJ файла с нормализацией и текстурными координатами"""
    vertices = []
    tex_coords = []  # VT - текстурные координаты
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
                
                elif parts[0] == 'vt':  # Текстурные координаты
                    if len(parts) >= 3:
                        u = float(parts[1])
                        v = float(parts[2])
                        tex_coords.append([u, v])
                
                elif parts[0] == 'f':  # Грани
                    vertex_indices = []
                    tex_indices = []
                    
                    for part in parts[1:]:
                        indices = part.split('/')
                        if indices[0]:
                            vertex_idx = int(indices[0]) - 1
                            if 0 <= vertex_idx:
                                vertex_indices.append(vertex_idx)
                        
                        # Текстурные координаты (второй элемент после '/')
                        if len(indices) > 1 and indices[1]:
                            tex_idx = int(indices[1]) - 1
                            if 0 <= tex_idx:
                                tex_indices.append(tex_idx)
                    
                    if len(vertex_indices) >= 3:
                        # Если для этой грани нет текстурных координат, оставляем список пустым
                        if len(tex_indices) != len(vertex_indices):
                            tex_indices = []
                        
                        face = Face(vertex_indices, tex_indices if tex_indices else None)
                        faces.append(face)
        
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
        
        model = Model3D(points, faces, tex_coords)
        print(f"✓ Загружено из {filename}: {len(points)} вершин, {len(faces)} граней, {len(tex_coords)} текстурных координат")
        return model
    
    except Exception as e:
        print(f"✗ Ошибка загрузки {filename}: {e}")
        return None

def create_cube():
    """Создание куба с нормалями (оригинальная функция - без текстуры)"""
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

def create_textured_cube():
    """Создание куба с текстурными координатами (дополнительная функция)"""
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
    
    # Текстурные координаты для куба (развертка куба)
    tex_coords = [
        [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],  # 0-3: первый квадрат
        [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],  # 4-7: второй квадрат
        [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],  # 8-11: третий квадрат
        [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],  # 12-15: четвертый квадрат
        [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],  # 16-19: пятый квадрат
        [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],  # 20-23: шестой квадрат
    ]
    
    # Грани куба с текстурными координатами
    faces = [
        # Задняя грань
        Face([0, 3, 2, 1], [0, 3, 2, 1]),
        # Передняя грань
        Face([4, 5, 6, 7], [4, 5, 6, 7]),
        # Левая грань
        Face([0, 4, 7, 3], [8, 9, 10, 11]),
        # Правая грань
        Face([1, 2, 6, 5], [12, 13, 14, 15]),
        # Нижняя грань
        Face([0, 1, 5, 4], [16, 17, 18, 19]),
        # Верхняя грань
        Face([2, 3, 7, 6], [20, 21, 22, 23]),
    ]
    
    model = Model3D(vertices, faces, tex_coords)
    print(f"✓ Создан текстурированный куб: {len(vertices)} вершин, {len(faces)} граней")
    return model

def create_textured_pyramid():
    """Создание пирамиды с текстурными координатами (дополнительная функция)"""
    vertices = [
        Point(0, 0.5, 0),     # 0 - вершина
        Point(-0.5, -0.5, -0.5),  # 1
        Point(0.5, -0.5, -0.5),   # 2
        Point(0.5, -0.5, 0.5),    # 3
        Point(-0.5, -0.5, 0.5),   # 4
    ]
    
    # Текстурные координаты
    tex_coords = [
        [0.5, 1.0],  # 0 - вершина
        [0.0, 0.0],  # 1
        [1.0, 0.0],  # 2
        [1.0, 0.0],  # 3
        [0.0, 0.0],  # 4
        [0.0, 1.0],  # 5 - дополнительная для основания
        [1.0, 1.0],  # 6 - дополнительная для основания
    ]
    
    # Грани пирамиды
    faces = [
        Face([0, 1, 2], [0, 1, 2]),        # Передняя треугольная грань
        Face([0, 2, 3], [0, 2, 6]),        # Правая треугольная грань
        Face([0, 3, 4], [0, 6, 5]),        # Задняя треугольная грань
        Face([0, 4, 1], [0, 5, 1]),        # Левая треугольная грань
        Face([1, 4, 3, 2], [1, 5, 6, 2]),  # Квадратное основание
    ]
    
    model = Model3D(vertices, faces, tex_coords)
    print(f"✓ Создана текстурированная пирамида: {len(vertices)} вершин, {len(faces)} граней")
    return model