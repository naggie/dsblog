DSBLOG aggregates articles and user profiles from a discourse blog category.
DSBLOG can also import articles from RSS feeds to discourse.



Look at `config.example.yml` for configuration.

To run:

```
pip install git+https://github.com/naggie/dsblog.git
dsblog config.example.yml
```

You'll find the website in `output_dir`. The build output is idempotent and stateful
-- previous articles/users are remembered so that old articles that fall off an
RSS feed persist. All output is text, line based so it can be version controlled.

