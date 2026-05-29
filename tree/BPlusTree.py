class BPlusNode:
    """
    Nodo base utilizado en la implementación del árbol B+.

    Este nodo puede representar:
    - Un nodo interno
    - Un nodo hoja

    Atributos:
        order (int):
            Número máximo de claves permitidas en el nodo.

        is_leaf (bool):
            Indica si el nodo es hoja.
            - True  -> nodo hoja
            - False -> nodo interno

        keys (list):
            Lista de claves almacenadas en el nodo.

            En nodos internos:
                Se utilizan como claves separadoras
                para dirigir la búsqueda.

            En nodos hoja:
                Son las claves reales almacenadas.

        children (list):
            Lista de referencias a nodos hijos.
            Solo se utiliza en nodos internos.

        next (BPlusNode):
            Referencia a la siguiente hoja del árbol.

            Este puntero permite realizar:
            - búsquedas por rango
            - recorridos secuenciales eficientes
    """

    def __init__(self, order, leaf=False):

        # Número máximo de claves permitidas
        self.order = order

        # Define si el nodo es hoja o interno
        self.is_leaf = leaf

        # Claves almacenadas en el nodo
        self.keys = []

        # Hijos del nodo (solo nodos internos)
        self.children = []

        # Puntero a la siguiente hoja
        self.next = None


class BPlusleafNode(BPlusNode):
    """
    Representa un nodo hoja del árbol B+.

    Los nodos hoja almacenan:
    - claves reales
    - registros asociados a cada clave

    Además, las hojas se encuentran enlazadas
    secuencialmente mediante el atributo `next`,
    permitiendo búsquedas por rango eficientes.
    """

    def __init__(self, order):

        # Inicializar como nodo hoja
        super().__init__(order=order, leaf=True)

        # Registros asociados a cada clave
        self.records = []


