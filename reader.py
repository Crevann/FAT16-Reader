import struct
import sys
from dataclasses import dataclass

class FilesystemReader:
    def __init__(self, src_filename):
        self.sector_size = 0
        self.reserved_sectors = 0

        with open(src_filename, 'rb') as file:
            self.binary = file.read()
        if self.binary[0x36:0x3B] != b'FAT16':
            raise Exception("Invalid format")

        self.sector_size = struct.unpack('<H', self.binary[0x0B:0x0D])[0]
        self.reserved_sectors = struct.unpack('<H', self.binary[0x0E:0x10])[0]

        self.fat_position = self.sector_size * self.reserved_sectors
        self.fat_size = struct.unpack('<H', self.binary[0x16:0x18])[0]
        self.fat_number = self.binary[0x10]
        
        self.root_position = self.fat_position + (self.fat_size * self.fat_number * self.sector_size)
        self.root_entries = struct.unpack('<H', self.binary[0x11:0x13])[0]
        self.dir_entry_size = 32

        self.dir_sector_number = self.binary[0x0D]
        #Read files here
        self.current_position = self.root_position #Each time increment by 32
        self.clusters_start = self.root_position + (self.root_entries * self.dir_entry_size)
        self.read_directory(self.current_position, 0)
        
    def read_directory(self, directory_position, depth):
        counter = 0
        while counter <= self.root_entries:
            if(self.binary[directory_position + counter]) == 0x00:
                return
            current_file = self.get_32byte_file_bytes(directory_position + counter)
            if current_file.attributes == 0x08:
                print("DISK NAME: ", end='')
            print("\t" * depth, end='')    
            print(current_file.name.decode().strip(), end='')
            if current_file.extension != b'   ':
                print("." + current_file.extension.decode())
            else:
                print("")
            if current_file.name != b'.       ' and current_file.name != b'..      ':
                if current_file.attributes == 0x10:
                    new_directory_location = self.clusters_start + (self.dir_sector_number * self.sector_size * (current_file.low_first_cluster - 2))
                    self.read_directory(new_directory_location, depth + 1)
            counter = counter + self.dir_entry_size

    def get_32byte_file_bytes(self, position):
        file = FileData(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        file.name = self.binary[position:(position + 8)]
        file.extension = self.binary[(position + 8):(position + 11)]
        file.attributes = self.binary[(position + 11)]
        file.creation_time_seconds = self.binary[(position + 13)]
        file.creation_time = struct.unpack('<H', self.binary[(position + 14):(position + 16)])[0]
        file.creation_date = struct.unpack('<H', self.binary[(position + 16):(position + 18)])[0]
        file.last_access_date = struct.unpack('<H', self.binary[(position + 18):(position + 20)])[0]
        file.high_first_cluster = struct.unpack('<H', self.binary[(position + 20):(position + 22)])[0]
        file.last_modification_time = struct.unpack('<H', self.binary[(position + 22):(position + 24)])[0]
        file.last_modification_date = struct.unpack('<H', self.binary[(position + 24):(position + 26)])[0]
        file.low_first_cluster = struct.unpack('<H', self.binary[(position + 26):(position + 28)])[0]
        file.size = struct.unpack('<I', self.binary[(position + 28):(position + 32)])[0]
        return file

@dataclass
class FileData:
    name: bytes
    extension: bytes
    attributes: bytes
    creation_time_seconds: bytes
    creation_time: bytes
    creation_date: bytes
    last_access_date: bytes
    high_first_cluster: bytes
    last_modification_time: bytes
    last_modification_date: bytes
    low_first_cluster: bytes
    size: bytes

if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise Exception("I need the path of the file to inspect")
    FilesystemReader(sys.argv[1])

