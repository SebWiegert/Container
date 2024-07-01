import os
import sys

import docker
import logging

from docker.errors import DockerException, APIError

from docker_utils import copy_files, remove_files, get_container
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Parse command line arguments, if there are any
if len(sys.argv) > 1:

    parser = argparse.ArgumentParser(description='Process images using mapper_from_images.')

    parser.add_argument('imgs_src', 
                        type=str,
                        help='Folder with images to process'
                        )
    parser.add_argument('ref_id',
                        type=int,
                        help='ID of the marker that will be the origin of the coordinate system'
                        )
    parser.add_argument('marker_size',
                        type=float,
                        help='Size of the marker in meters'
                        )
    parser.add_argument('output_prefix',
                        type=str,
                        help='Prefix added to the output file.',
                        default='map')
    
    args = parser.parse_args()

    # Extract command line arguments
    imgs_src = args.imgs_src
    ref_id = args.ref_id
    marker_size = args.marker_size
    output_prefix = args.output_prefix

    # add other parameters
    out_basename = f'imgs/{os.path.basename(imgs_src)}'
    ref_id = 0


# if no arguments are passed, use the default values
if len(sys.argv) == 1:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    imgs_dir_mounted = os.path.join(script_dir, 'imgs_mounted')

    logging.info(os.listdir(os.path.join("C:\\", "Users", "sebas", "OneDrive", "Masterarbeit")))
    img_src_name = input('Enter the name of the folder: ')
    
    src_dir = os.path.join("C:\\", "Users", "sebas", "OneDrive", "Masterarbeit", img_src_name)
    calib_dir_host = os.path.join("C:\\", "Users", "sebas", "OneDrive", "Masterarbeit", "calib")

    # Load parameters
    marker_size_meters = 0.06
    out_basename = f'imgs/{os.path.basename(src_dir)}'
    ref_id = 0

try:
    # Create a Docker client
    client = docker.from_env()
    client.ping()  # throw an exception if Docker is not reachable
    logging.info('Docker is running.')

except DockerException:
    logging.error('Docker is not running. Please start Docker and try again.')
    sys.exit() 

container = get_container(client)


# empty the mounted folder
if os.listdir(imgs_dir_mounted):
    remove_files(imgs_dir_mounted, filetype = "all")

# Copy images to the mounted folder
copy_files(src_dir, imgs_dir_mounted)
logging.info('Images copied to the mounted folder')



# Start the container
try:
    container.start()
    logging.info('Container started')

except APIError as e:
    logging.error(f'An error occurred during container start: {e}')
    
    if input('Do you want to remove the container? (y/n) ') == 'y':
        container.remove()
        logging.info('Container removed')

    sys.exit(1)

# try to run the commands to process the pictures:
try:
    # List files inside the /imgs directory of the container
    cmd = 'ls /imgs /calib'
    exec_result = container.exec_run(cmd)
    logging.info(exec_result.output.decode())

except APIError as e:
    logging.error(f'An error occurred while checking the availability of the images: {e}')
    container.stop()

mapper_command = f"mapper_from_images /imgs /calib/calib_s23_f08.yml {marker_size_meters} ARUCO_MIP_36h12 {out_basename} -ref {ref_id}"
# run mapper_from_images:
try:    
    cmd = 'mapper_from_images /imgs /calib/calib_s23_f08.yml 0.06 ARUCO_MIP_36h12 imgs/test -ref 0'
    exec_result = container.exec_run(mapper_command)
    logging.info(exec_result.output.decode())

except APIError as e:
    logging.error(f'An error occurred trying to execute mapper_from_images: {e}')
    container.stop()

finally:
    cmd = 'ls /imgs'
    exec_result = container.exec_run(cmd)
    logging.info(exec_result.output.decode())
    container.stop()
    logging.info('Container stopped')

# copy the yaml files to the src folder of the images
copy_files(src=imgs_dir_mounted, dst=src_dir, filetype=".yml")

# delete all files from the mounted folder
remove_files(imgs_dir_mounted, filetype = "all")
logging.info('Images removed from the mounted folder')
