import os

PAGE_SIZE = 4096

class DiskManager:

    def __init__(self, filepath: str):
        self.filepath = filepath
        mode = 'r+b' if os.path.exists(filepath) else 'w+b'
        self.file = open(filepath, mode)

        self.num_pages = os.path.getsize(filepath) // PAGE_SIZE
        # read the directory and add the page # etc

    def write_page(self, page_id, data:bytes):
        #print('writing page, data: ', data[:20])
        self.file.seek(page_id * PAGE_SIZE)
        self.file.write(data)
        self.file.flush()

    def read_page(self, page_id: int) -> bytes:
        self.file.seek(page_id * PAGE_SIZE)
        raw = bytearray(self.file.read(PAGE_SIZE))
        return raw if raw else bytearray(PAGE_SIZE)

    def allocate_page(self) -> int:
        #print('disk manager, num_pages: ', self.num_pages)
        page_id = self.num_pages
        self.num_pages += 1
        return page_id

    def close(self):
        self.file.close()