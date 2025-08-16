import math
import re
import pymem


class Pointers:
    def __init__(self, pid):
        self.pm = pymem.Pymem()
        self.pm.open_process_from_id(pid)
        self.CLIENT = 0x00400000
        
        self.CHAR_NAME_POINTER = 0x011450EC
        self.QUEUE_POINTER = 0x011BDF1C
        self.LOGIN_ERROR_POINTER = 0x012CE35C
    
    def get_pointer(self, base_address, offsets):
        """
        Calcula o ponteiro final seguindo uma cadeia de offsets.
        """
        try:
            address = base_address
            for offset in offsets:  # Navega pelos offsets até o endereço final
                address = self.pm.read_int(address) + offset
            return address
        except Exception as e:
            #print(f"Erro ao calcular o ponteiro: {e}")
            return None
    
    def read_value(self, address, data_type="byte"):
        try:
            if data_type == "byte":
                return self.pm.read_bytes(address, 1)[0]  # Lê 1 byte
            elif data_type == "int":
                return self.pm.read_int(address)  # Lê 4 bytes como inteiro
            elif data_type == "float":
                return self.pm.read_float(address)  # Lê 4 bytes como float
            else:
                print(f"Tipo de dado desconhecido: {data_type}")
                return None
        except Exception as e:
            #print(f"Erro ao ler valor ({data_type}): {e}")
            return None
    
    def read_string_from_pointer(self, base_pointer, offset=0, max_length=50):
        try:
            pointer_address = self.pm.read_int(base_pointer)
            final_address = pointer_address + offset
            byte_data = self.pm.read_bytes(final_address, max_length)
            string_data = byte_data.split(b'\x00', 1)[0].decode('utf-8', errors='ignore')
            return string_data
        except Exception as e:
            print(f"String Error: {e}")
            return "Offline Account"
    
    def read_string_direct(self, address, max_length=50):
        """
        Lê uma string diretamente de um endereço (sem seguir ponteiro)
        """
        try:
            byte_data = self.pm.read_bytes(address, max_length)
            string_data = byte_data.split(b'\x00', 1)[0].decode('utf-8', errors='ignore')
            return string_data
        except Exception as e:
            print(f"String Error: {e}")
            return ""
    
    def get_char_name(self):
        name = self.read_string_from_pointer(self.CHAR_NAME_POINTER, offset=0xBC, max_length=50)
        
        if re.match(r"^[\w]+$", name):  # Alfanumérico
            return name
        
        # Segunda tentativa
        pointer = self.get_pointer(self.CLIENT + 0x00D450EC, offsets=[0xBC])
        if pointer:
            name = self.read_string_from_pointer(pointer, offset=0x0, max_length=50)
        return name
    
    def get_queue(self):
        q = self.read_string_direct(self.QUEUE_POINTER, max_length=50)
        return q

    def check_login(self):
        error = self.read_value(self.LOGIN_ERROR_POINTER, data_type="int")
        # print(f"Error: {error}")
        return error
