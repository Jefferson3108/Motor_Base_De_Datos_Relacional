from storage import page
from storage.disk_persistence import DiskPersistence
from storage.page import Page, PAGE_SIZE
import json
class BufferPool:
    """
    Buffer Pool Manager.

    Se encarga de administrar las páginas en memoria RAM y coordinar
    la persistencia hacia disco.

    Funciones principales:
      - Cargar páginas desde disco bajo demanda
      - Mantener páginas cacheadas en memoria
      - Crear nuevas páginas
      - Buscar páginas con espacio disponible
      - Escribir páginas modificadas (dirty pages) a disco

    Conceptualmente actúa como una capa intermedia entre:
        Motor SQL ↔ BufferPool ↔ Disco

    Parameters
    ----------
    db_patch : str
        Ruta del archivo físico .db donde se almacenan las páginas.
    max_pages : int
        Máximo número de páginas permitidas en memoria.
        (todavía no se implementa reemplazo de páginas)
    """
    def __init__(self, db_patch: str,max_pages: int = 100):
        # Encargado de operaciones físicas sobre disco
        self.disk = DiskPersistence(db_patch)
        # Límite máximo de páginas en memoria
        self.max_pages = max_pages
        # Diccionario: page_id (int) → Page
        self.pages = {}

    #Cargar página desde disco o devolverla desde el pool si ya está cargada
    def fetch_page(self, page_id: int) -> page.Page:
        """
        Obtiene una página desde el buffer pool.

        Si la página ya está en memoria:
            → retorna la versión cacheada.

        Si NO está en memoria:
            → la carga desde disco
            → la deserializa
            → la almacena en el buffer pool.

        Parameters
        ----------
        page_id : int
            Identificador único de la página.

        Returns
        -------
        Page
            Objeto Page cargado en memoria.
        """
        if page_id not in self.pages:
            data = self.disk.read_page(page_id)
            self.pages[page_id] = page.Page.deserialize(page_id, data)
        return self.pages[page_id]
    
    # Crear una nueva página
    def new_page(self) -> page.Page:
        """
        Crea una nueva página vacía.

        El ID de la página corresponde al número total actual
        de páginas en disco.

        La página nueva se marca como dirty porque todavía
        no ha sido persistida.

        Returns
        -------
        Page
            Nueva página vacía lista para usarse.
        """
        # El siguiente ID disponible
        page_id = self.disk.total_pages()
        new_page = page.Page(page_id)
        page.is_dirty = True
        self.pages[page_id] = new_page
        return new_page
    
    # Buscar una página con espacio disponible para un nuevo registro
    def get_page_with_space(self, record: list) -> page.Page:
        """
        Busca una página con espacio suficiente para insertar
        un nuevo registro.

        Estrategia:
          1. Revisar páginas ya cargadas desde disco
          2. Revisar páginas existentes no cacheadas
          3. Si ninguna tiene espacio → crear nueva página

        El cálculo del espacio se hace serializando temporalmente
        el contenido y verificando que no exceda ~90% del tamaño
        máximo permitido.

        Parameters
        ----------
        record : list
            Registro que se desea insertar.

        Returns
        -------
        Page
            Página con espacio disponible.
        """
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
    
    # Escribir páginas modificadas a disco
    def flush_page(self, page_id: int) -> None:
        """
        Persiste en disco todas las páginas dirty
        actualmente cargadas en memoria.

        Una página dirty es una página modificada
        que aún no ha sido guardada físicamente.

        Después del flush:
            is_dirty = False

        Notes
        -----
        Actualmente el parámetro page_id no se usa realmente,
        porque el método recorre TODAS las páginas dirty.
        """
        for page_id, page in self.pages.items():
            if page.is_dirty:
                self.disk.write_page(page_id, page.serialize())
                page.is_dirty = False
            


       