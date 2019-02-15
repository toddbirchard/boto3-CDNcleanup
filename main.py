import os
import json
import boto3
from botocore.client import Config
from urllib.parse import unquote
from resizeimage import resizeimage

# Initialize a session using DigitalOcean Spaces.
session = boto3.session.Session()
client = session.client('s3',
                        region_name='nyc3',
                        endpoint_url='https://nyc3.digitaloceanspaces.com',
                        aws_access_key_id=os.environ.get('KEY'),
                        aws_secret_access_key=os.environ.get('SECRET'))


def get_folders():
    """Retrieve all folders underneath the specified directory.

    1. Set our bucket name.
    2. Specify a delimitr, AKA a character that all the files we're target have in common.
    3. Set folder path to objects as "Prefix".
    4. Create list of all recursively discovered folder names.
    5. Return list of folders.
    """
    get_folder_objects = client.list_objects_v2(
        Bucket='hackers',
        Delimiter='',
        EncodingType='url',
        MaxKeys=1000,
        Prefix='posts/2018/',
        ContinuationToken='',
        FetchOwner=False,
        StartAfter=''
        )
    folders = [item['Key'] for item in get_folder_objects['Contents']]
    print('folders', folders)
    return folders


def sanitize_object_key(obj):
    """Replace character encodings with actual characters."""
    new_key = unquote(unquote(obj))
    return new_key


def get_objects_in_folder(folderpath):
    """List all objects in the provided directory."""
    objects = client.list_objects_v2(
        Bucket='hackers',
        EncodingType='url',
        MaxKeys=1000,
        Prefix=folderpath,
        ContinuationToken='',
        FetchOwner=False,
        StartAfter=''
        )
    return objects


def create_retina_image(item):
    """Renames our file to specify that it is a Retina image."""
    indx = item.index('.')
    newname = item[:indx] + '@2x' + item[indx:]
    newname = sanitize_object_key(newname)
    client.copy_object(Bucket='hackers', CopySource='hackers/' + item, Key=newname)
    print(newname, " created!")


def create_standard_image(item):
    """Resizes large images to an appropriate size."""
    indx = item.index('/')
    filename = item[indx:]
    try:
        client.download_file(item, 'temp_img_store/' + filename)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise
    oldname = sanitize_object_key(item)
    resized_img = resizeimage.resize_width(img, width/2)
    print('oldname = ', oldname)


def manipulate_objects():
    """Build our entire CDN for us plzkthx.

    1. Loop through folders in subdirectory.
    2. In each folder, loop through all objects.
    3. Specify substrings likely to be found in 'garbage' files and remove them.
    4. Check if a period exists in our filename (thus not a folder)
    5. If so, clone the image object to match '@2x' retina display naming convention.
    6. Compress the size of the original image.
    7. Save images in WebP format.
    """
    for folder in get_folders():
        folderpath = sanitize_object_key(folder)
        objects = get_objects_in_folder(folderpath)
        for obj in objects['Contents']:
            item = sanitize_object_key(obj['Key'])
            banned = ['Todds-iMac', 'conflicted', 'Lynx']
            if any(x in item for x in banned):
                client.delete_object(Bucket="hackers", Key=item)
            else:
                if '.' in item:
                    create_retina_image(item)
                    create_standard_image(item)
                    client.delete_object(Bucket="hackers", Key=item)


manipulate_objects()
