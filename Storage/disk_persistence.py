import os

PAGE_SIZE = 4096  # Tamaño fijo de cada página en bytes (4 KB)


class DiskPersistence:
    """
    Gestor de persistencia en disco para un archivo de tabla.

    Es la única capa del motor que interactúa directamente con el
    sistema de archivos. Todas las demás capas (BufferPool, Page)
    pasan por aquí para leer o escribir datos físicos.

    El archivo se organiza como una secuencia continua de páginas
    de tamaño fijo (PAGE_SIZE bytes). Para acceder a la página N
    se salta N * PAGE_SIZE bytes desde el inicio del archivo.
    """

    def __init__(self, filename: str):
        """
        Inicializa el gestor y crea el archivo si no existe.

        Parameters
        ----------
        filename : str
            Ruta al archivo .db de la tabla. Ejemplo: "data/usuarios.db"
        """
        self.filename = filename
        if not os.path.exists(filename):
            open(filename, 'wb').close()

    def write_page(self, page_num: int, data: bytes) -> None:
        """
        Escribe exactamente PAGE_SIZE bytes en la posición de la página indicada.

        Parameters
        ----------
        page_num : int
            Número de página destino (0-indexed).
        data : bytes
            Exactamente PAGE_SIZE bytes a escribir.

        Raises
        ------
        AssertionError
            Si data no tiene exactamente PAGE_SIZE bytes.
        """
        assert len(data) == PAGE_SIZE, \
            f"La página debe tener exactamente {PAGE_SIZE} bytes, recibió {len(data)}"
        with open(self.filename, 'r+b') as f:
            f.seek(page_num * PAGE_SIZE)
            f.write(data)

    def read_page(self, page_num: int) -> bytes:
        """
        Lee exactamente PAGE_SIZE bytes desde la posición de la página indicada.
        Si la página no existe aún, retorna PAGE_SIZE bytes de ceros.

        Parameters
        ----------
        page_num : int
            Número de página a leer (0-indexed).

        Returns
        -------
        bytes
            Exactamente PAGE_SIZE bytes. Rellena con ceros si el archivo
            es más corto de lo esperado.
        """
        with open(self.filename, 'rb') as f:
            f.seek(page_num * PAGE_SIZE)
            data = f.read(PAGE_SIZE)
            if len(data) < PAGE_SIZE:
                data += bytes(PAGE_SIZE - len(data))
            return data

    def total_pages(self) -> int:
        """
        Retorna el número total de páginas que contiene el archivo.

        Returns
        -------
        int
            Número de páginas completas en el archivo.
            Retorna 0 si el archivo está vacío.
        """
        return os.path.getsize(self.filename) // PAGE_SIZE
    
     

      
