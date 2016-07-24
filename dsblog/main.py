#/usr/bin/env python
import yaml
import sys
import compiler


def main():
    if len(sys.argv) != 2:
        print "DSblog compiler"
        print "Usage: %s <config.yml>" % sys.argv[0]
        sys.exit()
    else:
        with open(sys.argv[1]) as f:
            config = yaml.load(f.read())

    compiler.compile(
            url=config["url"],
            api_user=config["api_user"],
            api_key=config["api_key"],
            category=config["category"],
            output_dir=config["output_dir"],
    )

if __name__ == "__main__":
    main()
