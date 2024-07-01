import os
import shutil

import logging
import sys



def check_environment():
    required_folders = ['imgs_mounted', 'calib_mounted', 'backup']
    for folder in required_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            logging.info(f"Created folder: {folder}")

def check_and_copy_calib_file(calib_folder, backup_folder, calib_file_name):
    calib_file_path = os.path.join(calib_folder, calib_file_name)
    backup_file_path = os.path.join(backup_folder, calib_file_name)
    
    # Check if the calib file exists in the calib folder
    if not os.path.exists(calib_file_path):
        # Check if the calib file exists in the backup folder
        if os.path.exists(backup_file_path):
            try:
                shutil.copy(backup_file_path, calib_file_path)
                logging.info(f"Calib file copied from {backup_folder} to {calib_folder}")
            except Exception as e:
                logging.error(f"Failed to copy calib file: {e}")
        else:
            logging.error(f"Calib file not found in backup folder: {backup_folder}")


        
def copy_files(src, dst, filetype=".jpg"):
    """
    Copy files from the source directory to the destination directory.

    Args:
        src (str): The path to the source directory.
        dst (str): The path to the destination directory.
        filetype (str, optional): The file extension to filter the files. Defaults to ".jpg", "all" copys all existing files.


    Raises:
        SystemExit: If an error occurs while copying the files.

    """
    for file in os.listdir(src):
        if file.endswith(filetype) or filetype == "all":
            src_file = os.path.join(src, file)
            dst_file = os.path.join(dst, file)
            
            try:
                shutil.copyfile(src_file, dst_file)
            except Exception as e:
                print(f"An error occurred: {e}")
                sys.exit(1)
    
                
def remove_files(folder, filetype=".jpg"):
    """
    Remove files of a specific type from a folder.

    Args:
        folder (str): The path to the folder containing the files.
        filetype (str, optional): The type of files to remove. Defaults to ".jpg".

    Raises:
        OSError: If an error occurs while removing a file.

    """
    if filetype == "all":
        for file in os.listdir(folder):
            try:
                os.remove(os.path.join(folder, file))
            except Exception as e:
                logging.error(f"An error occurred while removing file {file}: {e}")

    elif filetype == ".jpg":
        for file in os.listdir(folder):
            if file.endswith(filetype):
                try:
                    os.remove(os.path.join(folder, file))
                except Exception as e:
                    logging.error(f"An error occurred while removing file {file}: {e}")
          
def get_container(client, imgs_folder_name:str ="imgs_mounted", calib_folder_name:str="calib"):
   
    imgs_dir_mounted=os.path.join(os.path.dirname(os.path.abspath(__file__)), imgs_folder_name)
    if not os.path.exists(imgs_dir_mounted):
        os.makedirs(imgs_dir_mounted)
    
    calib_dir_mounted=os.path.join(os.path.dirname(os.path.abspath(__file__)), calib_folder_name)
    if not os.path.exists(calib_dir_mounted):
        os.makedirs(calib_dir_mounted)
        logging.error("Calibration folder had to be created. Please add calibration file to the folder.")
        sys.exit(1)

    # check if container exists
    containers = client.containers.list(all=True, filters={"ancestor": "mapper_container:latest"})
    
    # if container available: return the container
    if len(containers) == 1:
        container = containers.pop()
        return container

    # if no container available: Create the container
    if not containers:
        container_config = {
            'image': 'mapper_container:latest',
            'volumes': {
                imgs_dir_mounted: {'bind': '/imgs', 'mode': 'rw'},
                calib_dir_mounted: {'bind': '/calib', 'mode': 'rw'}
            },
            'command': "tail -f /dev/null"  # Keeps the container running
        }
        try:
            container = client.containers.create(**container_config)
            logging.info(f'Container created: {container.attrs.name}')
        
        except Exception as e:
            logging.error(f"An error occurred during container creation: {e}")
            sys.exit(1)

        return container
    


    if len(containers) > 1:
        logging.warning("More than one container with the same base image found. Remove all but the latest?")
        usr_input = input("(y/n): ")
        
        if usr_input.lower() != "y":
            logging.info("Exiting the program. Please remove unecessary containers manually.")
            sys.exit(0)

        if usr_input.lower() == "y":
            containers_by_age = sorted(containers, key=lambda x: x.attrs['Created'])
            
            try:
                while len(containers) > 1:
                    c_to_delete = containers_by_age.pop(0)
                    c_to_delete.stop()
                    c_to_delete.remove()
                    logging.info(f"Container {c_to_delete.attrs['Name']} removed.")
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                sys.exit(1)
            
