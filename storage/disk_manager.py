import os

PAGE_SIZE = 4096

class DiskManager:

    def __init__(self):
        pass

    def write_page(self, page_id: int, file_id: int, data:bytes):
        file, num_pages = self.open(file_id)

        file.seek(page_id * PAGE_SIZE)
        file.write(data)
        file.flush()

        file.close()

    def read_page(self, page_id: int, file_id: int) -> bytes:
        file, num_pages = self.open(file_id)

        file.seek(page_id * PAGE_SIZE)
        raw = bytearray(file.read(PAGE_SIZE))
        file.close()
        
        return raw if raw else bytearray(PAGE_SIZE)

    def allocate_page(self, file_id: int) -> int:
        file, num_pages = self.open(file_id)
        file.seek(num_pages * PAGE_SIZE)
        file.write(bytes(PAGE_SIZE))
        file.close()

        page_id = num_pages
        return page_id

    def open(self, file_id):
        filepath = f'data/{file_id}.db'
        mode = 'r+b' if os.path.exists(filepath) else 'w+b'
        file = open(filepath, mode)
        num_pages = os.path.getsize(filepath) // PAGE_SIZE
        return file, num_pages

    def close(self):
        pass