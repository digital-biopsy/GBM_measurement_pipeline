import os
import cv2
from tqdm import tqdm
import shutil
import pandas as pd
from termcolor import colored

class ImagePrep():
    def __init__(self, 
                 datapath, 
                 dataset,
                 sliding_step, 
                 tile_size,
                 verbose,
                 **kwargs):
        self.datapath = datapath
        self.dataset = dataset
        self.tile_size = tile_size
        self.sliding_step = sliding_step
        self.verb = verbose
        self.downsample_factor = kwargs.get('downsample_factor', 2)
        
        self._check_params()
        self._preprocess()


    def _check_params(self):
        """
        Check if parameters are valid.
        """
        # check if raw data directory exists
        if not os.path.exists(self.datapath):
            raise FileNotFoundError('Data path does not exist.')
        
        # check if dataset is valid
        if self.dataset == 'all':
            self.dataset = os.listdir(self.datapath)
            self.dataset.remove('.DS_Store')
        elif self.dataset not in os.listdir(self.datapath):
            raise FileNotFoundError('Dataset does not exist in data path.')
        else:
            self.dataset = [self.dataset]

        # check downsample factor
        assert self.downsample_factor >= 1, 'Downsample factor must be greater than or equal to 1.'
        assert isinstance(self.downsample_factor, int), 'Downsample factor must be an integer.'


    def _preprocess(self):        
        """
        Main function to preprocess images.
        """
        self.img_stats = [None] * len(self.dataset)
        self.img_count = [0] * len(self.dataset)
        for i, ds in enumerate(self.dataset):
            self._check_raw_data_directory(ds)
            if self._setup_saving_directories(ds):
                if self.include_stats:
                    # only keep the Image, Genotype, Genotype (#), Animal, GBMW, FPW, SDD columns
                    # GBML will be removed as it will lose its meaning after being cropped
                    img_stats = pd.read_csv(os.path.join(self.datapath, ds, 'stats.csv'))
                    img_stats = img_stats[['Image', 'Genotype', 'Genotype (#)', 'Animal', 'GBMW', 'FPW', 'SDD']]
                    self.img_stats[i] = img_stats
                self._crop_images(ds, i)
            
            
    def _setup_saving_directories(self, ds):
        """
        Setup saving directories for preprocessed images.
        """
        # check if there's a directory called 'data' in current directory
        if not os.path.exists('data'):
            os.mkdir('data')
            if self.verb: print(colored('Created directory "data".', 'blue'))
        # check if there's a directory called 'data/ds' in current directory
        if not os.path.exists(os.path.join('data', ds)):
            os.mkdir(os.path.join('data', ds))
            if self.verb: print(colored('Created directory "data/%s".' % ds, 'blue'))
        else:
            # ask if user wants to overwrite existing directory or append to it
            print(colored('Directory "data/%s" already exists.' % ds, 'yellow'))
            overwrite = input(colored('Do you want to overwrite it? (y/n): ', 'yellow'))
            while overwrite not in ['y', 'n']:
                overwrite = input(colored('Please enter (y/n): ', 'yellow'))

            if overwrite == 'y':
                shutil.rmtree(os.path.join('data', ds))
                os.makedirs(os.path.join('data', ds, 'inputs'))
                os.makedirs(os.path.join('data', ds, 'labels'))
                if self.verb: print(colored('Overwritten directory "data/%s".' % ds, 'blue'))
                return True
            elif overwrite == 'n':
                if self.verb: print(colored('Skipped directory "data/%s".' % ds, 'blue'))
                return False


    def _check_raw_data_directory(self, ds):
        """
        Check if dataset include directory 'inputs' and 'labels' and file 'stats.csv'
        """
        if not os.path.exists(os.path.join(self.datapath, ds, 'inputs')):
            raise FileNotFoundError('Dataset does not contain directory "inputs".')
        if not os.path.exists(os.path.join(self.datapath, ds, 'labels')):
            raise FileNotFoundError('Dataset does not contain directory "labels".')
        if not os.path.exists(os.path.join(self.datapath, ds, 'stats.csv')):
            self.include_stats = False
            if self.verb: print(colored('Dataset does not contain file "stats.csv", skipped ...', 'yellow'))
        else: self.include_stats = True
        
    
    def _crop_images(self, ds, ds_idx):
        """
        Crop images in dataset.
        """
        # get list of images in dataset
        input_list = {os.path.splitext(img)[0]: img for img in os.listdir(os.path.join(self.datapath, ds, 'inputs')) if img != '.DS_Store'}
        label_list = {os.path.splitext(img)[0]: img for img in os.listdir(os.path.join(self.datapath, ds, 'labels')) if img != '.DS_Store'}
        # create a csv file to store source-to-cropped image mapping
        with open(os.path.join('data', ds, 'stats.csv'), 'w') as f:
            # GBML is not included in the csv file as it will lose its meaning after being cropped
            if self.include_stats: f.write('idx,image,genotype,genotype_idx,animal,GBMW,FPW,SDD\n')
            else: f.write('idx,image\n')

        # iterate through images
        for img_name, full_input_name in tqdm(input_list.items(), desc=f'Preprocessing {ds}', ncols=80):
            if img_name not in label_list:
                if self.verb: tqdm.write(colored('Image %s\'s label not found, skipped ...' % full_input_name, 'grey'))
                continue
            if self.include_stats:
                # check if image is also in stats.csv
                if full_input_name not in self.img_stats[ds_idx]['Image'].values:
                    if self.verb: tqdm.write(colored('Image %s not found in stats.csv, skipped ...' % full_input_name, 'grey'))
                    continue

            full_label_name = label_list[img_name]
            self._sliding_window_crop(os.path.join(self.datapath, ds), ds_idx, full_input_name, full_label_name)

                
    def _sliding_window_crop(self, path, ds_idx, input_name, label_name):
        """
        Crop image using sliding window method.
        """
        input_img = cv2.imread(os.path.join(path, 'inputs', input_name))
        label_img = cv2.imread(os.path.join(path, 'labels', label_name))

        # downsample image
        if self.downsample_factor > 1:
            input_img = cv2.resize(input_img, (input_img.shape[1]//self.downsample_factor, input_img.shape[0]//self.downsample_factor))
            label_img = cv2.resize(label_img, (label_img.shape[1]//self.downsample_factor, label_img.shape[0]//self.downsample_factor))

        # check if image is of the same size of the label
        if input_img.shape != label_img.shape: raise ValueError('Image and label are not of the same size.')
        # get image dimensions
        height, width, _ = input_img.shape
    
        # crop image
        # get image metadata if stats.csv is included
        if self.include_stats:
            metadata = self.img_stats[ds_idx][self.img_stats[ds_idx]['Image'] == input_name].values[0]
            metadata = ','.join([str(m) for m in metadata])
        else: metadata = input_name
        
        for i in range(0, height, self.sliding_step):
            for j in range(0, width, self.sliding_step):
                # check if cropped image is of the same size as the label
                if i+self.tile_size > height or j+self.tile_size > width: continue
                # save cropped image
                input_cropped = input_img[i:i+self.tile_size, j:j+self.tile_size]
                label_cropped = label_img[i:i+self.tile_size, j:j+self.tile_size]
                self._save_cropped_image(
                    metadata, 
                    input_cropped, 
                    label_cropped, 
                    ds_idx
                )
                self.img_count[ds_idx] += 1


    def _save_cropped_image(
            self,
            metadata,
            input_cropped,
            label_cropped,
            idx,
            ):
        """
        Save cropped image.
        """
        # get image name
        img_idx = self.img_count[idx] + 1
        # save image
        cv2.imwrite(os.path.join('data', self.dataset[idx], 'inputs', f'{img_idx}.png'), input_cropped)
        cv2.imwrite(os.path.join('data', self.dataset[idx], 'labels', f'{img_idx}.png'), label_cropped)
        
        # write to csv file
        with open(os.path.join('data', self.dataset[idx], 'stats.csv'), 'a') as f:
            f.write(f'{img_idx},{metadata}\n')
        