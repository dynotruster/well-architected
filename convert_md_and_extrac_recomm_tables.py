import datetime
import os
from lark import logger
import markdown
from bs4 import BeautifulSoup
import json
import logging
import colorlog
from collections import OrderedDict
from collections import defaultdict

order_counter = 0  # Global order counter
local_counter = defaultdict(int)

root_folder = './well-architected' 
today = datetime.date.today().strftime('%Y-%m')
build_dir = os.path.join(root_folder, f'build/{today}')
# Load pre-trained word embeddings model


def get_most_similar(text, valid_pillars):
    text = text.lower()
    max_count = 0
    most_similar = None
    
    for pillar in valid_pillars:
        count = sum(1 for word in pillar.lower().split() if word in text)
        if count > max_count:
            max_count = count
            most_similar = pillar
    
    if most_similar is None:
        return None, 0  # Return None and 0 if no similar pillar is found
    
    similarity_rate = max_count / max(1, len(most_similar.split()))  # Avoid division by zero
    return most_similar, similarity_rate


def setup_logger():
    logger = colorlog.getLogger()
    logger.setLevel(logging.INFO)

    # Create a console handler
    handler = colorlog.StreamHandler()
    handler.setLevel(logging.INFO)

    # Create a formatter and set it for this handler
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# Setup the logger
logger = setup_logger()


def convert_to_title(text):
    words = text.split('-')
    title_words = [word.capitalize() for word in words]
    title = ' '.join(title_words)
    return title

def get_pillar(file_path_part, previous_hader):
    
    valid_pillars =['Performance Efficiency', 'Operational Excellence', 'Cost Optimization', 'Security', 'Reliability',]
    pillar_text =convert_to_title(file_path_part)
    logger.info(f'{pillar_text}, {file_path_part}' )
    most_sim = get_most_similar(previous_hader,valid_pillars)

    if  pillar_text in valid_pillars:  
        return pillar_text
    if most_sim[0] in valid_pillars:
        if (most_sim[1] < .7):
            logger.warning(f'Not so close : {previous_hader} , {most_sim}' )
        logger.warning(f'Most similiar: {previous_hader} , {most_sim}' )
        return most_sim[0]
    else:
        logger.warning(f'Invalid pillar >>>>>> : {previous_hader}')
        return "Reliability"
        
       
        
def get_applies_to(file_path):
    applies_to = '/'.join(file_path.split('/')[2:-1])  # Exclude root and file name
    category = file_path.split('/')[-1].split('.')[0].replace('-well-architected-framework', '')
    pillar_categories = [
        'cost-optimization',
        'operational-excellence',
        'reliability',
        'performance-efficiency',
        'security'
    ]
    if category  in pillar_categories:
         return applies_to
    
    if category not in pillar_categories:
        if category != 'overview' and category.replace('-review','') not in applies_to:
            return applies_to + "/" + category
        else:
            return applies_to
       
    
    
def get_category(file_path):
    category = file_path.split('/')[-1].split('.')[0]
    return category


def extract_table_data(table , file_path , pillar):
    global order_counter  # Declare the global variable
    rows = table.find_all('tr')[1:]  # Skip header row
    table_data = []
    for row in rows:
        columns = row.find_all('td')
        if len(columns) >= 2:
            order_counter += 1
            category = get_category(file_path)
            applies_to = get_applies_to(file_path)

            table_data.append({
                'title': columns[0].text.strip(),
                'description': columns[1].text.strip(),
                'order': order_counter,
                'category': category,
                'applies_to': applies_to,
                'file_path': file_path,
                'pillar': pillar
                
            })
    return table_data

def convert_md_to_html(root_folder):
    os.makedirs(build_dir, exist_ok=True)

    all_table_data = []
    html_links = []  # List to collect the paths of the converted files

    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as md_file:
                    md_content = md_file.read()

                html_content = markdown.markdown(md_content, extensions=['tables'])
                soup = BeautifulSoup(html_content, 'html.parser')

                tables = soup.find_all('table')
                for table in tables:
                    header = table.find('th')
                    if header and ('Recommendation' in header.text or 'Recommendations' in header.text):
                      
                        # Calculate the pillar form file path or previous h2 header
                        h2_header = table.find_previous('h2')
                        if h2_header:
                            logger.info(f'Found h2: {h2_header.text}')
                        else:
                            logger.warning('No preceding h2 found')
                        pillar = file_path.split('/')[-1].split('.')[0]
                        h2_header_text = h2_header.text if h2_header else None 
                        logger.info(f'{pillar} ,{h2_header_text} , {file_path}')

                        pillar = get_pillar(pillar ,h2_header_text)
                        table_data = extract_table_data(table , file_path , pillar )
                        all_table_data.extend(table_data )



                        output_file_name = os.path.splitext(file)[0] + '.html'
                        output_file_path = os.path.join(build_dir, output_file_name)
                        with open(output_file_path, 'w', encoding='utf-8') as html_file:
                            html_file.write(str(table))
                        
                        html_links.append(f'<li><a href="{output_file_name}">{output_file_name}</a></li>')  # Collect the file path

                        logger.info(f'Saved table from {file} to {output_file_path}')

    # Generate the index.html file
    index_content = (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "    <meta charset=\"UTF-8\">\n"
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        "    <title>Index of Converted Files</title>\n"
        "</head>\n"
        "<body>\n"
        "    <ul>\n"
        + '\n'.join(html_links) +
        "    </ul>\n"
        "</body>\n"
        "</html>"
    )

    index_file_path = os.path.join(build_dir, 'index.html')
    with open(index_file_path, 'w', encoding='utf-8') as index_file:
        index_file.write(index_content)

    return all_table_data


