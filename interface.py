import os
import cv2
import time
import numpy as np
import customtkinter
import tkinter
import tkinter.messagebox
from tkinter import filedialog
from PIL import Image, ImageTk
import traceback
import logging
import operator
import glob
from remote_control import RemoteControl

#DETECTION ENGINE (YOLO)
from TYRE_detect import TYREDetect
from DOT_detect import DOTDetect
from DOT_crop import DOTCrop
from DOT_ocr_detect import DOTOCRDetect
from SKU_read import SKURead
from SKU_save import SKUSave

# TEMPLATE MATCH (sklearn)
#from DOT_charmatch import DOTCharMatch

# RECOGNITION ENGINE (Paddle)
#from DOT_ocr import DOTOCR

from verify import verify
import utils
import threading
import multiprocessing

customtkinter.set_appearance_mode("Light")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

import winsound
#from playsound import playsound
        
TireFound = multiprocessing.Value('b', False)  # 'b' indicates a boolean
LOCK_OCR_SCANNER = multiprocessing.Value('b', False) 

### REMOTE CONTROL MM ###
RC_LOCK_FOCUS = multiprocessing.Value('b', True)
SKU_Recognized =  multiprocessing.Value('b', False)
RC_CameraReady = multiprocessing.Value('b', False)
RC_DotRectMidX = multiprocessing.Value('i', -9999) 
RC_DotRectMidY = multiprocessing.Value('i', -9999) 
oldRC_DotRectMidX = multiprocessing.Value('i', -10000) 
oldRC_DotRectMidY = multiprocessing.Value('i', -10000)
######################

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize Parameters
        self.resized_image = None
        
        # === AMBIENT MODE ===
        # 0 = "Production: Capture Sony imgs and process"
        # 1 = "Development: Get each Image after button press" [Debug]
        # ====================
        self.ProgramMode = 0
        self.DisableCamera = 0 # 0 = "Sony Remote is required" | 1 = "Program will run anyway"


        ### REMOTE CONTROL ###
        self.SquareThreshold = 0 #Must focus if the dif between old_rect and rect is > (THIS value)
        ######################


        ### OCR VAR-LOGIC ###
        self.DisablePhotoAfterVerify = True # True = Will NOT keep taking photos after Verify SKU
        
        #Especial vars#
        self.ClearResultAfterXframes = 3
        self.CachedFramecount = 0 #Resets to 0 when needed.        
        
        self.ocr_result = {
            'DOT': [], 'LOCAL': [], 'CHAR': [], 'SKU': [], 'DATA': [],
        }
        
        self.OCR_MaxConfirms = 1 # MAX num. of confirmations 
        self.CachedConfirmedSKUs = {} # key: SKU | value: CONFIRMED_AMOUNT
        ### END OF OCR ###
        
        # MISC
        self.text_dot_found = tkinter.StringVar(value="")
        self.text_dot_infos = tkinter.StringVar(value="") # SKU infos from table
        self.text_sku = tkinter.StringVar(value="SKU:")
        self.video_path = ""
        self.jpg_files = []
        self.IsVideoPaused = True
        
        #configure Texts
        ProgramEnvMode = "Developer" if self.ProgramMode else "Production"
        IsGUIDeveloper = "disabled" if self.ProgramMode else "enabled"
        
        # configure window
        self.title("CEVA 🤝 FEI")
        self.geometry(f"{1200}x{600}")

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3, 4, 5), weight=1)
        self.grid_rowconfigure((0, 1, 2, 4, 5), weight=1)

        # load interface IMAGES
        image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "InterfaceFigures")
        self.open_folder_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "open_folder_light.png")), size=(26, 26))
        self.play_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "play_light.png")), size=(26, 26))
        self.pause_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "pause_light.png")), size=(26, 26))
        self.webcam_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "webcam_light.png")), size=(26, 26))
        self.ocr_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "ocr_light.png")), size=(26, 26))
        self.export_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "export_light.png")), size=(26, 26))
        self.send_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "message_light.png")), size=(26, 26))
        #self.ceva_logo = Image.open(os.path.join(image_path, "ceva_icon.png"))
        #self.ceva_logo = ImageTk.PhotoImage(self.ceva_logo)
        
        #self.iconphoto(False, self.ceva_logo)

        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=6, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="CEVA - {0}".format(ProgramEnvMode), font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.play_video_button = customtkinter.CTkButton(self.sidebar_frame, command=lambda: self.update_video_button(Execute=True), text="EXECUTAR", state=IsGUIDeveloper, image=self.play_image, compound="bottom")
        self.play_video_button.grid(row=2, column=0, padx=20, pady=10)

        if (self.ProgramMode == 1):
            self.play_next_image = customtkinter.CTkButton(self.sidebar_frame, command=None, text="DEV. WAIT...", state="disabled", image=self.pause_image, compound="bottom")
            self.play_next_image.grid(row=3, column=0, padx=20, pady=20)
            
        #self.run_ocr_button = customtkinter.CTkButton(self.sidebar_frame, command=lambda: self.run_ocr_event(final=True), text="OCR", image=self.ocr_image, compound="bottom")
        #self.run_ocr_button.grid(row=4, column=0, padx=20, pady=20)
        
        self.export_button = customtkinter.CTkButton(self.sidebar_frame, command=self.export_skus, text="EXPORTAR", image=self.export_image, compound="bottom")
        self.export_button.grid(row=4, column=0, padx=20, pady=20)

        # Image/Webcam canvas
        self.video_frame = customtkinter.CTkFrame(self)
        self.video_frame.grid(row=0, column=1, rowspan=3, columnspan=5, padx=(20, 20), pady=(20, 0), sticky="nsew")
        self.video_frame.grid_columnconfigure(0, weight=1)
        self.video_frame.grid_rowconfigure(0,weight=1)
        self.canvas = customtkinter.CTkCanvas(self.video_frame, bg="#dbdbdb", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Crop canvas (DOT-SKU-DATA-LOCAL....)
        #self.crop_frame = customtkinter.CTkFrame(self)
        #self.crop_frame.grid(row=0, column=6, rowspan=1, columnspan=1, padx=(20, 20), pady=(20, 0), sticky="nsew")
        #self.label_zoom = customtkinter.CTkLabel(master=self.crop_frame, text="DOT-SKU", font=('Arial', 20))
        #self.label_zoom.grid(row=0, column=0, pady=(20, 20))

        self.canvas_crop_width, self.canvas_crop_height = 200, 120
        #self.canvas_crop = customtkinter.CTkCanvas(self.crop_frame, height=self.canvas_crop_height, width=self.canvas_crop_width, bg="#dbdbdb", highlightthickness=0)
        #self.canvas_crop.grid(row=1, column=0, sticky="nsew")
        
        # SKU canvas (SKU)
        self.sku_frame = customtkinter.CTkFrame(self)
        self.sku_frame.grid(row=1, column=6, rowspan=1, columnspan=1, padx=(20, 20), pady=(20, 0), sticky="nsew")
        self.label_zoom_sku = customtkinter.CTkLabel(master=self.sku_frame, text="SKU", font=('Arial', 20))
        self.label_zoom_sku.grid(row=0, column=0, pady=(20, 20))

        self.canvas_sku_width, self.canvas_sku_height = 200, 100
        self.canvas_sku = customtkinter.CTkCanvas(self.sku_frame, height=self.canvas_sku_height, width=self.canvas_sku_width, bg="#dbdbdb", highlightthickness=0)
        self.canvas_sku.grid(row=1, column=0, sticky="nsew")

        # DOT-SKU canvas
        self.dot_frame = customtkinter.CTkFrame(self)
        self.dot_frame.grid(row=4, column=1, columnspan=6, padx=(20, 20), pady=(20, 0), sticky="nsew")
        self.dot_frame.grid_columnconfigure(0, weight=1)
        self.dot_frame.grid_rowconfigure(0, weight=1)
        
        self.label_sku = customtkinter.CTkLabel(master=self.dot_frame, text="SKU: ", font=('Arial', 30))
        self.label_sku.grid(row=0, column=0, sticky="w", padx=(200,0), pady=(10,0))
        
        self.entrySKU = customtkinter.CTkEntry(master=self.dot_frame, width=250, textvariable=self.text_dot_found, font=('Arial', 30), justify="center")
        self.entrySKU.grid(row=0, column=0, pady=(10, 0))
        
        self.write_sku_button = customtkinter.CTkButton(self.dot_frame, width=80, height=20, command=self.mannual_sku, text="", state=IsGUIDeveloper, image=self.send_image, compound="top")
        self.write_sku_button.grid(row=0, column=0, sticky="e", padx=(0,200),pady=(10, 0))
        
        self.label_dot_result = customtkinter.CTkLabel(master=self.dot_frame, textvariable=self.text_dot_infos, font=('Arial', 20))
        self.label_dot_result.grid(row=1, column=0, padx=10, pady=10)
        
        print("INITIALIZING...")
        #Initialize non-GUI parts
        self.after(100, self.MultiThreadCore)
        print("=" * 50, "\n\n", "READY!", "\n\n", "=" * 50)
        #if (self.ProgramMode == 1):
            #self.play_next_image.configure(self.sidebar_frame, command=self.next_image_event, text="NEXT IMG.", state="normal", image=self.webcam_image)

    def ThreadInitializeObj(self):
        #self.OCR_Engine = DOTOCR()
        #if (self.ProgramMode == 1):
        self.video_frame.update()
        self.video_frame_width = self.video_frame.winfo_width()
        self.video_frame_height = self.video_frame.winfo_height()            
        c_width, c_height = utils.custom_resize(6000, 4000, self.video_frame_width, self.video_frame_height)
        
        self.DD = DOTDetect(c_width, c_height)
        self.TD = TYREDetect(c_width, c_height)
        #else:
            #Logitech Webcam
            #self.DD = None
            #self.TD = None          
        self.DC = DOTCrop()
        self.DOD = DOTOCRDetect()
        self.SR = SKURead()
        self.SS = SKUSave()
        #self.OCR_Engine.Get(crop_image)
        
    def ThreadInitializeRC(self):
        #if (self.ProgramMode == 0):
            #Logitech Webcam
            #self.open_webcam_event()
        self.RC = RemoteControl()        

    def ThreadCallDevNextImage(self):
        while (True):
            self.next_image_event(Devmode=0)
            time.sleep(0.2)
            
    def MultiThreadCore(self):
        
        #self.TemplateMatch = DOTCharMatch()
        
        #ThreadInitializeObj
        Th_Init = threading.Thread(target=self.ThreadInitializeObj, name='tInit')
        Th_Init.daemon=True
        Th_Init.start()        
        
        #FOLDER_READER
        Th_FolderReader = threading.Thread(target=self.IsolatedReadFolder, name='tFolderReader')
        Th_FolderReader.daemon=True
        Th_FolderReader.start()
        
        #CAMERA PROCESS
        if (self.ProgramMode == 0):

            if (self.DisableCamera == 0):
                #CAMERA REMOTE CONTROL (THREADS)
                Th_CameraPhoto = threading.Thread(target=self.RunCameraPhoto, name='tCameraPhoto')
                Th_CameraPhoto.daemon=True
                Th_CameraPhoto.start()
                    
                Th_CameraPhoto = threading.Thread(target=self.ThreadInitializeRC, name='tCameraAPI')
                Th_CameraPhoto.daemon=True
                Th_CameraPhoto.run()
                RC_CameraReady.value = True
                ###
            
            Th_CallCameraPhoto = threading.Thread(target=self.ThreadCallDevNextImage, name='tCameraCallPhoto')
            Th_CallCameraPhoto.daemon=True
            Th_CallCameraPhoto.start()
            
            #if (not self.CameraDetection):
                #self.play_webcam_event()
            self.update_video_button(Execute=False)
            
        else:
            #Read first Image from folder
            self.next_image_event()
            
        print("==== MULTI-THREAD -> INITIALIZED ====\n") 
        return

    def sku_verify_beep(self):
        freq = 1000
        dur = 300
        winsound.Beep(freq, dur)
        
    def sku_verification(self, SKUtext, Key):
        # Suq Lass
        if SKUtext:
            rec, desc, fam = verify(SKUtext)
            if rec == "SKU reconhecido: ":
                return True
        return False      

    def HeuristicVerifyOCR(self, paddle_txt, yolo_txt):
        paddle_l = list(paddle_txt)
        yolo_l = list(yolo_txt)
        maxLSize = max(len(paddle_txt), len(yolo_txt))
                    
        commonList = list("_" * maxLSize)
        for i in range(maxLSize):
            if paddle_l[i] == yolo_l[i]:
                commonList[i] = paddle_l[i]
                continue
            commonList[i] = "*"
        return ("".join(commonList))

    def run_ocr_event(self, index_folder, final = False):
        #self.text_dot_found.set("❌❌")
        #self.label_dot_result.update()

        if (LOCK_OCR_SCANNER.value):
            print("[OCR-WARNING] SKU already found!")
            return            

        if (type(self.small_bboxes) == None): 
            print("[OCR-WARNING] No Crops are available to OCR.")
            return
        
        #Cannot Continue without the SKU
        if not 'SKU' in self.small_bboxes:
            print("[OCR-WARNING] SKU label not found!")
            return
        
        FinalText = ""
        
        print("==== OCR CALL ====")
        #for crop_type in self.small_bboxes:    
        #    pass
        
        crop_type = 'SKU'
        crop_image = self.small_bboxes[crop_type]
        
        YoloOCRtxt, char_bboxes, frame = self.SR.find_sku(crop_image, index_folder)

        #char_amount = len(char_bboxes)
        #print("AAAAA: ", char_amount)
        
        #PaddleOCRtxt = ("_" * char_amount) if char_amount > 0 else ""
        #OCRtext_list = list(PaddleOCRtxt)
        #char_count = 0
        """for char_bbox in char_bboxes:
            #OCRresult = None
            #Process OCR
            #OCRresult = self.OCR_Engine.Get(char_bbox) # Get Paddle Result
            
            #self.TemplateMatch.GetBestMatch(char_bbox) # Get Template-Match Result
            
            if type(OCRresult) != None:
                #print(f"Found DET or REC!\n")
                for idx in range(len(OCRresult)):
                    res = OCRresult[idx]
                    if (len(res) > 0):
                        for line in res:
                            #print("DEBUG[0]: ", line)
                            #PaddleOCRtxt += line[0]
                            ocr_char = line[0]
                            if ocr_char.isalnum():
                                OCRtext_list[char_count] = ocr_char
            char_count += 1
        """      
        #PaddleOCRtxt = ("".join(OCRtext_list)).upper()
        
        if crop_type != 'SKU':
            print(f"PADDLE OCR - {crop_type}: ")
        else:
            Yrec, Ydesc, Yfam = verify(YoloOCRtxt)
            print(f"YOLO OCR   - SKU:{YoloOCRtxt} | Verify: {Yrec}; {Ydesc}; {Yfam}")
            
            #Prec, Pdesc, Pfam = verify(PaddleOCRtxt)
            #print(f"PADDLE OCR - SKU:{PaddleOCRtxt} | Verify: {Prec}; {Pdesc}; {Pfam}")
            
            #HeuristicOCRtxt = self.HeuristicVerifyOCR(PaddleOCRtxt, YoloOCRtxt)
            #Hrec, Hdesc, Hfam = verify(HeuristicOCRtxt)
            #print(f"HEURISTIC OCR - SKU:{HeuristicOCRtxt} | Verify: {Hrec}; {Hdesc}; {Hfam}")
            
            """if (self.sku_verification(PaddleOCRtxt, 'SKU')):
                #self.ocr_result[crop_type] = PaddleOCRtxt
                
                if PaddleOCRtxt in self.CachedConfirmedSKUs:
                    self.CachedConfirmedSKUs[PaddleOCRtxt] += 1
                    self.label_dot_result.update()                     
                else:
                    self.CachedConfirmedSKUs[PaddleOCRtxt] = 1
                    
                self.text_dot_found.set("VERIFICANDO: " + ("⭕ " * self.CachedConfirmedSKUs[PaddleOCRtxt]))
            """

            if (self.sku_verification(YoloOCRtxt, 'SKU')):
                #self.ocr_result[crop_type] = YoloOCRtxt
                
                if YoloOCRtxt in self.CachedConfirmedSKUs:
                    self.CachedConfirmedSKUs[YoloOCRtxt] += 1
                    self.label_dot_result.update()                     
                else:
                    self.CachedConfirmedSKUs[YoloOCRtxt] = 1
                    
                #self.text_dot_found.set("VERIFICANDO: " + ("⭕ " * self.CachedConfirmedSKUs[YoloOCRtxt]))                    
            else:
                if YoloOCRtxt[0] == '8':
                    YoloOCRtxt = 'B' + YoloOCRtxt[1:]
                    
                    if (self.sku_verification(YoloOCRtxt, 'SKU')):
                        #self.ocr_result[crop_type] = YoloOCRtxt
                        Yrec, Ydesc, Yfam = verify(YoloOCRtxt)
                        if YoloOCRtxt in self.CachedConfirmedSKUs:
                            self.CachedConfirmedSKUs[YoloOCRtxt] += 1
                            self.label_dot_result.update()                     
                        else:
                            self.CachedConfirmedSKUs[YoloOCRtxt] = 1
                    
            frame = Image.fromarray(frame)
            width, height = frame.size
            custom_width, custom_height = utils.custom_resize(width, height, self.canvas_sku_width, self.canvas_sku_height)
            resized_image = frame.resize((custom_width, custom_height))
            self.resized_image2 = ImageTk.PhotoImage(resized_image)
            self.canvas_sku.create_image(0, 0, anchor='nw', image=self.resized_image2)
            
            #self.crop_frame.update()
            self.canvas_sku.update()
            #self.canvas_crop.update()
            
        print("==================\n")        
        
        # CHECK for SKU-MVP
        HasMVP_SKU = False
        try:
            #Order by Gretest value
            
            for key in sorted(self.CachedConfirmedSKUs, key=self.CachedConfirmedSKUs.get,reverse=True):
                val = self.CachedConfirmedSKUs[key]
                #print("Order: {0} {1}".format(key, self.CachedConfirmedSKUs[key]))
                if val >= self.OCR_MaxConfirms:
                    self.ocr_result = {'SKU': key}
                    HasMVP_SKU = True  
                    break         
        except:
            pass
        
        if HasMVP_SKU:
            SKU_Recognized.value = True
            self.sku_verify_beep()
            
            #Infos = "N/A"
            Infos = ""
            for key, values in self.ocr_result.items():
                try:
                    FinalText += values #+ " | HEUR: " + HeuristicOCRtxt
                    
                except:
                    pass
            #try:
            #    Infos = "\nPADDLE: " + Prec + Pdesc + Pfam
            #except:
            #    pass
            
            try:
                #Infos += "\n" + Yrec + Ydesc + ' ' + Yfam
                Infos += "Descrição: " + Ydesc + ' ' + Yfam
            except:
                pass                
            
            self.SS.save_skus_to_txt(FinalText)
            self.text_dot_found.set(FinalText.upper())
            self.text_dot_infos.set(Infos.upper())
            self.label_dot_result.update()
            CanPausePhotoTaken = self.DisablePhotoAfterVerify and self.ProgramMode == 0
            LOCK_OCR_SCANNER.value = CanPausePhotoTaken
            self.CachedConfirmedSKUs = {} #Clear Confirmations
            if CanPausePhotoTaken:
                self.update_video_button(Execute=False)

    def show_frame(self, ret, frame):
        if ret:
            frame = cv2.resize(frame, (self.resized_video_width, self.resized_video_height))
            # Convert the image from OpenCV BGR format to PIL RGB format
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Convert the image to PIL format
            image = Image.fromarray(frame)
            # Convert the image to ImageTk format
            image = ImageTk.PhotoImage(image)
            
            # Update the image display
            self.video_frame.image = image
            self.canvas.create_image(0, 0, anchor='nw', image=image)
            self.video_frame.update()
            return True
        return False

    def update_video_button(self, Execute=True):
        if (Execute):
            self.entrySKU.configure(state="disabled")
            #self.write_sku_button.configure(state="disabled")
            
            self.IsVideoPaused = False
            SKU_Recognized.value = False
            self.reset_sku_result()
            self.play_video_button.configure(self.sidebar_frame, command=lambda: self.update_video_button(Execute=False), text="PAUSAR", image=self.pause_image)     
        else:
            self.entrySKU.configure(state="normal")
            #self.write_sku_button.configure(state="normal")
            
            self.IsVideoPaused = True
            self.play_video_button.configure(self.sidebar_frame, command=lambda: self.update_video_button(Execute=True), text="EXECUTAR", image=self.play_image)

    def export_skus(self):
        original_path_skus = self.SS.file_name
        filetype = ("Text file", ".txt")
        
        with open(original_path_skus, "r") as f:
            data = f.read()
        
        filename = filedialog.asksaveasfilename(
            defaultextension=filetype[1],
            filetypes=[filetype]
        )
        
        if filename:
            with open(filename, "w") as f:
                f.write(data)
            
            print(f"Data exported to: {filename}")
            
            with open(original_path_skus, 'w') as file:
                pass
            
            #self.SS.update_sku_file_name()
        
    def mannual_sku(self):
        mannual_input = self.entrySKU.get().upper()
        
        if (not self.sku_verification(mannual_input, 'SKU')):
            return
        
        self.sku_verify_beep()
        
        Yrec, Ydesc, Yfam = verify(mannual_input)
        
        Infos = "Descrição: " + Ydesc + ' ' + Yfam
        
        if SKU_Recognized.value:
            self.SS.save_skus_to_txt(mannual_input, sku_replaced=True)
        else:
            self.SS.save_skus_to_txt(mannual_input)
        self.text_dot_infos.set(Infos.upper())
          

    def open_webcam_event(self):

        webcam = cv2.VideoCapture(2)

        # Check if video opened successfully
        if not webcam.isOpened(): 
            print("Error opening Webcam")
            return

        self.current_video = webcam

        # Get the frame rate of the video
        self.video_fps = webcam.get(cv2.CAP_PROP_FPS)

        # Get the resolution of the video
        width = int(webcam.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(webcam.get(cv2.CAP_PROP_FRAME_HEIGHT))
        aspect_ratio = width / height
        self.video_frame.update()
        self.video_frame_width = self.video_frame.winfo_width()
        self.video_frame_height = self.video_frame.winfo_height()

        # Calculate the new size of the image
        if aspect_ratio > 1:
            # If the image is wider than it is tall
            new_width = self.video_frame_width
            new_height = round(self.video_frame_width / aspect_ratio)
        else:
            # If the image is taller than it is wide
            new_height = self.video_frame_height
            new_width = round(self.video_frame_height * aspect_ratio)

        self.resized_video_width = new_width
        self.resized_video_height = new_height

        print(self.resized_video_height, self.resized_video_width)

        # Read the first frame
        ret, frame = webcam.read()
        self.show_frame(ret, frame)

        self.play_video_button.configure(state="normal")

    #Called by Threading
    def IsolatedReadFolder(self):
        self.pictures_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Camera Output")
        self.out_valid_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Out Valid")
        self.out_invalid_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Out Invalid")
        while (True):
            self.jpg_files = os.listdir(self.pictures_path)
            time.sleep(0.08)

    #Called by UpdateOnly
    def UpdateFolderList(self):
        self.jpg_files = os.listdir(self.pictures_path)

    #Called by Threading
    def RunCameraPhoto(self):
        while (True):
            while (RC_CameraReady.value and not LOCK_OCR_SCANNER.value):
                if (not RC_LOCK_FOCUS.value):
                    RectThresholdX = (abs(RC_DotRectMidX.value - oldRC_DotRectMidX.value) > self.SquareThreshold)
                    RectThresholdY = (abs(RC_DotRectMidY.value - oldRC_DotRectMidY.value) > self.SquareThreshold)
                    
                    if (RectThresholdX or RectThresholdY):
                        print("*" * 30, "\n\n","Initializing Focus:")
                        remoteFocusTh = threading.Thread(target=self.RC.manualClickToFocus, name='tFocusRemoteControl', kwargs={'PosX': RC_DotRectMidX.value, 'PosY': RC_DotRectMidY.value})
                        remoteFocusTh.daemon = True
                        remoteFocusTh.run()
                        oldRC_DotRectMidX.value = RC_DotRectMidX.value
                        oldRC_DotRectMidY.value = RC_DotRectMidY.value
                    RC_LOCK_FOCUS.value = True
                    
                remoteTh = threading.Thread(target=self.RC.take_picture, name='tRemoteControl')
                remoteTh.daemon = True
                remoteTh.run()
                TireFound.value = False
            time.sleep(0.1)

    def UpdateVideoFrame(self, tyre_image):
        # Update frame
        self.video_frame.image = tyre_image
        self.canvas.create_image(0, 0, anchor='nw', image=tyre_image)
        self.canvas.update()        

    def reset_sku_result(self):
        self.CachedFramecount = 0
        LOCK_OCR_SCANNER.value = False
        TireFound.value = False
        self.CachedConfirmedSKUs = {}
        self.text_dot_found.set("")
        self.text_dot_infos.set("")
        self.label_dot_result.update()
        self.canvas.delete("all")
        self.canvas_sku.delete("all")
        #self.canvas_crop.delete("all")
        
        #Delete all images in the folder

        #Try to consume latest photo
        try:
            #_, _ = self.DD.find_dot(self.jpg_files, self.pictures_path, self.out_valid_path,  self.out_invalid_path)
            
            files = glob.glob(self.pictures_path + '/*')
            for file in files:
                os.remove(file)
        except:
            pass

    def next_image_event(self, Devmode=1):
        if Devmode:
            print("[DEV] Running Next Image...")
        # else:
        #     if not TireFound.value:
        #         self.CachedFramecount += 1
        #         if (self.CachedFramecount >= self.ClearResultAfterXframes):
        #             self.reset_sku_result()                   
        #     else:
        #         self.CachedFramecount = 0
    
        if (self.IsVideoPaused and Devmode == 0):
            RC_CameraReady.value = False
            return
        
        print("======== PROCESSING IMAGE ========")
        #Check if there's a image on "Camera Output"
        getPictureAmount = len(self.jpg_files)
        if (getPictureAmount > 0):
            RC_CameraReady.value = False
            if Devmode:
                self.play_next_image.configure(self.sidebar_frame, command=self.next_image_event, text="WAIT...", state="disabled", image=self.pause_image)
            
            #Get New image
            image_path = os.path.join(self.pictures_path, self.jpg_files[0])
            try:
                rawimage = cv2.imread(image_path)
                
                #adjust to canvas size
                self.video_frame.update()
                self.video_frame_width = self.video_frame.winfo_width()
                self.video_frame_height = self.video_frame.winfo_height()                    
                csize_x, csize_y = utils.custom_resize(6000, 4000, self.video_frame_width, self.video_frame_height) 
                            
                #Check DOT boxes
                tyre_image, all_bboxes_tyres, _ = self.DD.show_dot(True, rawimage, resize_x=csize_x, resize_y=csize_y)
                
                if tyre_image:
                    TireFound.value = True
                    print("[Image Event] Tyre found")
                    self.write_dot_sku_frame()                       

                    self.UpdateVideoFrame(tyre_image)
                    # Show crop on interface
                    #self.crop_frame.image = self.resized_image
                    #self.canvas_crop.create_image(0, 0, anchor='nw', image=self.resized_image)
                    #self.crop_frame.update()                    
                    
                else:
                    TireFound.value = False
                    print("[Image event] NO DOT-SKU FOUND")
                    self.reset_sku_result()
            except Exception as e:
                print("Unable to scan photo:\n")
                logging.error(traceback.format_exc())
        else:
            RC_CameraReady.value = True
            print("[Image event] No Images in Output folder")
        if Devmode:
            self.play_next_image.configure(self.sidebar_frame, command=self.next_image_event, text="NEXT IMG.", state="normal", image=self.webcam_image)

    def write_dot_sku_frame(self):
        all_bboxes, image = self.DD.find_dot(self.jpg_files, self.pictures_path, self.out_valid_path,  self.out_invalid_path)
        self.UpdateFolderList() #Force update since Photo was deleted
        
        if image is not None and len(all_bboxes) > 0:# and (time.time() - take_pic_delay) > 0.3:
            #take_pic_delay = time.time()
            
            #Coords from Sony Camera Image 6000x4000
            x1, y1, x2, y2, _score, _class_id = all_bboxes[0]
            RC_LOCK_FOCUS.value = False
            
            RC_DotRectMidX.value, RC_DotRectMidY.value = int((x1 + x2) / 2), int((y1 + y2) / 2)
            
            rotated_dot, index_folder = self.DC.cropDot(image, all_bboxes)

            if rotated_dot:
                print("\n========DOT-SKU FOUND======\n")
                dot_sku_img, small_bboxes, _ = self.DOD.show_dot(rotated_dot, index_folder)

                if len(small_bboxes) >= 1:
                    self.small_bboxes = small_bboxes
                    Th_EventOCR = threading.Thread(target=self.run_ocr_event, name='tRecognition', args={'index_folder': index_folder})
                    Th_EventOCR.daemon=True
                    Th_EventOCR.run()
                
                rotated_dot = dot_sku_img.copy()
                width, height = rotated_dot.size
                custom_width, custom_height = utils.custom_resize(width, height, self.canvas_crop_width, self.canvas_crop_height)
                #self.croped_dot = rotated_dot
                
                self.resized_image = rotated_dot.resize((custom_width, custom_height))
                self.resized_image = ImageTk.PhotoImage(self.resized_image)
                    
    def play_webcam_event(self):
        first_pass = True
        self.update_video_button(Execute=self.IsVideoPaused)

        if (self.IsVideoPaused):
            self.reset_sku_result()
            return
        
        self.DD = DOTDetect(self.resized_video_width, self.resized_video_height)
        self.TD = TYREDetect(self.resized_video_width, self.resized_video_height)

        # Calculate the delay between each frame
        #delay = (1/self.video_fps)

        #take_pic_delay = time.time()
        
        while not self.IsVideoPaused:
            if not TireFound.value:
                self.CachedFramecount += 1
                if (self.CachedFramecount >= self.ClearResultAfterXframes):
                    self.reset_sku_result()                   
            else:
                self.CachedFramecount = 0
            
            getPictureAmount = len(self.jpg_files)
            # Record the start time
            #start_time = time.time()

            # Read the video frame
            ret, frame = self.current_video.read()

            #image, all_bboxes, original_frame = DD.show_dot(ret, frame)
            #tyre_image, all_bboxes_tyres, _ = self.TD.show_tyre(ret, frame)
            tyre_image, all_bboxes_tyres, _ = self.DD.show_dot(ret, frame)
            if tyre_image:
                # If tyre found
                if len(all_bboxes_tyres) > 0:
                    
                    #Coords from Webcam Camera Image 1080x720
                    #x1, y1, x2, y2, _score, _class_id = all_bboxes_tyres[0]
    
                    TireFound.value = True
                    print("TIRE FOUND!!!!")
                    #Execute the next step after a Photo is preset in folder |OR| If OCR Scanner is NOT locked
                    if getPictureAmount <= 0 or LOCK_OCR_SCANNER.value:
                        self.UpdateVideoFrame(tyre_image)
                        continue                       
                    
                    print("PASS WITH: ", getPictureAmount)
                    while (getPictureAmount > 0):
                        self.write_dot_sku_frame()
                        getPictureAmount = len(self.jpg_files)        
                else:
                    TireFound.value = False
                               
                self.UpdateVideoFrame(tyre_image)
                # Show crop on interface
                #self.crop_frame.image = self.resized_image
                #self.canvas_crop.create_image(0, 0, anchor='nw', image=self.resized_image)
                #self.crop_frame.update()
            else:
                TireFound.value = False
                break
                   
            # Calculate the time taken to process the frame
            #time_taken = time.time() - start_time
            # If the time taken is less than the delay, wait for the remaining time
            #if time_taken < delay:
            #    time.sleep(delay - time_taken)