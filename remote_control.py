from pywinauto.application import Application, timings
from pywinauto.keyboard import send_keys
import pywinauto.controls
from time import sleep, perf_counter, monotonic
import threading
import win32api
# Make sure the remote app is already open


class RemoteControl:

    def InitAPI_Program(self) -> None:
        print("INIT SONY REMOTE API")
        ApplicationPath = "C:/Program Files/Sony/Imaging Edge/Remote.exe"

        try:
            self.app = Application(backend="uia").connect(path=ApplicationPath, timeout=5.0)
            self.AlreadyRunning = self.app.is_process_running()
            print("PROGRAM ALREADY RUNNING!")
        except:
            print("========================\nAUTO-OPEN -> Sony Remote.exe")
            self.app = Application(backend="uia").start(ApplicationPath).connect(path=ApplicationPath, timeout=10.0)  

            dialog = self.app.window_(title="Remote")
        
            #print("WAIT FOR WINDOW")
            dialog.wait('exists', timeout=30.0, retry_interval=1)
            #print("WINDOW OPEN: OK")

            wrapper_list = dialog.children()
            #print("REMOTE WRAPPER:\n", wrapper_list)
            CameraNotFound = False
            for wrapper in wrapper_list:
                if "The camera is not connected." in wrapper.window_text():
                    CameraNotFound = True
                    break
            #print("Camera Not Found:", CameraNotFound)
            GetListWrapper = self.app.top_window().children()[0]        

            timings.wait_until(timeout=30, retry_interval=0.1, func=GetListWrapper.is_visible)
            
            #Check if camera is found!
            try:
                if CameraNotFound: 
                    raise ValueError('Kill App')
                
                CollectItems = GetListWrapper.items()[1]
                timings.wait_until(timeout=30, retry_interval=0.1, func=CollectItems.is_visible)
                CollectItems.click_input(double=True) 
            except: 
                print("Error Camera not FOUND!\nRetrying in 5 seconds...")
                self.app.kill(soft=False)
                print("AUTO-KILL -> Sony Remote.exe\n========================")
                sleep(5)
                self.InitAPI_Program() #restart init           
        

    def __init__(self) -> None:
        self.PhotosAmount = 3
        self.CachedFrames = 0
        self.FirstPicture = True
        self.win = None
        # Check if Program is already Running
        self.app = None
        self.AlreadyRunning = False
    
        self.InitAPI_Program()
    
        self.FinishSetup()
        print("CAMERA READY\n========================")

    def debugListElements(self):
        for i in range(len(ListOfElements)):
            if i <= 58: continue
            
            if (ListOfElements[i].friendly_class_name() == "Button"):
                print("Prepare: 1 sec")
                sleep(1)
                print(f"[{i}] Clicking: ", ListOfElements[i])
                try:        
                    ListOfElements[i].click()
                except:
                    print("Unable to Click! SKIPING...")
                sleep(5)
                continue
            print(f"[{i}]Skip: ", ListOfElements[i])        

    def sleep_timer(self, seconds):
        event = threading.Event()
        thread = threading.Thread(target=lambda: event.wait(timeout=seconds))
        thread.daemon = True
        thread.start()
        thread.join()

    def FinishSetup(self):
        self.win = self.app.window(title_re='.*Remote*').wait('ready', timeout=30.0, retry_interval=1)
        
        if not self.AlreadyRunning:
            self.win.type_keys("{VK_LWIN down}"
            "{VK_SHIFT down}"
            "{LEFT down}")

            self.win.type_keys("{VK_LWIN up}"
                    "{VK_SHIFT up}"
                    "{LEFT up}")
        
        # print(f"DEBUG LIST: \n{self.win.children()}")
        # countE = 0
        # for wrapper in self.win.children():
        #     if type(wrapper) == pywinauto.controls.uia_controls.StaticWrapper:
        #         (x, y) = self.win.children()[0].rectangle().mid_point()
        #         print(f"{countE} ELEM: {(x, y)}")
        #         self.win.children()[0].click_input(button='left', coords=(x, y), absolute=True)
        #     countE += 1

        # for i in range(len(self.win.children())):
        #     print(f"[{i}] {self.win.children()[i].window_text()}")
        
        # try:
        #     LiveViewElement = self.app.top_window().children()[98] # LIVE VIEW OFFSET (98 if not hidden.)
        #     LiveViewElement.click()
        # except:
        #     print("WARNING: Unable to hide camera VIEW. (Already hidden or not found)")
           
    def GetAndCheckViewWindowVisibility(self):
        DynamicStaticViewWindow = []
        for wrapper in self.win.children():
            if type(wrapper) == pywinauto.controls.uia_controls.StaticWrapper:
                DynamicStaticViewWindow.append(wrapper)
                #(x, y) = self.win.children()[0].rectangle().mid_point()
                #print(f"{countE} ELEM: {(x, y)}")
                #self.win.children()[0].click_input(button='left', coords=(x, y), absolute=True) 
        
        try:
            timings.wait_until(timeout=2, retry_interval=0.1, func=DynamicStaticViewWindow[0].is_visible)
            return DynamicStaticViewWindow[0]
        except:
            print("Port View Window is NOT visible!")

        return None
                  
    def manualClickToFocus(self, PosX, PosY):
        PosX, PosY = int(PosX), int(PosY)
        
        #PosX, PosY = 3156, 1147
        #PosX, PosY = 3000, 2000
        
        ViewPortElem = self.GetAndCheckViewWindowVisibility()
        
        if (ViewPortElem == None):
            print("ViewPort was NOT found!")
            return None
        ViewPortElem.set_focus()
        
        gx, gy = win32api.GetCursorPos()
        RectPort = ViewPortElem.rectangle()
        
        #Get View Port Resulution
        ViewPortW = RectPort.right - RectPort.left
        ViewPortH = RectPort.bottom - RectPort.top
        ViewPortR = ViewPortW / ViewPortH
        print((ViewPortW, ViewPortH), f"Image Ratio {ViewPortR}")
        
        #Compensate For Non-Visible Area (Original Image ratio is 3:2)
        WidthRatio = 3
        HeightRatio = 2
        IdealL, IdealA = ViewPortW, ViewPortH
        if (ViewPortR > 1):
            IdealL = int((WidthRatio*ViewPortH)/HeightRatio) # L > A
            VisiblePortX = int(RectPort.left + ((ViewPortW - IdealL) / 2))
            VisiblePortY = int(RectPort.top) 
        else:
            IdealA = int((HeightRatio*ViewPortW)/WidthRatio) # A > L
            VisiblePortX = int(RectPort.left)
            VisiblePortY = int(RectPort.top + ((ViewPortH - IdealA) / 2))   
            
        maxVisiblePortX = VisiblePortX + IdealL
        maxVisiblePortY = VisiblePortY + IdealA
             
        VisibleWidth = maxVisiblePortX - VisiblePortX
        VisibleHeight = maxVisiblePortY - VisiblePortY
             
        #Using Sony Camera 6000x4000
        StaticFactorW = 1.02 - (1/24)
        StaticFactorH = 1.10 - (1/16)
        ScaleFactorW = (VisibleWidth/6000) * StaticFactorW
        ScaleFactorH = (VisibleHeight/4000) * StaticFactorH
             
        print(f"Ideal L|A: ({IdealL}, {IdealA})")
        print(f"Rect MidPoint: {PosX}, {PosY}")
        print(f"Max Resulution: {ViewPortW}, {ViewPortH}")
        print(f"Max Visible Resulution: {VisibleWidth}, {VisibleHeight}")
        
        #Scale Point
        (ScalePX, ScalePY) =  (PosX * ScaleFactorW) + VisiblePortX, (PosY * ScaleFactorH) + VisiblePortY
        print(f"Scaled: {ScalePX}, {ScalePY}")
        
        #Set position (clamped Visible Window)
        (SetPX, SetPY) = max(VisiblePortX, min(maxVisiblePortX, int(ScalePX))), max(VisiblePortY, min(maxVisiblePortY, int(ScalePY)))
        ViewPortElem.click_input(button='left', coords=(SetPX, SetPY), absolute=True)
        
        # while (True):
        #     lgx, lgy = win32api.GetCursorPos()
        #     print(lgx, lgy, SetPX, SetPY)
        #     MaxShift = 1
        #     minLgx, maxLgx = lgx - MaxShift, lgx + MaxShift
        #     minLgy, maxLgy = lgy - MaxShift, lgy + MaxShift
            
        #     if ((SetPX >= minLgx and SetPX <= maxLgx) and (SetPY >= minLgy and SetPY <= maxLgy)): break
        #     ViewPortElem.click_input(button='left', coords=(SetPX, SetPY), absolute=True)
        #     sleep(0.08)
        pywinauto.mouse.move(coords=(gx, gy))
        
        print(f"[RemoteControl] {RectPort} Focused at ({SetPX}, {SetPY}) successfully")
            
    def take_picture(self):
        print("TAKE PICTURE...")
        #self.app.Remote['Button4'].click() #Auto Focus!
        
        self.win.type_keys('{VK_NUMPAD1 down}')

        start_time = monotonic()
        self.sleep_timer(0.55)
        
        self.win.type_keys('{VK_NUMPAD1 up}')
        self.sleep_timer(0.04) 
        self.CachedFrames = 0
        
        print("\nPICTURE TAKEN\n", f"Time: {monotonic() - start_time}")