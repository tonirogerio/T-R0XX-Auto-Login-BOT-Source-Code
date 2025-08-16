import os
import cv2
import numpy as np
import win32gui
import win32ui
import win32con
import ctypes


class ImageFinder:
    def __init__(self, hwnd):
        self.hwnd = hwnd

    def get_title_bar_height(self):
        """
        Obtém a altura da barra de título da janela.
        """
        SM_CYCAPTION = 4
        return ctypes.windll.user32.GetSystemMetrics(SM_CYCAPTION)

    def capture_window(self):
        """
        Captura a imagem da janela definida pelo hwnd.
        """
        try:
            rect = win32gui.GetWindowRect(self.hwnd)
            width, height = rect[2] - rect[0], rect[3] - rect[1]

            hwnd_dc = win32gui.GetWindowDC(self.hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)

            save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)

            bmp_info = save_bitmap.GetInfo()
            bmp_str = save_bitmap.GetBitmapBits(True)
            img = np.frombuffer(bmp_str, dtype=np.uint8)
            img.shape = (bmp_info['bmHeight'], bmp_info['bmWidth'], 4)

            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, hwnd_dc)
            win32gui.DeleteObject(save_bitmap.GetHandle())

            return img[..., :3]

        except Exception as e:
            print(f"Erro ao capturar a janela: {e}")
            return None

    def find_image(self):
        """
        Procura pela imagem cancel.bmp dentro da janela hwnd.
        Retorna 1 se encontrada, senão 0.
        """
        base_dir = os.path.dirname(__file__)
        image_path = os.path.join(base_dir, "img", "cancel.bmp")
        template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        if template is None:
            print("Imagem foi encontrada ou está corrompida.")
            return 0

        window_img = self.capture_window()
        if window_img is None:
            return 0

        window_gray = cv2.cvtColor(window_img, cv2.COLOR_BGR2GRAY)
        result = cv2.matchTemplate(window_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)

        return 1 if max_val > 0.9 else 0


"""# como usar
hwnd = 853300
finder = ImageFinder(hwnd)
found = finder.find_image()

if found:
    print("Imagem encontrada.")
else:
    print("Imagem não encontrada.")"""

