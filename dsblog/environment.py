import yaml
from os import makedirs
from os.path import join,dirname,realpath,isdir

script_dir = dirname(realpath(__file__))
default_yml_filepath = join(script_dir,'defaults.yml')

defaults = {
    "output_dir": 'output',

    "header_img_dir": 'imgs/headers/',
    "scaled_img_dir": 'imgs/scaled/',
    "original_img_dir": 'imgs/original/',

    "max_article_img_width": 710,
    "max_avatar_width": 710,
}

config = dict()

def getConfig():
    if not config:
        raise RuntimeError('config not loaded yet')

    return config


def loadConfig(yml_filepath):
    config.update(defaults)

    with open(yml_filepath) as f:
        patch = yaml.load(f.read())

    config.update(patch)

    # make paths absolute
    config['header_img_dir'] = join(config['output_dir'],config['header_img_dir'])
    config['scaled_img_dir'] = join(config['output_dir'],config['scaled_img_dir'])
    config['original_img_dir'] = join(config['output_dir'],config['original_img_dir'])


def makeDirs():
    if not config:
        raise RuntimeError('config not loaded yet')

    for key in ['header_img_dir','scaled_img_dir','original_img_dir']:
        path = config[key]

        if not isdir(path):
            makedirs(path)
