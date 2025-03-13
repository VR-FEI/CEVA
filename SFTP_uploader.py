import paramiko
import os
import datetime
import pytz

class SFTPUploader:
    def __init__(self):
        self.host = "ftpext.cevalogistics.com"
        self.port = 22
        self.username = "saleslatam"
        self.password = "L9FYD38+ke\"+"
        self.remote_path = "/FEI-XMLs/"
        self.sftp = None
        self.client = None

        results_folder_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "SKU Results")
        self.file_name_agro = os.path.join(results_folder_path, "sku_agro.xml")
        self.file_name_truck = os.path.join(results_folder_path, "sku_truck.xml")
    
    def connect(self):
        """Estabelece conexão SFTP"""
        try:
            self.client = paramiko.Transport((self.host, self.port))
            self.client.connect(username=self.username, password=self.password)
            self.sftp = paramiko.SFTPClient.from_transport(self.client)
            print("[INFO] Conexão SFTP estabelecida com sucesso!")
        except Exception as e:
            print(f"[ERRO] Falha ao conectar ao SFTP: {e}")
            self.disconnect()

    def disconnect(self):
        """Fecha a conexão SFTP"""
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
        print("[INFO] Conexão SFTP fechada.")

    def upload_file(self, local_file_path, file_type):
        """Faz upload do arquivo XML para o SFTP"""
        if not os.path.exists(local_file_path):
            print(f"[ERRO] Arquivo não encontrado: {local_file_path}")
            return
        
        # Gerar timestamp para o nome do arquivo
        tz = pytz.timezone("America/Sao_Paulo")  # Ajuste conforme necessário
        timestamp = datetime.datetime.now(tz).strftime("%Y-%m-%d_%H-%M-%S")
        
        # Renomear arquivo antes de enviar
        file_name = os.path.basename(local_file_path)
        new_file_name = f"{file_type}_{timestamp}.xml"
        remote_file_path = os.path.join(self.remote_path, new_file_name)

        try:
            self.sftp.put(local_file_path, remote_file_path)
            print(f"[INFO] Arquivo {new_file_name} enviado com sucesso para {self.remote_path}")
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao enviar {local_file_path}: {e}")
            return False

    def upload_sku_files(self):
        """Faz upload dos arquivos Agro e Truck"""
        self.connect()
        pass_agro = self.upload_file(self.file_name_agro, "AGRO")
        pass_truck = self.upload_file(self.file_name_truck, "TRUCK")
        self.disconnect()

        if pass_agro and pass_truck:
            return True
        return False

    