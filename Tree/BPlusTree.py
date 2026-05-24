class BPlusNode:
    def __init__(self, order, leaf=False):
        self.order = order
        self.is_leaf = leaf
        self.keys = []
        self.children = []
        self.next = None


class BPlusleafNode(BPlusNode):
    def __init__(self,order):
        super().__init__(order=order, leaf=True)
        self.records = []
          


class BPlusTree:
    def __init__(self, order):
        self.root = None
        self.order = order

    def insert(self, key, record):
        if self.root is None:
            self.root = BPlusleafNode(self.order)
            self.root.keys.append(key)
            self.root.records.append(record)
            return 
        self.insert_non_full(self.root, key, record)

        if len(self.root.keys) >= self.order: 
            new_root = BPlusNode(self.order)
            new_root.children.append(self.root)
            self.split_child_Tree_BPlus(new_root, 0)
            self.root = new_root
            
        
    

    def insert_non_full(self, node, key, record):
        if node.is_leaf:
            i=0
            while i < len(node.keys)  and node.keys[i] < key:
                i += 1
            node.keys.insert(i, key)
            node.records.insert(i, record)
        else:
            i = len(node.keys) - 1
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            if len(node.children[i].keys) >= self.order: 
                self.split_child_Tree_BPlus(node, i)
                if key > node.keys[i]:
                    i += 1
            self.insert_non_full(node.children[i], key, record)

    def split_child_Tree_BPlus(self, parent, index):
        full_child = parent.children[index]
        if full_child.is_leaf:
            mid = len(full_child.keys) // 2
            new_child = BPlusleafNode(self.order)
            new_child.keys = full_child.keys[mid:]
            new_child.records = full_child.records[mid:]
            full_child.keys = full_child.keys[:mid]
            full_child.records = full_child.records[:mid]
            key_to_move = new_child.keys[0]
            parent.keys.insert(index, key_to_move)
            parent.children.insert(index + 1, new_child)
            new_child.next = full_child.next
            full_child.next = new_child
            return None

        else:
            mid = len(full_child.keys) // 2
            key_to_move = full_child.keys[mid]
            new_child = BPlusNode(self.order)
            new_child.is_leaf = False
            new_child.keys = full_child.keys[mid + 1:]
            full_child.keys = full_child.keys[:mid]
            new_child.children = full_child.children[mid + 1:]
            full_child.children = full_child.children[:mid + 1]
            parent.keys.insert(index, key_to_move)
            parent.children.insert(index + 1, new_child)
            return None
    
    def search(self, key):
        return self._search(self.root, key)

    def _search(self, node, key):

        if node is  None:
            return None
        if node.is_leaf:
            for i, k in enumerate(node.keys):
                if k == key:
                 return node.records[i]
            return None
        else:
                i = 0
                while i < len(node.keys) and key >= node.keys[i]:
                    i += 1
                return self._search(node.children[i], key)
tree= BPlusTree(order=3)
for i in [10, 20, 5, 6, 12, 30, 25]:
    tree.insert(i, f"Record {i}")

print(tree.search(10))  # Output: Record 10
print(tree.search(5))   # Output: Record 5
print(tree.search(15))  # Output: None
print(tree.search(30)) 
print(tree.search(1)) # Output: Record 30
               

            



      
        
      

 
    
        
        