def merge_similar_items(items):
    processed_items = []
    order_counter = 1

    while items:
        current_item = items.pop(0)
        merged_item = {
            "title": current_item["title"],
            "description": current_item["description"],
            "order": order_counter,
            "categories": OrderedDict.fromkeys([current_item["category"]]),
            "applies_to": OrderedDict.fromkeys([current_item["applies_to"]]),
            "file_paths": OrderedDict.fromkeys([current_item["file_path"]]),
            "pillars": OrderedDict.fromkeys([current_item["pillar"]])
        }
        i = 0
        while i < len(items):
            item = items[i]
            if current_item["title"] == item["title"] and current_item["description"] == item["description"]:
                merged_item["categories"].update(OrderedDict.fromkeys([item["category"]]))
                merged_item["applies_to"].update(OrderedDict.fromkeys([item["applies_to"]]))
                merged_item["file_paths"].update(OrderedDict.fromkeys([item["file_path"]]))
                merged_item["pillars"].update(OrderedDict.fromkeys([item["pillar"]]))
                items.pop(i)
            else:
                i += 1
        # Convert OrderedDict keys back to lists
        merged_item["categories"] = list(merged_item["categories"].keys())
        merged_item["applies_to"] = list(merged_item["applies_to"].keys())
        merged_item["file_paths"] = list(merged_item["file_paths"].keys())
        merged_item["pillars"] = list(merged_item["pillars"].keys())
        
        processed_items.append(merged_item)
        order_counter += 1
    
    return processed_items



generated_aids = set()

def gen_aid(applies_to):
    # Extracting the last part of the path
    last_part = applies_to.split('/')[-1]

    # Splitting the last part by '-'
    parts = last_part.split('-')

    # Check for the conditions: more than two dashes and begins with "azure-"
    if last_part.count('-') > 2 and last_part.startswith('azure-'):
        # Remove "azure-" from the beginning
        last_part = last_part.replace('azure-', '', 1)
        # Remove "-instance" from the end if present
        last_part = last_part[:-9] if last_part.endswith('-instance') else last_part

    # Taking the first two letters from each part
    prefix_parts = [part[:2].upper() for part in parts]

    # Joining the extracted letters with a '-'
    prefix = '-'.join(prefix_parts)

    local_counter[last_part] += 1

    # Creating the AID
    aid = f'{prefix}-{"{:02d}".format(local_counter[last_part])}'
    if aid in generated_aids:
        raise ValueError(f'Duplicate AID generated: {aid}')
    
    generated_aids.add(aid)
    return aid

def produce_final_items(items):
    processed_items = []
    while items:
        current_item = items.pop(0)
        final_item = {
            "aid": gen_aid(current_item["applies_to"][0]),
            "title": current_item["title"],
            "description": current_item["description"],
            "order": current_item["order"],
            "applies_to": ", ".join(current_item["applies_to"]),
            "pillars": ", ".join(current_item["pillars"]),
            "type" : "Azure-Well-Arch-Oct-2023",
            "comments": "",
            "azureMatchedRuels":"",
        }
        processed_items.append(final_item)
    return processed_items
    
if __name__ == "__main__":
    root_folder = '.'      # Replace with the path to your folder

    today = datetime.date.today().strftime('%Y-%m')
    build_dir = os.path.join(root_folder, f'build/{today}')
    table_data = convert_md_to_html(root_folder)

    # Output the table data to a JSON file
    json_output_path = os.path.join(root_folder, build_dir, 'table_data.json')
    with open(json_output_path, 'w', encoding='utf-8') as json_file:
        json.dump(table_data, json_file, indent=4, ensure_ascii=False)

    logger.info(f'Saved table data to {json_output_path}')



    merged_itmes = merge_similar_items(table_data)

    merged_items_path = os.path.join(root_folder, build_dir, 'merged-itmes.json')

    with open(merged_items_path, 'w', encoding='utf-8') as json_file:
        json.dump(merged_itmes, json_file, indent=4, ensure_ascii=False)

    logger.info(f'Saved merged items to {merged_items_path}')




    final_items = produce_final_items(merged_itmes)

    final_items_path = os.path.join(root_folder, build_dir, 'final_items.json')

    with open(final_items_path, 'w', encoding='utf-8') as json_file:
        json.dump(final_items, json_file, indent=4, ensure_ascii=False)

    logger.info(f'Saved merged items to {final_items_path}')


