import os
import time

class SKUSave:
	def __init__(self) -> None:
		results_folder_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "SKU Results")
		temp_file_name = "temp.txt"
		#self.timestamp = time.strftime("%Y-%m-%d_%H-%M")
		self.file_name = os.path.join(results_folder_path, temp_file_name)

	def save_skus_to_txt(self, sku, sku_replaced=False):
		# If model predict wrong and the person replaced the sku
		if sku_replaced:
			with open(self.file_name, 'r') as file:
				lines = file.readlines()
			
			lines[-1] = sku + '\n'
	
			with open(self.file_name, 'w') as file:
				file.writelines(lines)
		else:
			with open(self.file_name, "a") as file:
				file.write(f"{sku}\n")
	
	def update_sku_file_name(self):
		self.timestamp = time.strftime("%Y-%m-%d_%H-%M")