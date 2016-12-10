#/usr/bin/env python
import yaml
import sys

def main():
    if len(sys.argv) != 3:
        print "DSblog aggregator"
        print "Usage: %s <config.yml> <build_dir/>" % sys.argv[0]
        sys.exit()
    else:
        build_dir = sys.argv[2]
        with open(sys.argv[1]) as f:
            config = yaml.load(f.read())

if __name__ == "__main__":
    main()
