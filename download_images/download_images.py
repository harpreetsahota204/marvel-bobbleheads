"""
Script to download product images from Popcultcha website.
Downloads images for Marvel bobbleheads and Pop! Vinyl figures.
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import fiftyone as fo

def create_download_folder():
    """
    Creates a folder to store downloaded images if it doesn't exist.

    Returns:
        str: Name of the created folder
    """
    folder_name = "popcultcha_products"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    return folder_name

def clean_filename(title):
    """
    Removes invalid characters from filename and limits length.

    Args:
        title (str): Original filename to clean

    Returns:
        str: Cleaned filename safe for saving
    """
    # List of characters that are invalid in filenames
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        title = title.replace(char, '')
    return title[:150]  # Limit filename length to avoid path issues

def download_product_images(url):
    """
    Downloads product images from given Popcultcha URL.

    Args:
        url (str): URL of the product listing page
    """
    # Create folder for downloads
    folder_name = create_download_folder()

    # Set headers to mimic browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Get main page content
    main_response = requests.get(url, headers=headers)
    main_soup = BeautifulSoup(main_response.text, 'html.parser')

    # Find all product links on the page
    product_links = main_soup.find_all('a', class_='product-item-link')
    print(f"Found {len(product_links)} products")

    # Process each product
    for index, product in enumerate(product_links, 1):
        try:
            # Get product URL and clean title
            product_url = product.get('href')
            product_title = clean_filename(product.get_text().strip())

            print(f"\nProcessing ({index}/{len(product_links)}): {product_title}")

            # Get individual product page content
            product_response = requests.get(product_url, headers=headers)
            product_soup = BeautifulSoup(product_response.text, 'html.parser')

            # Try different image selectors - site may use different classes
            product_images = product_soup.find_all('img', class_='gallery-placeholder__image')
            if not product_images:
                product_images = product_soup.find_all('img', class_='fotorama__img')

            # Process each image for the product
            for img_index, img in enumerate(product_images, 1):
                try:
                    # Get image URL - try different possible attributes
                    img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')

                    if img_url:
                        # Add https: if URL starts with //
                        if img_url.startswith('//'):
                            img_url = 'https:' + img_url

                        # Download the image
                        img_response = requests.get(img_url, headers=headers)
                        if img_response.status_code == 200:
                            # Get file extension from URL or default to jpg
                            file_extension = os.path.splitext(img_url)[1] or '.jpg'

                            # Create filename with index and product title
                            file_name = f"{index}_{product_title}_{img_index}{file_extension}"
                            file_path = os.path.join(folder_name, file_name)

                            # Save the image
                            with open(file_path, 'wb') as f:
                                f.write(img_response.content)
                            print(f"Downloaded: {file_name}")

                            # Delay to avoid overwhelming server
                            time.sleep(0.5)

                except Exception as e:
                    print(f"Error downloading image {img_index}: {str(e)}")

        except Exception as e:
            print(f"Error processing product {index}: {str(e)}")

        # Delay between products
        # time.sleep(1)

def create_fiftyone_dataset():
    dataset = fo.Dataset.from_images_patt(images_patt = "./popcultcha_products/*.png",
                                          name="marvel-bobbleheads",
                                          overwrite=True,
                                          persistent=True)

def main():
    # URL of the product listing page
    url = "https://www.popcultcha.com.au/shop-by/brand/marvel/bobble-heads-and-pop-vinyl.html"
    download_product_images(url)
    create_fiftyone_dataset()

if __name__ == "__main__":
    main()