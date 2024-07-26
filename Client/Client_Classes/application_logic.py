import Global.custom_models
from Global.custom_models import VGG,MNISTMLP
import json
import torch
from io import BytesIO
import base64
import zlib
from Global import base_io

class dflmq_client_app_logic():
    
    def __init__(self, is_simulating,id,root_directory)-> None:

        self.id = id
        self.is_simulating = is_simulating
        self.root_directory = root_directory
        self.logic_model = None
        self.logic_model_name = ""
        self.simulated_logic_data_train = None
        self.simulated_logic_data_test = None
        self.simulated_logic_dataset_name = None
       
        self.executables = ['construct_logic_model', 'collect_logic_model', 'collect_logic_data', 'load_model', 'load_dataset']

    def load_model(self, model_name):
        dir = self.root_directory + "/models/"
        data = base_io.load_file(dir,model_name)
        if(data != -1):
            self.logic_model = data
            self.logic_model_name = model_name
            print("Model " + model_name + " loaded.")
    
    def load_dataset(self,dataset_name):
        dir = self.root_directory + "/datasets/"
        data1 = base_io.load_file(dir,dataset_name+"_training")
        data2 = base_io.load_file(dir,dataset_name+"_testing")
        if(data1 != -1):
            self.simulated_logic_dataset_name = dataset_name 
            self.simulated_logic_data_train = data1
            print("Training dataset loaded. set size: " + str(len(data1)))
        if(data2 != -1):
            self.simulated_logic_data_test = data2
            print("Test dataset loaded. set size: " + str(len(data2)))
    
    def construct_logic_model(self, model_name, model_params):
        self.logic_model = Global.custom_models.get_model_class(model_name)
        self.logic_model_name = model_name

        self.collect_logic_model(model_params)

        dir = self.root_directory + "/models/"
        base_io.save_file(dir,model_name,self.logic_model)
    
    def collect_logic_model(self, parameters):
        print(len(parameters))
        weights_and_biases = json.loads(parameters)
        for name, param in self.logic_model.named_parameters():
            if name in weights_and_biases:
                param.data = torch.tensor(weights_and_biases[name])
    
    def collect_logic_data(self,dataset_name, type, bin_data):
        print("performing data collection")

        decoded_compressed_data = base64.b64decode(bin_data.encode('utf-8'))
        decompressed_data = zlib.decompress(decoded_compressed_data)
        buffer_from_string = BytesIO(decompressed_data)
        loaded_dataset = torch.load(buffer_from_string)
        
        self.simulated_logic_data_train = loaded_dataset["trainset"]
        self.simulated_logic_dataset_name = dataset_name  
        self.simulated_logic_data_test = loaded_dataset["testset"]
        print("Number of images in the loaded training dataset:", len(loaded_dataset["trainset"]))
        print("Number of images in the loaded testing dataset:", len(loaded_dataset["testset"]))
        dir = self.root_directory + "/datasets/"
        base_io.save_file(dir,dataset_name+"_training",loaded_dataset["trainset"])
        base_io.save_file(dir,dataset_name+"_testing",loaded_dataset["testset"])
        
    def get_model(self):
        return 0
    
    def get_data(self):
        return 0
    
    def _execute_on_msg(self, header_parts, body):

        if header_parts[2] == 'collect_logic_model':
            print("received collect model command. parsing command ...")
            model_params = body.split(' -model_params ')[1].split(';')[0]
            self.collect_logic_model(model_params)

        if header_parts[2] == 'construct_logic_model':
            print("received construct model command. parsing command ...")
            id = body.split('-id ')[1].split(' -model_name ')[0]
            if(id == 'all' or id == self.id):
                model_name = body.split('-model_name ')[1].split(' -model_params ')[0]
                model_params = body.split(' -model_params ')[1].split(';')[0]
            
                self.construct_logic_model(model_name, model_params)
               
        
        if header_parts[2] == 'collect_logic_data':
            print("received collect data command. parsing command ...")
            id = body.split('-id ')[1].split(' -dataset_name ')[0]
            print(id)
            print(self.id)
            if(id == 'all' or id == self.id):
                print("id match")
                dataset_name = body.split('-dataset_name ')[1].split(' -dataset_type ')[0]
                dataset_type = body.split(' -dataset_type ')[1].split(' -data ')[0]
                bin_data     = body.split(' -data ')[1].split(';')[0]
                self.collect_logic_data(dataset_name,dataset_type,bin_data)
        
        if header_parts[2] == 'load_model':
            model_name = body.split('-model_name ')[1].split(';')[0]
            self.load_model(model_name)

        if header_parts[2] == 'load_dataset':
            dataset_name = body.split('-dataset_name ')[1].split(';')[0]
            self.load_dataset(dataset_name)
            
        