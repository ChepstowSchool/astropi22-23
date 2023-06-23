
# Import the libraries needed for the program to run.
from pathlib import Path
from PIL import Image
from pycoral.adapters import common
from pycoral.adapters import classify
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.dataset import read_label_file
from picamera import PiCamera
import os
from time import sleep, time
from orbit import ISS
from datetime import datetime, timedelta
from pathlib import Path

# Find location of main.py file for relative file paths.
base_folder = Path(__file__).parent.resolve()
# Naming cursor for PiCamera and setting resolution of images.
cam = PiCamera()
cam.resolution = (1290, 720)
'''Declaring variable count_cloud to count how many images are categorised as clouds.
Cloud images will be deleted, but as a plan B, we will count how many images of clouds are deleted.
We will use this data to calculate a percentage of cloud free sky to make a calculation on available sky space that could be used for artificial cloud seeding.'''
cloud_count = 0
 
def convert(angle):
    """
    Convert a `skyfield` Angle to an EXIF-appropriate
    representation (positive rationals)
    e.g. 98° 34' 58.7 to "98/1,34/1,587/10"

    Return a tuple containing a boolean and the converted angle,
    with the boolean indicating if the angle is negative.
    """
    sign, degrees, minutes, seconds = angle.signed_dms()
    exif_angle = f'{degrees:.0f}/1,{minutes:.0f}/1,{seconds*10:.0f}/10'
    return sign < 0, exif_angle


def capture(camera, image):
    """Use `camera` to capture an `image` file with lat/long EXIF data."""
    point = ISS.coordinates()

    # Convert the latitude and longitude to EXIF-appropriate representations
    south, exif_latitude = convert(point.latitude)
    west, exif_longitude = convert(point.longitude)

    # Set the EXIF tags specifying the current location
    camera.exif_tags['GPS.GPSLatitude'] = exif_latitude
    camera.exif_tags['GPS.GPSLatitudeRef'] = "S" if south else "N"
    camera.exif_tags['GPS.GPSLongitude'] = exif_longitude
    camera.exif_tags['GPS.GPSLongitudeRef'] = "W" if west else "E"

    # Capture the image and append time stamp
    cam.capture(image)
    
# Create a `datetime` variable to store the start time
start_time = datetime.now()
# Create a `datetime` variable to store the current time
# (these will be almost the same at the start)
now_time = datetime.now()
    
    
# Run a loop for 180 minutes - 1 minute to allow for the image capture loop.
while (now_time < start_time + timedelta(minutes=179)):
    # Capture an image from the PiCam every 10 seconds.
    sleep(10)
    
    cam.start_preview()
    # Creates a filename with a time stamp appended. Stores image in root folder
    file_name = str(base_folder) + "/image_" + str(time()) + ".jpg"
    file = file_name
    # Calls the capture function
    capture(cam, file)
    # Update the current time to ensure our 179 minute countdown is accurate
    now_time = datetime.now()

    #Setting the relative file path for the ML module.
    script_dir = Path(__file__).parent.resolve()

    #Declaring variables for the files and data for the ML module.
    model_file = script_dir/'models/model_edgetpu.tflite'
    data_dir = script_dir/'data'
    label_file = data_dir/'labels.txt'
    image_file = file

    interpreter = make_interpreter(f"{model_file}")
    interpreter.allocate_tensors()

    size = common.input_size(interpreter)
    image = Image.open(image_file).convert('RGB').resize(size, Image.ANTIALIAS)

    common.set_input(interpreter, image)
    interpreter.invoke()
    classes = classify.get_classes(interpreter, top_k=1)

    # Checks the assigned labels for images by the ML module.
    # Delete images that are not coast line images, and count how many cloud images are deleted.
    labels = read_label_file(label_file)
    for c in classes:
        print(f'{labels.get(c.id, c.id)} {c.score:.5f}')

    if (f'{labels.get(c.id, c.id)}') == "land":
        os.remove(file)
    elif (f'{labels.get(c.id, c.id)}') == "clouds":
        os.remove(file)
        cloud_count += 1
    elif (f'{labels.get(c.id, c.id)}') == "nightAndTwilight":
        os.remove(file)
    
    # Save the count of cloud files deleted to a .txt file
    f = open(str(base_folder) + "/cloud_count.txt", 'w')

    clouds = str(cloud_count)
    f.write(clouds)

    f.flush()
    os.fsync(f.fileno())

    f.close()

# Close the Picamera
cam.stop_preview()