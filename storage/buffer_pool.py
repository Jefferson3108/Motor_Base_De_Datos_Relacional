from storage import page
from storage.disk_persistence import DiskPersistence
from storage.page import Page, PAGE_SIZE
import json
class BufferPool:
    def __init__(self, db_patch: str,max_pages: int = 100):
        self.disk = DiskPersistence(db_patch)
        self.max_pages = max_pages
        self.pages = {}
    
    def fetch_page(self, page_id: int) -> page.Page:
        if page_id not in self.pages:
            data = self.disk.read_page(page_id)
            self.pages[page_id] = page.Page.deserialize(page_id, data)
        return self.pages[page_id]
    
    def new_page(self) -> page.Page:
        page_id = self.disk.total_pages()
        new_page = page.Page(page_id)
        page.is_dirty = True
        self.pages[page_id] = new_page
        return new_page
    
    def get_page_with_space(self, record: list) -> page.Page:
        total_pages = self.disk.total_pages()
        for page_id in range(total_pages):
            page = self.fetch_page(page_id)
            test_page = page.records+[record]
            if len(json.dumps(test_page).encode('utf-8')) <= PAGE_SIZE*0.9:
                return page
        
        total_pages = self.disk.total_pages()
        for page_id in range(total_pages):
            if page_id not in self.pages:
                page = self.fetch_page(page_id)
                test=page.records+[record]
                if len(json.dumps(test).encode('utf-8')) <= page.PAGE_SIZE*0.9:
                    return page

            
            
        return self.new_page()
    
    def flush_page(self, page_id: int) -> None:
        for page_id, page in self.pages.items():
            if page.is_dirty:
                self.disk.write_page(page_id, page.serialize())
                page.is_dirty = False
            


       