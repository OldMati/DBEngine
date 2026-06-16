from buffer.buffer_pool import BufferPoolManager
from index.b_tree_page import BTreePage
import struct
import os

class BPlusTree:
    # page 0: [root_page_id (4 bytes), num_keys (4 bytes)]
    # page 1+: root/leaf/inner node

    def __init__(self, bpm:BufferPoolManager, file_id: int, new_index = False):
        #self.bpm = BufferPoolManager(index_file)
        #new_index = not os.path.exists(index_file)
        self.bpm = bpm
        self.file_id = file_id

        #print('BPlusTre __init__ method is called')

        if new_index:
            #print('new index, creating root')
            # allocate page for the header
            bpm.allocate_page(self.file_id)
            # create root page
            self.root_page_id = 1
            self.num_keys = 0
            self._write_metadata()
            root_page = BTreePage(bpm.fetch_page(bpm.allocate_page(self.file_id), self.file_id), True, 1, True)
            root_page.serialize()
            self.bpm.unpin_page(self.root_page_id, self.file_id, True)
            assert root_page.page_id == 1
            assert root_page.is_leaf == True
        else:
            #print('file does exist in os, reading metadata')
            self._read_metadata()
            #print('root_id: ', self.root_page_id)
    

    def insert(self, key: int, rid: tuple[int, int]):
        # find the correct leaf node
        leaf_node, path = self._find_leaf(key)

        # insert the key into the node
        # find the index of the key in sorted order
  
        leaf_node.insert(key, rid)
        self.num_keys += 1

        # if key > 200:
        #     print(f'last key of the leaf node: {leaf_node.keys[-1]}, key: {key}')

        # check if node has enough space
        if not leaf_node.is_overflow():
            #if key % 50 == 0:
                #print('leaf node did not overflow at inserting key', key)
            #print('num_keys of page_1: ', leaf_node.num_keys)
            leaf_node.serialize()
            self.bpm.unpin_page(leaf_node.page_id, self.file_id, True)
            return
        
        # node does not have enough space -> split
        self._split_leaf(leaf_node, path)

    def _split_leaf(self, leaf_node: BTreePage, path: list[int]):
        # create new node
        new_page_id = self.bpm.allocate_page(self.file_id)
        new_node = BTreePage(self.bpm.fetch_page(new_page_id, self.file_id), True, new_page_id, True)
        #print('allocated new_page_id for new page: ', new_page_id, new_node.page_id)

        # calculate split_index
        split_index = leaf_node.num_keys // 2

        # copy half the keys into the new node
        new_node.keys = leaf_node.keys[split_index:]
        new_node.RIDs = leaf_node.RIDs[split_index:]

        # remove them from the original node
        del leaf_node.keys[split_index:]
        del leaf_node.RIDs[split_index:]

        new_node.num_keys = len(new_node.keys)
        leaf_node.num_keys = len(leaf_node.keys)

        # adjust the pointers
        new_node.next_leaf = leaf_node.next_leaf
        leaf_node.next_leaf = new_node.page_id
        new_node.prev_leaf = leaf_node.page_id

        # fix the pointers of the neighboring leafs
        next_leaf_page_id = new_node.next_leaf
        if next_leaf_page_id > 0:
            #print('detching next_leaf_page_id: ', next_leaf_page_id)
            next_leaf = BTreePage(self.bpm.fetch_page(next_leaf_page_id, self.file_id))
            next_leaf.prev_leaf = new_node.page_id
            next_leaf.serialize()
            self.bpm.unpin_page(next_leaf_page_id, self.file_id, True)
        

        #print('not fetching next_leaf_page_id: ', next_leaf_page_id)
        # write the nodes into the disc
        leaf_node.serialize()
        new_node.serialize()

        #print('now unpinning the new leaf node, page_id: ', new_node.page_id)
        self.bpm.unpin_page(leaf_node.page_id, self.file_id, True)
        self.bpm.unpin_page(new_node.page_id, self.file_id, True)

        # update the parent node
        index_of_parent = len(path) - 2

        if index_of_parent >= 0:
            self._update_parent(path, index_of_parent, new_node)
        else:
            self._split_root(leaf_node, new_node, new_node.keys[0])
        
    def _update_parent(self, path: list[int], idx: int, new_node: BTreePage, separator: int | None = None):
        node_page_id = path[idx]
        node = BTreePage(self.bpm.fetch_page(node_page_id, self.file_id))
        
        # insert new key into the node
        min_key = separator if separator else new_node.keys[0]
        pointer = new_node.page_id

        node.insert_pointer(min_key, pointer)

        # check if node has enough space
        if not node.is_overflow():
            node.serialize()
            self.bpm.unpin_page(node.page_id, self.file_id, True)
            return
        
        # node does not have enough space -> split
        self._split_internal(node, path, idx)

    def _split_internal(self, node: BTreePage, path: list[int], idx: int):
        # create new node
        new_page_id = self.bpm.allocate_page(self.file_id)
        new_node = BTreePage(raw=self.bpm.fetch_page(new_page_id, self.file_id), new_page=True, page_id=new_page_id, is_leaf=False)

        # update num_keys
        split_index = node.num_keys // 2

        # copy half the keys into the new node
        new_node.keys = node.keys[split_index + 1:]
        new_node.pointers = node.pointers[split_index + 1:]

        # store the split key
        split_key = node.keys[split_index]

        # remove elements from the original node
        del node.keys[split_index:]
        del node.pointers[split_index + 1:]
        
        node.num_keys = len(node.keys)
        new_node.num_keys = len(new_node.keys)

        # write the nodes into the disc
        node.serialize()
        new_node.serialize()
        self.bpm.unpin_page(node.page_id, self.file_id, True)
        self.bpm.unpin_page(new_node.page_id, self.file_id, True)

        # update the parent node
        if idx == 0:
            # create new root
            self._split_root(node, new_node, split_key)
        else:
        # else update parent
            self._update_parent(path, idx - 1, new_node, split_key)

    def _split_root(self, node: BTreePage, new_node: BTreePage, separator: int):
        self.root_page_id = page_id = self.bpm.allocate_page(self.file_id)

        root_node = BTreePage(self.bpm.fetch_page(page_id, self.file_id), True, page_id, False)
        root_node.pointers.append(node.page_id)
        root_node.insert_pointer(separator, new_node.page_id)
        root_node.serialize()

        self.bpm.unpin_page(page_id, self.file_id, True)
        print('THE ROOT AFTER FIRST SPLIT:')
        print(f'keys: {root_node.keys}' )
        print(f'pointers: {root_node.pointers}' )
        print(f'id: {root_node.page_id}' )

        self._write_metadata()


    def _find_leaf(self, key) -> tuple[BTreePage, list]:
        # fetch the root page
        #print(f'root_page_id: ', self.root_page_id)
        root_page = BTreePage(self.bpm.fetch_page(self.root_page_id, self.file_id))
        path = [self.root_page_id]

        node = root_page

        # while node is an inner node
        while not node.is_leaf:
            #print('Linear search of keys in page ', node.page_id)
            #print('keys: ', node.keys)
            # linear search until key >= keys[i]
            page_id = node.pointers[0]
            for i in range(node.num_keys - 1, -1, -1):
                if key > node.keys[i]:
                    #print('Chosen node key: ', node.keys[i])
                    page_id = node.pointers[i + 1]
                    break

            self.bpm.unpin_page(node.page_id, self.file_id)
            node = BTreePage(self.bpm.fetch_page(page_id, self.file_id))
            path.append(node.page_id)
        # print('Correct leafnode: ', node.page_id, 'path: ', path)
        # min_key = node.keys[0] if node.keys else -1000
        # max_key = node.keys[-1] if node.keys else 99999999
        #print(f'Saerching for key={key}, leaf found: {node.page_id}, num_keys: {node.num_keys}, min_key: {min_key}, max_key: {max_key}')
        #if node.keys:
            #print(node.keys)
        return node, path

    def search(self, key) -> list[tuple[int, int]]:
        # find the leftmost correct leaf
        leaf_node, _ = self._find_leaf(key)
        rids = []

        while True:
            # search the leaf
            rids.extend(leaf_node.lookup(key))
            passed = bool(leaf_node.keys) and leaf_node.keys[-1] > key
            next_id = leaf_node.next_leaf
            self.bpm.unpin_page(leaf_node.page_id, self.file_id)
            if passed or next_id is None or next_id <= 0:
                break
            leaf_node = BTreePage(self.bpm.fetch_page(next_id, self.file_id))
            
        return rids


    def range_scan(self, start_key, end_key) -> list:
        pass

    def delete(self, kay):
        pass

    def _read_metadata(self):
        raw = self.bpm.fetch_page(0, self.file_id)
        self.root_page_id = struct.unpack_from('I', raw, 0)[0]
        self.num_keys = struct.unpack_from('I', raw, 4)[0]
        self.bpm.unpin_page(0, self.file_id)
    
    def _write_metadata(self):
        raw = self.bpm.fetch_page(0, self.file_id)
        struct.pack_into('I', raw, 0, self.root_page_id)
        struct.pack_into('I', raw, 4, self.num_keys)
        self.bpm.unpin_page(0, self.file_id, True)