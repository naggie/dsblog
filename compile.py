from jinja2 import Environment, FileSystemLoader
import os

output_directory = 'www/'


env = Environment(loader=FileSystemLoader('templates'))

template = env.get_template('blog.html')
filepath = os.path.join(output_directory,'index.html')
template.stream().dump(filepath)
