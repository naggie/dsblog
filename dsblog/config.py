import yaml
from os.path import join,dirname,realpath

script_dir = dirname(realpath(__file__))
default_yml_filepath = join(script_dir,'defaults.yml')


config = dict()

def getConfig():
    if not config:
        raise RuntimeError('config not loaded yet')

    return config


def loadConfig(yml_filepath):
    with open(default_yml_filepath) as f:
        patch = yaml.load(f.read())

    config.update(patch)

    with open(yml_filepath) as f:
        patch = yaml.load(f.read())

    config.update(patch)
