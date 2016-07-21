DSBLOG renders articles and user profiles from a discourse blog category.

Articles can be imported from other systems in an idempotent manner.


Look at `config.example.yml` for configuration.

To run:

    virtualenv .
    source bin/activate
    pip install -r requirements.txt
    python ./dsblog/dsblog.py config.example.yml build/

You'll find the website in build. The build output is idempotent and stateful
-- previous articles/users are remembered so that old articles that fall off an
RSS feeds persist. All output is text, line based so it can be version controlled.

