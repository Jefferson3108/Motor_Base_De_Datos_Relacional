import json
from operator import index
PAGE_SIZE = 4096
class Page:
    """
    Representa una página física de almacenamiento.

    Una página contiene múltiples registros y es la unidad mínima
    de lectura/escritura en disco.

    Conceptualmente:
        Disco → dividido en páginas
        Página → contiene registros

    Attributes
    ----------
    page_id : int
        Identificador único de la página.

    records : list
        Lista de registros almacenados en la página.

    is_dirty : bool
        Indica si la página fue modificada en memoria y todavía
        no ha sido persistida en disco.
    """
    def __init__(self, page_id:int):
        # El ID de la página se asigna al crearla, pero el contenido
        self.page_id = page_id
        #Registros almacenados en la página. Cada registro es una lista de valores.
        self.records = []
        # Indica si la página ha sido modificada en memoria y no se ha guardado en disco.
        self.is_dirty = False

    # Agregar un nuevo registro a la página
    def add_record(self, record: list)-> bool:
        """
        Inserta un registro en la página.

        Antes de confirmar la inserción se verifica que
        el tamaño serializado de la página no exceda PAGE_SIZE.

        Si la página se desborda:
            → se revierte la inserción
            → retorna False

        Parameters
        ----------
        record : list
            Registro a insertar.

        Returns
        -------
        bool
            True  → inserción exitosa
            False → overflow de página
        """
        self.records.append(record)
        if len(self.serialize()) > PAGE_SIZE:
            self.records.pop()
            return False
        self.is_dirty = True
        return True
    
    # Eliminar un registro específico de la página
    def delete_record(self, record: list)-> None:
        """
        Elimina un registro de la página por índice.

        Parameters
        ----------
        index : int
            Posición del registro dentro de la página.
        """
        del self.record[index]
        self.is_dirty = True
    
    def serialize(self)-> bytes:
        """
        Convierte la página a bytes para persistencia en disco.

        Flujo:
          records → JSON → bytes UTF-8

        El resultado final se rellena con bytes nulos (\x00)
        hasta alcanzar exactamente PAGE_SIZE bytes.

        Returns
        -------
        bytes
            Página serializada lista para escribirse en disco.

        Raises
        ------
        OverflowError
            Si el contenido excede PAGE_SIZE.
        """
        # Convertir registros a JSON binario
        data = json.dumps(self.records).encode('utf-8')
        if len(data) > PAGE_SIZE:
            raise OverflowError(f"Los datos serializados exceden el tamaño de página de {PAGE_SIZE} bytes.")
        return data.ljust(PAGE_SIZE, b'\x00')
    
    @staticmethod
    # Convertir bytes leídos desde disco de vuelta a una instancia de Page
    def deserialize(page_id: int, data: bytes):
        """
        Reconstruye una página desde bytes leídos del disco.

        Flujo:
          bytes → texto UTF-8 → JSON → records

        Parameters
        ----------
        page_id : int
            ID de la página.

        data : bytes
            Contenido binario leído desde disco.

        Returns
        -------
        Page
            Página reconstruida en memoria.
        """
        page = Page(page_id)
        text = data.rstrip(b'\x00').decode('utf-8')
        page.records = json.loads(text) if text else []
        return page

        

        
        

        
                