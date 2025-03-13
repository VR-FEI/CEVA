from paddleocr import PaddleOCR,draw_ocr
import numpy
import os
import sys

class DOTOCR:
    def __init__(self) -> None:
        self.ocr = PaddleOCR(
            debug=False,
            use_gpu=True,
            use_mlu=False,
            use_mp=True,
            gpu_mem=1024,
            
            save_crop_res=False,
            crop_res_save_dir= ".\\crop_output\\",
            image_dir=None,
            
            det=False,
            #det_algorithm='DB',
            det_model_dir=None,
            #det_db_thresh=0.5,
            #det_db_box_thresh=0.4,
            #det_db_unclip_ratio=2.0,
            #use_dilation=True,
            #det_db_score_mode="slow",
            #det_image_shape="3, 48, 160",
            ocr_version="PP-OCRv4",
            
            rec_batch_num=32,
            rec_algorithm="ParseQ",
            rec_model_dir=".\\Models\\OCR\\rec_ceva_parseq_ar_char_i3", #rec_abinet_trained
            rec_char_dict_path= ".\\Models\\OCR\\parseq_dict.txt",
            rec_thresh=0.8,
            rec_image_shape="3,32,128",
            use_space_char=False,
            rec_image_inverse=False,
            drop_score=0.5,
            max_text_length=25,
            
            cls_model_dir=None,
            use_angle_cls=False,
            
            use_tensorrt=False, 
            #min_subgraph_size=1, 
            lang='en',
            
            return_word_box=False,
        ) # need to run only once to download and load model into memory

    def Get(self, crop_nparray):
        EnableRec = True
        # print(self.ocr.ocr('./TestOCRe/DOT.png', cls=False, det=False, rec=EnableRec))
        # print(self.ocr.ocr('./TestOCRe/LOCAL.png', cls=False, det=False, rec=EnableRec))
        # print(self.ocr.ocr('./TestOCRe/CHAR.png', cls=False, det=False, rec=EnableRec))
        # print(self.ocr.ocr('./TestOCRe/SKU.png', cls=False, det=False, rec=EnableRec))
        # print(self.ocr.ocr('./TestOCRe/DATA.png', cls=False, det=False, rec=EnableRec))
        # print("=====================================================")
        return self.ocr.ocr(crop_nparray, cls=False, det=False, rec=EnableRec)

    def DrawPaddleF(self):
        return draw_ocr
