import os
import time
import shutil
import pandas as pd
from termcolor import colored
from sklearn.model_selection import train_test_split

class SegTrainer():
    def __init__(
            self,
            dataset,
            kfold,
            verbose,
            epochs,
            batch_size,
            learning_rate,
            **kwargs):
        # if value not in kwargs or None, use default value
        self.dataset = dataset
        self.verb = verbose
        self.kfold = kfold
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.split_ratio = kwargs.get('split_ratio', 0.8)

        self._train_network_main()


    @property
    def datetime(self): return '20230720_182607' # return time.strftime("%Y%m%d_%H%M%S")


    def _check_params(self):
        """
        Check if parameters are valid.
        """
        assert self.kfold >= 1, 'kfold must be greater than or equal to 1.'
        assert isinstance(self.kfold, int), 'kfold must be an integer.'

        assert os.path.exists(os.path.join('data', self.dataset)), 'Dataset does not exist.'
        assert os.path.exists(os.path.join('data', self.dataset, 'inputs')), 'Dataset does not contain directory "inputs".'
        assert os.path.exists(os.path.join('data', self.dataset, 'labels')), 'Dataset does not contain directory "labels".'
        assert os.path.exists(os.path.join('data', self.dataset, 'stats.csv')), 'Dataset does not contain file "stats.csv".'


    def _train_network_main(self):
        """
        Train the network.
        """
        try:
            # initialize directory structure
            self.save_path = os.path.join('checkpoints', self.datetime)
            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path)
            self._generate_train_test_sets()
        except Exception as e:
            shutil.rmtree(self.save_path)
            print(colored('Training failed, removed directory "%s".' % self.save_path, 'red'))
            raise e
        except KeyboardInterrupt:
            shutil.rmtree(self.save_path)
            print(colored('Training interrupted, removed directory "%s".' % self.save_path, 'red'))
        

    def _generate_train_test_sets(self):
        """
        Generate train and test sets.
        """
        if self.kfold == 1: self._random_split_dataset()
        else:
            for n in range(self.kfold):
                self._split_on_folds()

    
    def _random_split_dataset(self):
        """
        Randomly split dataset into train and test sets.
        """
        # read in the list of images from stats.csv
        img_list = pd.read_csv(os.path.join('data', self.dataset, 'stats.csv'))['idx'].values
        train_list, test_list = train_test_split(img_list, train_size=self.split_ratio, random_state=42)
        with open(os.path.join(self.save_path, 'train_00.txt'), 'w') as f:
            for img in train_list:
                f.write('%s\n' % img)
        with open(os.path.join(self.save_path, 'test_00.txt'), 'w') as f:
            for img in test_list:
                f.write('%s\n' % img)
        

    def _split_on_folds(self):
        """
        Split dataset into train and test sets based on k-fold cross-validation.
        """
        raise NotImplementedError('k-fold cross-validation is not implemented yet.')