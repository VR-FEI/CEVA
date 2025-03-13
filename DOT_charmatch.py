import cv2
import os
from skimage.metrics import structural_similarity as ssim

class DOTCharMatch:
    def __init__(self) -> None:
        self.TemplateFolder = os.path.join(os.path.dirname(os.path.realpath(__file__)), ".Digits")   
        
    def GetBestMatch(self, nparr) -> dict:
        gray_reference = cv2.cvtColor(nparr, cv2.COLOR_BGR2GRAY)
        
        best_match = None
        max_ssim = -1
        for filename in os.listdir(self.TemplateFolder):
            if filename.endswith(".png"): 
                # Load each image
                image = cv2.imread(os.path.join(self.TemplateFolder, filename))
                image = cv2.resize(image, (gray_reference.shape[1], gray_reference.shape[0]))
                gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                # Compute the Structural Similarity Index (SSIM) between the two images
                (score, diff) = ssim(gray_reference, gray_image, full=True)
                diff = (diff * 255).astype("uint8")
                # print("[INFO] Match: {}, SSIM: {}".format(filename, score))

                # If the current SSIM score is higher than the current max SSIM, update max SSIM and best match
                if score > max_ssim:
                    max_ssim = score
                    best_match = filename
        print("Best match: {}, SSIM: {}".format(best_match[0], max_ssim))
        return {}