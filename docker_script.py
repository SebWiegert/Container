import os
import sys
import shutil

import datetime

import docker
from docker.errors import DockerException

try:
    client = docker.from_env()
    client.ping()  # throw an exception if Docker is not reachable
    print("Docker is running.")

except DockerException:
    print("Docker is not running. Please start Docker and try again.")

# Create a folder on the host machine. This folder will be mounted to the container
mount_folder_path = os.path.join("mounted_folder")

# check if folder already exists, create it if not
if not os.path.exists(mount_folder_path):
    os.makedirs(mount_folder_path)

# check if folder is empty, delete content if not
else:
    files = os.listdir(mount_folder_path)
    if files:
        for file in files:
            print(file)
        usr = input("Delete folder content? (y/n): ")
        if usr == "y":
            for file in files:
                file_path = os.path.join(mount_folder_path, file)
                os.remove(file_path)
        else:
            print("script aborted by user.")
            sys.exit(1)




# define necessary paths
img_folder_name = "V2_38deg"
host_root_pth = os.path.join("C:\\", "Users", "sebas", "OneDrive", "Masterarbeit")
host_imgs_src = os.path.join(host_root_pth, img_folder_name)
host_calib_src = os.path.join(host_root_pth, "calib", "calib_s23_f08.yml")


# Copy images to the mounted folder
for file in os.listdir(host_imgs_src):
    if file.endswith(".jpg"):
        src = os.path.join(host_imgs_src, file)
        dst = os.path.join(mount_folder_path, file)
        shutil.copyfile(src, dst)

# copy calibration file to folder that will be mounted
if os.path.exists(host_calib_src):
    shutil.copyfile(host_calib_src, os.path.join(mount_folder_path, "calib_s23_f08.yml"))

# create mapper_from_images cli command
input_dir="/imgs/"
calib_file="imgs/calib_s23_f08.yml"
marker_size=0.06
marker_dict="ARUCO_MIP_36h12"
output=f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')}"
ref_id = f"-ref 0"



# Prepare env variables to run the container with the mounted folder and execute the command

image_name = "mapper_container:latest"
command_to_run = f"cd /imgs/ && ls" # mapper_from_images {input_dir} {calib_file} {marker_dict} {marker_size} {output} {ref_id}"

# Run the container
container = client.containers.run(
    image_name,
    command="/bin/bash -c '{}'".format(command_to_run),
    volumes={
        mount_folder_path: {'bind': '/imgs/', 'mode': 'rw'},
    },
    stdout=True,
    stderr=True
)

print(container.decode("utf-8"))

# Wait for the cont#container.wait()

# Delete .jpg files and files with calib in their filename from mount_folder_path
for file in os.listdir(mount_folder_path):
    if file.endswith(".jpg") or "calib" in file:
        file_path = os.path.join(mount_folder_path, file)
        os.remove(file_path)

# Move the rest of the files to the "output" folder in the current directory
output_folder_path = os.path.join("output")
if not os.path.exists(output_folder_path):
    os.makedirs(output_folder_path)

for file in os.listdir(mount_folder_path):
    file_path = os.path.join(mount_folder_path, file)
    dst = os.path.join(output_folder_path, file)
    shutil.move(file_path, dst)

# Remove the mounted folder to prevent problems
shutil.rmtree(mount_folder_path)

# get the logs and print them
logs = container.logs()
print(logs)

# Clean up
container.remove()