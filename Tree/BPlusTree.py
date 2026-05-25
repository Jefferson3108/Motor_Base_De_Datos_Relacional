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
    
    def delete(self, key):
        if self.root is None:
            return  # árbol vacío, nada que eliminar
        self._delete(self.root, key)
        if len(self.root.keys) == 0 and not self.root.is_leaf:
            # si la raíz quedó sin claves, hacer que el primer hijo sea la nueva raíz
            self.root = self.root.children[0]
        if len(self.root.keys) == 0 and self.root.is_leaf:
            # si la raíz es una hoja vacía, eliminar el árbol
            self.root = None
    
    def _delete(self, node, key):
        if node.is_leaf:
            # eliminar la clave y el registro asociado de la hoja
            if key in node.keys:
                index = node.keys.index(key)
                del node.keys[index]
                del node.records[index]
            return

        # nodo interno: encontrar el hijo correcto para bajar
        i = 0
        while i < len(node.keys) and key >= node.keys[i]:
            i += 1
        # bajar al hijo correspondiente
        self._delete(node.children[i], key)
        #  después de eliminar, verificar si el hijo se quedó con muy pocas claves y necesita reequilibrio
        if i < len(node.children) and len(node.children[i].keys) < self.order // 2:
            self._rebalance(node, i)

            
        
    def _rebalance(self, parent, index):
        # intentar tomar prestado del hermano izquierdo
        min_keys = self.order // 2
        if index > 0 and len(parent.children[index - 1].keys) > min_keys:
            left_sibling = parent.children[index - 1]
            current = parent.children[index]
            if current.is_leaf:
                current.keys.insert(0, left_sibling.keys[-1])
                current.records.insert(0, left_sibling.records[-1])
                del left_sibling.keys[-1]
                del left_sibling.records[-1]
                parent.keys[index - 1] = current.keys[0]  # actualizar clave del padre
            else:
                current.keys.insert(0, parent.keys[index - 1])
                current.children.insert(0, left_sibling.children.pop())
                parent.keys[index - 1] = left_sibling.keys.pop()

        # intentar tomar prestado del hermano derecho
        elif index < len(parent.children) - 1 and len(parent.children[index + 1].keys) > min_keys:
            right_sibling = parent.children[index + 1]
            current = parent.children[index]
            if current.is_leaf:
                current.keys.insert(len(current.keys), right_sibling.keys[0])
                current.records.insert(len(current.records), right_sibling.records[0])
                del right_sibling.keys[0]
                del right_sibling.records[0]
                parent.keys[index] = right_sibling.keys[0]  # actualizar clave del padre
            else:
                current.keys.append(parent.keys[index])
                current.children.append(right_sibling.children.pop(0))
                parent.keys[index] = right_sibling.keys.pop(0)
        else:


             # si no se puede tomar prestado de ningún hermano, fusionar con un hermano
             if index < len(parent.children) - 1:
                 self._merge(parent, index)
             else:
                 self._merge(parent, index - 1)

    def _merge(self, parent, index):
       # index = posición de la hoja IZQUIERDA en parent.children
       left  = parent.children[index]
       right = parent.children[index + 1]

       if left.is_leaf:
            # --- merge de hojas ---

            # 1. pasar todas las claves y records de la derecha a la izquierda
            left.keys    += right.keys
            left.records += right.records

            # 2. actualizar el puntero next — la izquierda ahora apunta
            #    a lo que apuntaba la derecha (saltamos la hoja que desaparece)
            left.next = right.next

            # 3. eliminar el separador del padre que dividía las dos hojas
            del parent.keys[index]

            # 4. eliminar la hoja derecha del padre (ya no existe)
            del parent.children[index + 1]

       else:
         # --- merge de nodos internos ---

         # 1. bajar el separador del padre al nodo izquierdo
         #    (necesario porque los hijos del derecho necesitan un separador)
         left.keys.append(parent.keys[index])

         # 2. pasar todas las claves del derecho al izquierdo
         left.keys += right.keys

         # 3. pasar todos los hijos del derecho al izquierdo
         left.children += right.children

         # 4. eliminar el separador del padre
         del parent.keys[index]

         # 5. eliminar el nodo derecho del padre
         del parent.children[index + 1]



tree = BPlusTree(order=3)
for i in [10, 20, 5, 6, 12, 30, 25]:
    tree.insert(i, f"Record {i}")

# caso 1 — eliminar sin déficit
tree.delete(12)
print(tree.search(12))   # None
print(tree.search(10))   # Record 10 ← vecino intacto

# caso 2 — eliminar con préstamo
tree.delete(10)
print(tree.search(10))   # None
print(tree.search(6))    # Record 6  ← debe seguir

# caso 3 — eliminar con merge
tree.delete(5)
print(tree.search(5))    # None
print(tree.search(6))    # Record 6  ← debe seguir

# eliminar algo que no existe
tree.delete(99)          # no debe explotar

# eliminar todo
for i in [6, 20, 25, 30]:
    tree.delete(i)
print(tree.search(30))   # None
print(tree.root)         # None o hoja vacía



               

            



      
        
      

 
    
        
        