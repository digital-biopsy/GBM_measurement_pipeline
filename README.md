# Digital Biopsy Pipeline
This is an automated TEM image measurement pipeline for Glomerular Basement Membrane width (GBMW) and Foot Processes width (FPW). The detailed method is published on bioRxiv: [to be added]. <br>
<p align="center"><img src="./imgs/demo.png" width="550"></p>

## Installation
### Prepare the environment (optional but recommended)
It is recommended to install the package dependencies in an [Anaconda](https://www.anaconda.com/products/individual) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) environment. To install, checkout the official installation guide for [Anaconda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) and [Miniconda](https://docs.conda.io/en/latest/miniconda.html#installing).
- Create a conda environment
    ```
    conda create -n digital-biopsy python=3.8
    ```
- Activate the environment
    ```
    conda activate digital-biopsy
    ```
- Deactivate the environment
    ```
    conda deactivate
    ```
### Install the dependencies
```
pip install -r requirements.txt
```

## Run the code
Configuring this pipeline primarily involves two part of the settings:
- Arguments parsed from the command line: these arguments primarily control what task to perform, e.g. preprocessing, segmentation, measurement, evaluation, etc.
- Parameters defined in `params.yaml`: these parameters primarily control the hyperparameters of the model, e.g. how to tile the image, training parameters, and some constants of the input images (pixel/nm ratio) etc.

## Arguments syntax
```
python main.py [-h] [-prep [DATASET]] [-i] [-v]
```
### Task arguments
These arguments control what task to perform. They are mutually exclusive, meaning only one of them can be used at a time.
`-prep`: 
    Preprocess the dataset. This will perform the image cropping, image shuffling, and subject-wise k-fold cross validation (CV). As the data stored in the 'stats.csv' is performed by multiple operators and lacks format consistency, it will also performed the corner case handling to exclude the data that does not contain a desired stats entry (GBMW or FPW etc.) <br>
### Other arguments
`-v`: Verbosely print currently training process, helpful for debugging.
#### Prepare the dataset
##### args
To load the image to the UNet as well as the pipeline, it needed to be pre-processed (cropped) into smaller image patches. This can be done by running the following command. This command will automatically create a folder named `data/` under the project root directory if there is not one, and store the pre-processed data in it. <br>
This argument requires an additional parameter which is the `<name of the dataset>` or `all`, which will specify which folder (dataset) to preprocess under the datapath. The image processing pipeline requires a specific structure of the data. See [Dataset structures](#dataset-structures) for more details.
```
python main.py -prep [dataset name]
```
##### Related params
| Parameter           | Default          | Required     | Description                                    |
| ------------------- | ---------------- | -------------| ---------------------------------------------- |
| `datapath`          | `data/`          | yes          | The path to the dataset.                       |
| `downsample_factor` | 2                | no           | The downsample factor of the image. Namely, how many pixels are averaged into one pixel on each dimension. E.g. 2 means 4 pixels are averaged into one pixel. |
| `tile_size`         | 512              | no           | The size of the image patch. (width = height)  |
####


## `params.yaml`


## Dataset structures
For raw data, we requires it to be stored in the following structure.
```
|-datapath/ </br>
|---dataset/ </br>
|-----stats.csv </br>
|-----inputs/ </br>
|-------img-name-1.jpg </br>
|-------img-name-2.jpg </br>
|------- ... </br>
|-----labels/ </br>
|-------img-name-1.png </br>
|-------img-name-2.png </br>
|------- ... </br>
```
`datapath` is the root directory of all datasets, we designed in following way as the mice biopsy data could be sampled from different mice or different time points. It will be easier to manage the data if we store them in different `dataset` folders. In each `dataset` folder, three component is required: 1. `inputs` is the folder that contains all the raw images. 2. `labels` is the folder that contains all the labels. The label name must be exact match of the input name. 3. [Optional:] the `stats.csv` file that contains the 'expert' measurement of the dataset. If the directory does not contain the `stats.csv` file, the program will not be able to perform the measurement evaluation. <br>
In the above example, the part 'img-name-1' could be replaced by arbitrary string, as long as there's a corresponding label with the same name in the `labels` folder. <br>
**NOTE**: All names must be unique, otherwise the program will overwrite the existing file with the same name and cause unexpected behavior.


## arg '-prep'
This argument will pre-process the image. It will perform the image cropping, image shuffling, and subject-wise k-fold cross validation (CV). As the data stored in the 'stats.csv' is performed by multiple operators and lacks format consistency, it will also performed the corner case handling to exclude the data that does not contain a desired stats entry (GBMW or FPW etc.)
### Related params (params_meta.py)
kfold = 5 (0 if all in inputs, 1 if all in tests, 5 by default (80% train 20% test))
sliding_step = 300 (the step size of the sliding window after downsampling. i.e the raw img are first downsampled before performing sliding window).
### Generated Dataset
The '-prep' command will first initialize a Preprocess instance by loading all the pre-processing params. Then it reads all the raw image-label pairs in and store their absolute path in 'project_root/data/kfold/inputs-<subject-groupname>.txt'. The subject-wise kfold will requires kfold shuffle before applying cropping. Hence, Preprocessor will first shuffle the subjects and store them in 'project_root/data/kfold/fold_<n>/', append corresponding raw-image and raw-label input train/test list according to the current fold, and perform the cropping. </br>
The cropped training image tiles are stored into the 'project_root/data/labels/' and 'project_root/data/inputs/' folder. The testing labels and inputs are stored in the 'inputs' and 'labels' folder under the 'project_root/data/test/'. The validation folder is a lengacy folder, we currently use in-line validation that is randomly selected during training so this folder is no longer needed.
### Generated Dataset Structure
|-project_root/data/ </br>
|---tile_stats.csv </br>
|---kfold/ </br>
|-----fold_0/ </br>
|-------inputs.txt (all abs path of input imgs of this fold) </br>
|-------labels.txt (all abs path of labels of this fold) </br>
|-----fold_1/ </br>
|-------inputs.txt (all abs path of input imgs of this fold) </br>
|-------labels.txt (all abs path of labels of this fold) </br>
|-----inputs-<subject-groupname-1>.txt (abs paths of imgs in this group) </br>
|-----labels-<subject-groupname-1>.txt (abs paths of labels in this group) </br>
|-----inputs-<subject-groupname-2>.txt (abs paths of imgs in this group) </br>
|-----labels-<subject-groupname-2>.txt (abs paths of labels in this group) </br>
|---inputs/ (all cropped trainset inputs) </br>
|---labels/ (all cropped trainset labels) </br>
|---test/
|-----inputs/ (all cropped testset inputs) </br>
|-----labels/ (all cropped testset labels) </br>
## arg '-kfold'
*** NOTE: this will deleted the pre-trained weight matrix ***
*** NOTE: do not use any command that calls update_image_list after running this command, it will re-shuffle the kfold and cause deprecated measurement result (could be using the training fold for testing) ***
This argument will automatically do the kfold data preprocessing and the training.
### arg '-train'
*** NOTE: do not use any command that calls update_image_list after running this command, it will re-shuffle the train and cause deprecated measurement result (could be using the training fold for testing) ***
This argument train the shuffled inputs/labels pairs. It need to be used after applying '-prep'.
### arg '-pred'
This command will predict (segment) the test set using the trained_weight matrices of the corresponding fold.
### arg '-save'
This argument will visualize the predicted results w.r.t. the original image and highlight the False Positive labels and False Negative labels.
### arg '-eval'
This argument perform the GBMW and FPW measurement. It will also do the same procedure as '-save'

## To Do List
- [x] Randomize the train test split.
- [x] Add data (input/target/test) into .gitignore.
- [ ] Test if current model work on cpu devices.
- [x] Train test split already included in the code, delete the validation folder.
- [x] Intergrate the image tiling with the training script.
- [ ] Refactor code to enable training on server/local pc.
- [ ] Check the optimizer logic
- [ ] Add grayscale augmentation methods to prevent overfitting on color.
- [x] Move parameters to 'params_meta.py'
## To Run The Script
#### Commands
Data pre-processing is required before training. The data path is defined in 'params-meta.py'
```
python main.py -prep
```
Hyperparameters are defined in 'params-meta.py'
```
python main.py -train
```
The following command will predict using the trained model and save the predictions under the 'pred' folder<br>
Note: the model must align with the weight matrices that used to predict. Changing the hyperparameters might cause runtime failures.
```
python main.py -pred
```
#### Optional command(s)
The following optional command works with '-pred' and '-train'. This will verbosely print out some of the training progresses that help debugging.
```
-v
```
## Git Commands
The easiest way to use github is through [Github Desktop](https://desktop.github.com/). But here are some commands that might be helpful in case of necessary.
#### 1. Clone the repository
```
git clone <http address of the repository>
```
```
git clone https://github.com/digital-biopsy/deep-segmentation.git
```
Github might prompt user to enter their token before access the repository. Setup instructions are [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token). Don't forget to take down the token somewhere.
#### 2. Create a branch
Creating a branch helps users to commit changes that haven't been fully tested.
1. Create a branch in local repository.
```
git checkout -b <your branch name>
```
2. Push to the remote branch
Creating a branch locally would not chage the remote repository. The below command can push the new local branch to remote.
```
git push -u origin <a branch that not in the remote>
```
3. Switch to other branch.
All changes in the current branch need either be commited or stashed.
```
git checkout <an already existed branch>
```
#### 3. Git Commit and Stash
Git commit allow you to commit changes locally which git push save changes remotely.
1. Check current changes
git status will print out all the changed files.
```
git status
```
2. Git add
git add will add all changes but sometime its not desirable because it might also add dependencies or cache files.
```
git add .
```
```
git add <file path in the root directory and the file name>
```
3. Git commited
```
git commit -m "some commit message about the change"
```

4. Git Push
Push changes to remote branch. For the most of the time, remote names are just 'origin'
```
git push <remote name> <branch name>
```
5. Git pull
pull remote changes (collaborators' changes to local repo)
```
git pull
```

#### 4. Common workflow of committing to remote branch.
Create a new branch.
```
git branch checkout -b <your branch name>
```
Work on the changes.
Pull all the remote changes and solve conflicts locally.
```
git pull
```
Add changed files. Repeat this until add all the files.
```
git add <file name>
```
Commit changes
```
git commit -m "some commit message about the change"
```
Push the changes to new branch
```
git push -u origin <a branch that not in the remote>
```
or push to an existing branch.
```
git push origin <a branch that not in the remote>
```
