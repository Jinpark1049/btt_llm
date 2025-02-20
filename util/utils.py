import os
import re

def get_page(doc, page_num):
    return doc[page_num].get_text('text')

def pages_to_text(doc, index_list):
    text = ""
    for index in index_list:
        text += get_page(doc, index) + '\n'
    return text

def extract_table_of_content(doc):
    
    results = ''

    for page_num, page in enumerate(doc, start=1):
        page_text = page.get_text("text")
        if page_text.count("·") > 200:
            if page_num < 8:
                results += page_text
        if page_num >= 8:
            break
    text_list = [re.sub(r'·+', '', text).strip() for text in results.split("\n") if text.count("·") > 5]
    
    table_info = dict()
    for item in text_list:
        match = re.match(r'(.+?)\s+(\d+)$', item) 
        if match:
            front_word = match.group(1).strip()
            last_number = match.group(2)
            table_info[front_word] = int(last_number)
    return table_info

def year_pdf_files(main_dir, year):
    
    directory_path = os.path.join(main_dir, str(year))
    all_files = [os.path.join(directory_path, files) for files in os.listdir(directory_path) if files.endswith('.pdf')] 
    print(f"number of files in the folder are {len(all_files)}")
    return all_files


if __name__ == "__main__":
    
    main_dir = "/workspace/btt/bttReports/"
    
    if os.path.exists(main_dir):
        year_pdf_files(main_dir, 2022)
        
    
