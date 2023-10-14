import os
import markdown
from bs4 import BeautifulSoup

def convert_md_to_html(root_folder):
    # Ensure the build directory exists
    build_dir = os.path.join(root_folder, 'build')
    os.makedirs(build_dir, exist_ok=True)

    # List to hold the links to all converted files
    links = []

    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as md_file:
                    md_content = md_file.read()

                # Convert markdown to HTML
                html_content = markdown.markdown(md_content, extensions=['tables'])

                # Optionally, prettify the HTML using BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                pretty_html = soup.prettify()

                # Construct the output file name and path
                output_file_name = os.path.splitext(file)[0] + '.html'
                output_file_path = os.path.join(build_dir, output_file_name)

                # Write the HTML content to the output file
                with open(output_file_path, 'w', encoding='utf-8') as html_file:
                    html_file.write(pretty_html)

                # Add a link to this file to the links list
                links.append(f'<a href="build/{output_file_name}">{output_file_name}</a><br>\n')

                print(f'Converted {file} to HTML and saved to {output_file_path}')

    # Create the index.html file
    index_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Index of Converted Files</title>
</head>
<body>
    <h1>Index of Converted Files</h1>
    {''.join(links)}
</body>
</html>
"""
    index_file_path = os.path.join(root_folder, 'index.html')
    with open(index_file_path, 'w', encoding='utf-8') as index_file:
        index_file.write(index_content)

    print(f'Created index.html at {index_file_path}')

if __name__ == "__main__":
    root_folder = './'  # Replace with the path to your folder
    convert_md_to_html(root_folder)
