import os
import time
import xml.etree.ElementTree as ET

class SKUSave:
	def __init__(self) -> None:
		results_folder_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "SKU Results")
		self.file_name_agro = os.path.join(results_folder_path, "sku_agro.xml")
		self.file_name_truck = os.path.join(results_folder_path, "sku_truck.xml")
	
		self._initialize_xml(self.file_name_agro)
		self._initialize_xml(self.file_name_truck)
		temp_file_name = "temp.txt"
		self.file_name = os.path.join(results_folder_path, temp_file_name)
		#self.timestamp = time.strftime("%Y-%m-%d_%H-%M")

	def _initialize_xml(self, file_name):
		if not os.path.exists(file_name):
			root = ET.Element("SKUs")
			tree = ET.ElementTree(root)
			tree.write(file_name)

	def initialize_both_xml(self):
		for file in [self.file_name_agro, self.file_name_truck]:
			if not os.path.exists(file):
				root = ET.Element("SKUs")
				tree = ET.ElementTree(root)
				tree.write(file)


	def save_skus_to_txt(self, sku, description, family, sku_replaced=False):
    	# If model predict wrong and the person replaced the sku
		if sku_replaced:
			with open(self.file_name, 'r') as file:
				lines = file.readlines()
			index = -1 if len(lines) > 0 else 0
			lines[index] = f"{sku},{description},{family}\n"

			with open(self.file_name, 'w') as file:
				file.writelines(lines)
		else:
			with open(self.file_name, "a") as file:
				file.write(f"{sku},{description},{family}\n")
	
	def save_skus_to_xml(self, sku, description, family, sku_replaced=False):
		if family.upper() == "AGRO":
			file_name = self.file_name_agro
		elif family.upper() == "TRUCK":
			file_name = self.file_name_truck
		else:
			print("[WARNING] SKU family not recognized. Not saving.")
			return

		tree = ET.parse(file_name)
		root = tree.getroot()
        
		if sku_replaced:
			for sku_elem in root.findall("SKU"):  
				if sku_elem.find("Code").text == sku:
					sku_elem.find("Description").text = description
					sku_elem.find("Family").text = family
					break
		else:
			sku_elem = ET.Element("SKU")
			code_elem = ET.SubElement(sku_elem, "Code")
			code_elem.text = sku
			desc_elem = ET.SubElement(sku_elem, "Description")
			desc_elem.text = description
			family_elem = ET.SubElement(sku_elem, "Family")
			family_elem.text = family
			root.append(sku_elem)
        
		tree.write(file_name, encoding="utf-8", xml_declaration=True)

	def export_skus(self, export_path_agro, export_path_truck):
		if export_path_agro and os.path.exists(self.file_name_agro):
			os.replace(self.file_name_agro, export_path_agro)
			self._initialize_xml(self.file_name_agro)
		
		if export_path_truck and os.path.exists(self.file_name_truck):
			os.replace(self.file_name_truck, export_path_truck)
			self._initialize_xml(self.file_name_truck)

	def update_sku_file_name(self):
		self.timestamp = time.strftime("%Y-%m-%d_%H-%M")