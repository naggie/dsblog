DSBLOG aggregates articles and user profiles from:

 1. A discourse blog category
 2. RSS feeds


Look at `config.example.yml` for configuration.

To run:

    virtualenv .
    source bin/activate
    pip install -r requirements.txt
    python ./dsblog/dsblog.py config.example.yml build/

You'll find the website in build.
