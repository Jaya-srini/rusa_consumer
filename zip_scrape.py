from bs4 import BeautifulSoup
import requests
import csv
import re
import pandas as pd

base_url = 'https://www.house.gov'

# Read all URLs from the CSV file
print("Reading URLs from zip_url.csv...")
url_df = pd.read_csv('zip_url.csv')

# Loop through each URL in the CSV
for idx, row in url_df.iterrows():
    url = row['url']  # Assuming the column name is 'url'
    
    # Get the last 4 characters (like "al01") for the filename
    url_code = url[-4:]
    output_filename = f'zip_split_results_{url_code}.csv'
    
    print(f"\nProcessing {url_code}...")
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f'URL error for {url_code}')
        continue
    else:
        print(f'Page loaded successfully for {url_code}')

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all links that contain "QRY" in their URL (these are ZIP code links)
    all_links = soup.find_all("a", href=True)
    zip_links = []
    for link in all_links:
        if "QRY" in link['href']:
            zip_links.append(link)

    with open(output_filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['ZIP Code', 'Districts', 'Split ZIP'])

        for link in zip_links:
            zipcode = link.text.strip()
            zip_page = base_url + link['href'].replace('..', '')

            sub_response = requests.get(zip_page)
            sub_soup = BeautifulSoup(sub_response.text, 'html.parser')

            # Find all district codes (format: 2 letters + 2 numbers, like "AL01")
            district_links = []
            all_links = sub_soup.find_all('a')

            for link in all_links:
                link_text = link.text.strip()
                
                # Check if it matches district pattern: 2 uppercase letters + 2 digits
                is_district = re.match(r'^[A-Z]{2}\d{2}$', link_text)
                
                if is_district:
                    district_links.append(link_text)
            
            # Remove duplicates
            district_links = sorted(list(set(district_links)))

            # Check if ZIP is split across multiple districts
            if len(district_links) > 1:
                split = "Yes"
            else:
                split = "No"

            # Write one row per ZIP
            writer.writerow([zipcode, ", ".join(district_links), split])
            #print(f"{zipcode}\t{', '.join(district_links)}\t{split}")

    print(f"Results saved to {output_filename}")

    # Clean the CSV file
    print(f"Cleaning {output_filename}...")

    # Read the CSV
    df = pd.read_csv(output_filename)

    # Initialize lists to store cleaned data
    zip_codes = []
    districts_list = []
    split_list = []

    current_zip = None
    current_districts = []

    # Go through each row of the CSV one by one
    for idx2, row2 in df.iterrows():
        value = str(row2['ZIP Code']).strip()
        
        # Check if this value is a number (ZIP code) or text (district code)
        is_zipcode = value.isdigit()
        
        if is_zipcode:
            # Before starting a new ZIP, save the previous one (if it exists)
            if current_zip is not None:
                zip_codes.append(current_zip)
                districts_list.append(", ".join(current_districts))
                
                # Was the previous ZIP split across multiple districts?
                number_of_districts = len(current_districts)
                if number_of_districts > 1:
                    split_list.append("Yes")
                else:
                    split_list.append("No")
            
            # Now start tracking this new ZIP code
            current_zip = value
            current_districts = []  # Reset the districts list for this new ZIP
        
        else:
            # This row is a district code, so add it to our current ZIP's list
            current_districts.append(value)

    # Don't forget to add the last ZIP
    if current_zip is not None:
        zip_codes.append(current_zip)
        districts_list.append(", ".join(current_districts))
        
        # Check if last ZIP was split
        number_of_districts = len(current_districts)
        if number_of_districts > 1:
            split_list.append("Yes")
        else:
            split_list.append("No")

    # Create cleaned DataFrame
    clean_df = pd.DataFrame({
        'ZIP Code': zip_codes,
        'Districts': districts_list,
        'Split ZIP': split_list
    })

    # Save to a cleaned CSV with the same naming pattern
    cleaned_filename = f'zip_split_results_{url_code}_cleaned.csv'
    clean_df.to_csv(cleaned_filename, index=False)

    print(f"Cleaned results saved to {cleaned_filename}")
    print(clean_df.head(20))
    print("\n" + "="*60)

print("\nAll URLs processed!")
