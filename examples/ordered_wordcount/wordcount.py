import json
from argparse import ArgumentParser


def wordcount(filename, save_name):
    """Return number of words in file."""

    with open(filename, "r") as f:
        data = f.read()
        words = data.split()

        num_words = len(words)

    with open(f"{save_name}.json", "w") as g:
        json.dump({"num_words": num_words}, g)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--textfile", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    wordcount(args.textfile, args.name)
