import os
import shutil


def organize_files(input_dir, output_dir):
    """Organize PDF files into directories based on site IDs."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.endswith(".pdf"):
            # Extract the site ID from the filename
            site_id = filename.split('_')[0]
            # Create the site directory if it doesn't exist
            site_dir = os.path.join(output_dir, site_id)
            if not os.path.exists(site_dir):
                os.makedirs(site_dir)
            # Move the file to the site directory
            shutil.move(os.path.join(input_dir, filename), os.path.join(site_dir, filename))


if __name__ == "__main__":
    input_directory = "dataset"
    output_directory = "output"
    organize_files(input_directory, output_directory)
