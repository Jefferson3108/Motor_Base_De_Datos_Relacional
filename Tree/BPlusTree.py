class BPlusNode:
    def __init__(self, order, leaf=False):
        self.order = order      # máximo de claves permitidas en el nodo
        self.is_leaf = leaf     # True si es hoja, False si es nodo interno
        self.keys = []          # claves de enrutamiento (nodo interno) o de datos (hoja)
        self.children = []      # punteros a nodos hijos (solo nodos internos)
        self.next = None        # puntero a la siguiente hoja (solo hojas, para range scan)


class BPlusleafNode(BPlusNode):
    def __init__(self, order):
        super().__init__(order=order, leaf=True)
        self.records = []       # valores asociados a cada clave (solo hojas)


class BPlusTree:
    def __init__(self, order):
        self.root = None        # raíz del árbol, None si está vacío
        self.order = order      # orden del árbol: máximo de claves por nodo

    def insert(self, key, record):
        # si el árbol está vacío, crear la primera hoja como raíz
        if self.root is None:
            self.root = BPlusleafNode(self.order)
            self.root.keys.append(key)
            self.root.records.append(record)
            return

        # insertar en el subárbol correspondiente
        self.insert_non_full(self.root, key, record)

        # si la raíz se desbordó, crear una nueva raíz y dividir
        # este es el único momento en que el árbol crece en altura
        if len(self.root.keys) >= self.order:
            new_root = BPlusNode(self.order)
            new_root.children.append(self.root)
            self.split_child_Tree_BPlus(new_root, 0)
            self.root = new_root

    def insert_non_full(self, node, key, record):
        if node.is_leaf:
            # encontrar la posición correcta para mantener las claves ordenadas
            i = 0
            while i < len(node.keys) and node.keys[i] < key:
                i += 1
            node.keys.insert(i, key)
            node.records.insert(i, record)
        else:
            # encontrar el hijo al que le corresponde esta clave
            i = len(node.keys) - 1
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1

            # si el hijo está lleno, dividirlo antes de bajar
            if len(node.children[i].keys) >= self.order:
                self.split_child_Tree_BPlus(node, i)
                # después del split el padre tiene una clave nueva
                # determinar a cuál de los dos hijos resultantes bajar
                if key > node.keys[i]:
                    i += 1

            self.insert_non_full(node.children[i], key, record)

    def split_child_Tree_BPlus(self, parent, index):
        full_child = parent.children[index]

        if full_child.is_leaf:
            # --- split de hoja ---
            # la clave del medio se COPIA al padre (queda en ambas hojas)
            mid = len(full_child.keys) // 2

            new_child = BPlusleafNode(self.order)
            # la mitad derecha va a la nueva hoja
            new_child.keys    = full_child.keys[mid:]
            new_child.records = full_child.records[mid:]
            # la mitad izquierda queda en la hoja original
            full_child.keys    = full_child.keys[:mid]
            full_child.records = full_child.records[:mid]

            # la primera clave de la nueva hoja sube al padre como separador
            key_to_move = new_child.keys[0]
            parent.keys.insert(index, key_to_move)
            parent.children.insert(index + 1, new_child)

            # mantener la lista enlazada de hojas actualizada
            new_child.next = full_child.next
            full_child.next = new_child

        else:
            # --- split de nodo interno ---
            # la clave del medio se MUEVE al padre (no queda en ningún hijo)
            mid = len(full_child.keys) // 2
            key_to_move = full_child.keys[mid]

            new_child = BPlusNode(self.order)
            new_child.is_leaf = False
            # claves y hijos a la derecha del medio van al nuevo nodo
            new_child.keys     = full_child.keys[mid + 1:]
            new_child.children = full_child.children[mid + 1:]
            # claves y hijos a la izquierda del medio quedan en el original
            full_child.keys     = full_child.keys[:mid]
            full_child.children = full_child.children[:mid + 1]

            parent.keys.insert(index, key_to_move)
            parent.children.insert(index + 1, new_child)

    def search(self, key):
        return self._search(self.root, key)

    def _search(self, node, key):
        if node is None:
            return None

        if node.is_leaf:
            # buscar linealmente en la hoja — las claves están ordenadas
            for i, k in enumerate(node.keys):
                if k == key:
                    return node.records[i]
            return None  # clave no encontrada

        # nodo interno: encontrar el hijo correcto y bajar
        i = 0
        while i < len(node.keys) and key >= node.keys[i]:
            i += 1
        return self._search(node.children[i], key)

tree = BPlusTree(5)
for i in [10, 20, 5, 15, 25, 30, 1, 6, 12, 18]:
    tree.insert(i, f"Record for {i}")
print(tree.search(15))  # Output: Record for 15
print(tree.search(100)) # Output: None (clave no encontrada)
print(tree.search(1))   # Output: Record for 1
print(tree.search(30))  # Output: Record for 30
print(tree.search(7))   # Output: None (clave no encontrada)
               

            



      
        
      

 
    
        
        