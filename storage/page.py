import json
from operator import index
PAGE_SIZE = 4096
class Page:
    def __init__(self, page_id:int):
        self.page_id = page_id
        self.records = []
        self.is_dirty = False
    
    def add_record(self, record: list)-> bool:
        self.records.append(record)
        if len(self.serialize()) > PAGE_SIZE:
            self.records.pop()
            return False
        self.is_dirty = True
        return True
    
    def delete_record(self, record: list)-> None:
        del self.record[index]
        self.is_dirty = True
    
    def serialize(self)-> bytes:
        data = json.dumps(self.records).encode('utf-8')
        if len(data) > PAGE_SIZE:
            raise OverflowError(f"Los datos serializados exceden el tamaño de página de {PAGE_SIZE} bytes.")
        return data.ljust(PAGE_SIZE, b'\x00')
    
    @staticmethod
    def deserialize(page_id: int, data: bytes):
        page = Page(page_id)
        text = data.rstrip(b'\x00').decode('utf-8')
        page.records = json.loads(text) if text else []
        return page

        

        
        

        
                