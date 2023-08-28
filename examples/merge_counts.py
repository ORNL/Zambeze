
import json
from argparse import ArgumentParser


def wordcount(countfiles):
    """Return number of words in file."""

    titles = []
    total_words = 0

    for filename in countfiles:

        titles.append(filename.split('.')[0])
        with open(filename, 'r') as f:
            data = json.load(f)
            total_words += int(data['num_words'])

    with open(f"wordcount_summary.txt", 'w') as g:
        g.write(f"The total wordcount from these books: \n"
                f"{', '.join(titles)} \n" 
                f"is {total_words}")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--countfiles", nargs="+", required=True)
    args = parser.parse_args()

    wordcount(args.countfiles)