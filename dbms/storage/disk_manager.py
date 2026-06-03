import os

class DiskManager:
    PAGE_SIZE = 4096

    def __init__(self, filepath: str):
        self.filepath = filepath
        mode = 'r+b' if os.path.exists(filepath) else 'w+b'
        self.file = open(filepath, mode)

        self.num_pages = os.path.getsize(filepath) // self.PAGE_SIZE
        # read the directory and add the page # etc

    def write_page(self, page_id, data:bytes):
        self.file.seek(page_id * self.PAGE_SIZE)
        self.file.write(data)
        self.file.flush()

    def read_page(self, page_id: int) -> bytes:
        self.file.seek(page_id * self.PAGE_SIZE)
        raw = bytearray(self.file.read(self.PAGE_SIZE))
        print('raw[0:6]:', list(raw[0:6]))  # entire header
        return raw

    def allocate_page(self) -> int:
        page_id = self.num_pages
        self.num_pages += 1
        return page_id

    def close(self):
        self.file.close()
        