class BPlusTree:
    """
    Implementación de un árbol B+.

    Características:
    - Inserción de claves
    - Búsqueda de registros
    - Eliminación de claves
    - Actualización de registros
    - División de nodos
    - Rebalanceo automático
    - Fusión de nodos

    El árbol B+ mantiene todas las claves reales
    almacenadas únicamente en las hojas.

    Los nodos internos funcionan únicamente
    como estructuras de navegación.
    """

    def __init__(self, order):
        """
        Inicializa un árbol B+ vacío.

        Args:
            order (int):
                Máximo número de claves permitidas
                en cada nodo.
        """

        # Raíz del árbol
        self.root = None

        # Orden del árbol
        self.order = order

    def insert(self, key, record):
        """
        Inserta una nueva clave junto con su registro asociado.

        Flujo general:
        1. Si el árbol está vacío, crear una hoja raíz.
        2. Insertar recursivamente.
        3. Si la raíz se desborda, dividirla.
        4. Crear una nueva raíz.

        Args:
            key:
                Clave que será insertada.

            record:
                Registro asociado a la clave.
        """
        # Caso especial:
        # árbol vacío
        if self.root is None:

            self.root = BPlusleafNode(self.order)
            self.root.keys.append(key)
            self.root.records.append(record)
            return

        # Insertar en el subárbol correspondiente
        self.insert_non_full(self.root, key, record)

        # Si la raíz excede el tamaño permitido,
        # el árbol aumenta su altura
        if len(self.root.keys) >= self.order:

            # Crear nueva raíz
            new_root = BPlusNode(self.order)

            # La raíz anterior se convierte en hijo
            new_root.children.append(self.root)

            # Dividir antigua raíz
            self.split_child_Tree_BPlus(new_root, 0)

            # Actualizar raíz
            self.root = new_root


    def insert_non_full(self, node, key, record):
        """
        Inserta una clave en un nodo que todavía
        tiene espacio disponible.

        Si durante el descenso un hijo está lleno,
        se divide antes de continuar.

        Args:
            node:
                Nodo actual.

            key:
                Clave a insertar.

            record:
                Registro asociado.
        """

        # Inserción en hoja
        if node.is_leaf:

            # Buscar posición ordenada
            i = 0

            while i < len(node.keys) and node.keys[i] < key:
                i += 1

            # Insertar clave y registro
            node.keys.insert(i, key)
            node.records.insert(i, record)

        
        # Inserción en nodo interno
        else:

            # Buscar hijo correcto
            i = len(node.keys) - 1

            while i >= 0 and key < node.keys[i]:
                i -= 1

            i += 1

            # Si el hijo está lleno,
            # dividir antes de bajar
            if len(node.children[i].keys) >= self.order:

                self.split_child_Tree_BPlus(node, i)

                # Determinar cuál de los dos hijos
                # resultantes debe recibir la clave
                if key > node.keys[i]:
                    i += 1

            # Continuar recursivamente
            self.insert_non_full(node.children[i], key, record)

    def split_child_Tree_BPlus(self, parent, index):
        """
        Divide un hijo lleno en dos nodos.

        Existen dos casos:
        - División de hoja
        - División de nodo interno

        Args:
            parent:
                Nodo padre del nodo a dividir.

            index:
                Posición del hijo dentro del padre.
        """

        full_child = parent.children[index]

        # División de nodo hoja
        if full_child.is_leaf:

            """
            En hojas:
            - la clave central NO desaparece
            - se copia al padre
            """

            mid = len(full_child.keys) // 2

            # Crear nueva hoja
            new_child = BPlusleafNode(self.order)

            # Mitad derecha
            new_child.keys = full_child.keys[mid:]
            new_child.records = full_child.records[mid:]

            # Mitad izquierda
            full_child.keys = full_child.keys[:mid]
            full_child.records = full_child.records[:mid]

            # Primera clave de la nueva hoja
            # sube al padre
            key_to_move = new_child.keys[0]

            parent.keys.insert(index, key_to_move)
            parent.children.insert(index + 1, new_child)

            # Actualizar lista enlazada de hojas
            new_child.next = full_child.next
            full_child.next = new_child


        # División de nodo interno
        else:

            """
            En nodos internos:
            - la clave central sube al padre
            - desaparece de los hijos
            """

            mid = len(full_child.keys) // 2

            # Clave que subirá al padre
            key_to_move = full_child.keys[mid]

            # Crear nuevo nodo interno
            new_child = BPlusNode(self.order)

            new_child.is_leaf = False

            # Mitad derecha
            new_child.keys = full_child.keys[mid + 1:]
            new_child.children = full_child.children[mid + 1:]

            # Mitad izquierda
            full_child.keys = full_child.keys[:mid]
            full_child.children = full_child.children[:mid + 1]

            # Insertar en padre
            parent.keys.insert(index, key_to_move)
            parent.children.insert(index + 1, new_child)

    def search(self, key):
        """
        Busca un registro asociado a una clave.

        Args:
            key:
                Clave a buscar.

        Returns:
            Registro asociado si existe.
            None en caso contrario.
        """

        return self._search(self.root, key)

    def _search(self, node, key):
        """
        Método recursivo de búsqueda.

        Args:
            node:
                Nodo actual.

            key:
                Clave buscada.

        Returns:
            Registro encontrado o None.
        """

        # Árbol vacío
        if node is None:
            return None

        # Buscar en hoja
        if node.is_leaf:
            # Búsqueda lineal
            for i, k in enumerate(node.keys):
                if k == key:
                    return node.records[i]
            return None

        
        # Buscar en nodo interno
        i = 0
        while i < len(node.keys) and key >= node.keys[i]:
            i += 1
        return self._search(node.children[i], key)
    

    def delete(self, key):
        """
        Elimina una clave del árbol.

        Después de eliminar:
        - se verifica déficit
        - se rebalancea si es necesario
        - se ajusta la raíz si queda vacía

        Args:
            key:
                Clave a eliminar.
        """

        # Árbol vacío
        if self.root is None:
            return

        # Eliminar recursivamente
        self._delete(self.root, key)

        # Si la raíz quedó vacía
        # y tiene hijos,
        # reducir altura del árbol
        if len(self.root.keys) == 0 and not self.root.is_leaf:

            self.root = self.root.children[0]

        # Si la raíz es hoja vacía,
        # el árbol queda vacío
        if len(self.root.keys) == 0 and self.root.is_leaf:

            self.root = None

    def _delete(self, node, key):
        """
        Método recursivo de eliminación.

        Args:
            node:
                Nodo actual.

            key:
                Clave a eliminar.
        """

        # Eliminación en hoja
        if node.is_leaf:

            if key in node.keys:
                index = node.keys.index(key)
                del node.keys[index]
                del node.records[index]
            return

        
        # Descender en nodo interno
        i = 0
        while i < len(node.keys) and key >= node.keys[i]:
            i += 1

        # Continuar eliminación
        self._delete(node.children[i], key)

        # Verificar déficit
        if (
            i < len(node.children)
            and len(node.children[i].keys) < self.order // 2
        ):
            self._rebalance(node, i)

    def _rebalance(self, parent, index):
        """
        Rebalancea un nodo con déficit.

        Estrategias:
        1. Pedir prestado al hermano izquierdo.
        2. Pedir prestado al hermano derecho.
        3. Fusionar nodos.

        Args:
            parent:
                Nodo padre.

            index:
                Posición del hijo con déficit.
        """

        min_keys = self.order // 2

        # Intentar préstamo del hermano izquierdo
        if (
            index > 0
            and len(parent.children[index - 1].keys) > min_keys
        ):

            left_sibling = parent.children[index - 1]
            current = parent.children[index]

            
            # Préstamo en hoja
            if current.is_leaf:

                current.keys.insert(0, left_sibling.keys[-1])
                current.records.insert(0, left_sibling.records[-1])

                del left_sibling.keys[-1]
                del left_sibling.records[-1]

                # Actualizar separador del padre
                parent.keys[index - 1] = current.keys[0]

            # Préstamo en nodo interno
            else:

                current.keys.insert(0, parent.keys[index - 1])

                current.children.insert(
                    0,
                    left_sibling.children.pop()
                )

                parent.keys[index - 1] = left_sibling.keys.pop()

        # Intentar préstamo del hermano derecho
        elif (
            index < len(parent.children) - 1
            and len(parent.children[index + 1].keys) > min_keys
        ):

            right_sibling = parent.children[index + 1]
            current = parent.children[index]

            # --------------------------
            # Préstamo en hoja
            # --------------------------
            if current.is_leaf:
                current.keys.append(right_sibling.keys[0])

                current.records.append(
                    right_sibling.records[0]
                )

                del right_sibling.keys[0]
                del right_sibling.records[0]

                # Actualizar separador
                parent.keys[index] = right_sibling.keys[0]
 
            # Préstamo en nodo interno
            else:

                current.keys.append(parent.keys[index])

                current.children.append(
                    right_sibling.children.pop(0)
                )

                parent.keys[index] = right_sibling.keys.pop(0)

        # Si no se puede prestar:
        # fusionar   
        else:

            if index < len(parent.children) - 1:
                self._merge(parent, index)

            else:
                self._merge(parent, index - 1)

    def _merge(self, parent, index):
        """
        Fusiona dos nodos hermanos.

        Args:
            parent:
                Nodo padre.

            index:
                Posición del hijo izquierdo.
        """

        left = parent.children[index]
        right = parent.children[index + 1]

        # Merge de hojas
        if left.is_leaf:

            # Mover claves y registros
            left.keys += right.keys
            left.records += right.records

            # Actualizar lista enlazada
            left.next = right.next

            # Eliminar separador del padre
            del parent.keys[index]

            # Eliminar hijo derecho
            del parent.children[index + 1]

        # Merge de nodos internos
        else:

            # Bajar separador del padre
            left.keys.append(parent.keys[index])

            # Transferir claves
            left.keys += right.keys

            # Transferir hijos
            left.children += right.children

            # Eliminar separador
            del parent.keys[index]

            # Eliminar hijo derecho
            del parent.children[index + 1]

    def update(self, key, new_record):
        """
        Actualiza el registro asociado a una clave.

        Args:
            key:
                Clave a actualizar.

            new_record:
                Nuevo valor asociado.

        Returns:
            True si la actualización fue exitosa.
            False si la clave no existe.
        """
        node = self.root
        while node is not None:
            # Buscar en hoja
            if node.is_leaf:
                for i, k in enumerate(node.keys):
                    if k == key:
                        node.records[i] = new_record
                        return True
                return False
            # Descender
            else:
                i = 0
                while i < len(node.keys) and key >= node.keys[i]:
                    i += 1
                node = node.children[i]
        return False
    def range_search(self, key_start, key_end):
        """
        Retorna todos los registros cuyas claves 
        estén dentro del rango [key_start, key_end].
        """
        results=[]
        node=self.root
        # Descender hasta la hoja que podría contener key_start
        if node is None:
            return results
        while not node.is_leaf:
            i=0
            while i<len(node.keys) and key_start>=node.keys[i]:
                i+=1
            node=node.children[i]
        # Recorrer hojas enlazadas hasta superar key_end
        while node is not None:
            for i, key in enumerate(node.keys):
                if key> key_end:
                    return results
                if key>=key_start:
                    results.append(node.records[i])
            node=node.next
        return results
    def search_greater(self, key):
     """Retorna todos los records con clave > key."""
     results = []
     node = self.root
     if node is None:
        # El árbol está vacío, retornar lista vacía
        return results
     while not node.is_leaf:
         # Descender por el hijo más a la izquierda
         node = node.children[0]
     while node is not None:
         for i, k in enumerate(node.keys):
            if k > key:
             # Si la clave es mayor, agregar el registro a resultados
             results.append(node.records[i])
         node = node.next
     return results # Retorna todos los registros con clave > key
    
    def search_less(self, key):
        """Retorna todos los records con clave < key."""
        results = []
        node = self.root
        # Descender hasta la hoja que podría contener key
        if node is None:
            return results
        while not node.is_leaf:
            # Descender por el hijo más a la izquierda
            node = node.children[0]
        while node is not None:
            for i, k in enumerate(node.keys):
                if k < key:
                    # Si la clave es menor, agregar el registro a resultados
                    results.append(node.records[i])
                else:
                    return results
            node = node.next
        return results # Retorna todos los registros con clave < key
    
    def get_all(self):
        """Retorna todos los registros del árbol."""
        results = []
        node = self.root
        # Descender hasta la hoja más a la izquierda
        if node is None:
            return results
        while not node.is_leaf:
            # Descender por el hijo más a la izquierda
            node = node.children[0]
        while node is not None:
            # Agregar todos los registros de la hoja actual
            results.extend(node.records)
            node = node.next
        return results # Retorna todos los registros del árbol
       


               

            



      
        
      

 
    
        
        