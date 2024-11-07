import requests 
from bs4 import BeautifulSoup
import os
import time
import fiftyone as fo
from urllib.parse import urljoin

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
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        title = title.replace(char, '')
    return title[:150]

def get_total_pages(soup):
    """
    Gets the total number of pages from the pagination element.
    
    Args:
        soup (BeautifulSoup): Parsed HTML of the main page
        
    Returns:
        int: Total number of pages, defaults to 1 if not found
    """
    pagination = soup.find('ul', class_='pages-items')
    if pagination:
        pages = pagination.find_all('a', class_='page')
        if pages:
            try:
                return max(int(page.get_text().strip()) for page in pages)
            except ValueError:
                return 1
    return 1

def download_product_images(base_url):
    """
    Downloads product images from all pages of Popcultcha URL.

    Args:
        base_url (str): Base URL of the product listing page
    """
    folder_name = create_download_folder()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # Get first page to determine total pages
    main_response = requests.get(base_url, headers=headers)
    main_soup = BeautifulSoup(main_response.text, 'html.parser')
    
    product_count = 0
    
    # Process each page
    for page in range(1, 5):
        page_url = f"{base_url}?p={page}" if page > 1 else base_url
        
        try:
            page_response = requests.get(page_url, headers=headers)
            page_soup = BeautifulSoup(page_response.text, 'html.parser')
            product_links = page_soup.find_all('a', class_='product-item-link')
            
            print(f"Found {len(product_links)} products on page {page}")
            
            # Process each product on the page
            for index, product in enumerate(product_links, 1):
                try:
                    product_url = product.get('href')
                    product_title = clean_filename(product.get_text().strip())
                    product_count += 1

                    print(f"\nProcessing product {product_count}: {product_title}")

                    product_response = requests.get(product_url, headers=headers)
                    product_soup = BeautifulSoup(product_response.text, 'html.parser')

                    product_images = product_soup.find_all('img', class_=['gallery-placeholder__image', 'fotorama__img'])

                    for img_index, img in enumerate(product_images, 1):
                        try:
                            img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')

                            if img_url:
                                if img_url.startswith('//'):
                                    img_url = 'https:' + img_url

                                img_response = requests.get(img_url, headers=headers)
                                if img_response.status_code == 200:
                                    file_extension = os.path.splitext(img_url)[1] or '.jpg'
                                    file_name = f"{product_count}_{product_title}_{img_index}{file_extension}"
                                    file_path = os.path.join(folder_name, file_name)

                                    with open(file_path, 'wb') as f:
                                        f.write(img_response.content)
                                    print(f"Downloaded: {file_name}")

                                    # time.sleep(0.5)

                        except Exception as e:
                            print(f"Error downloading image {img_index}: {str(e)}")

                except Exception as e:
                    print(f"Error processing product {product_count}: {str(e)}")

            # Delay between pages
            # time.sleep(2)

        except Exception as e:
            print(f"Error processing page {page}: {str(e)}")

def create_fiftyone_dataset():
    """Creates a FiftyOne dataset from downloaded images"""
    dataset = fo.Dataset.from_images_patt(
        images_patt="./popcultcha_products/*.png",
        name="marvel-bobbleheads",
        overwrite=True,
        persistent=True
    )
    return dataset

def main():
    base_url = "https://www.popcultcha.com.au/shop-by/brand/marvel/bobble-heads-and-pop-vinyl.html"
    download_product_images(base_url)
    create_fiftyone_dataset()

if __name__ == "__main__":
    main()