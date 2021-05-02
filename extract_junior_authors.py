'''
The script is to extract a list of junior researchers.

A tentative filter is authors who
(1) have not published *ACL papers as first authors,
(2) BUT have published at non-*ACL venues but also recorded on ACL anthology (e.g., workshops, LREC, etc), OR as non-first authors on *ACL papers,
(3) AND have at least 1 ACL anthology entry within 3 years,
(4) AND earliest publication date is within 3 years, AND total number of papers <= 3.

git clone https://github.com/acl-org/acl-anthology
pip install acl-anthology/bin/requirements.txt
mv extract_junior_authors.py acl_anthology/bin/
python acl-anthology/bin/extract_junior_authors.py


Author: Zhijing Jin
Date: Mar 13, 2021

Credits to Prof Matt Post https://gist.github.com/mjpost/c1984462bacfb4012a57520c13a08e26
'''

import os
import sys

from anthology import Anthology
from anthology.utils import deconstruct_anthology_id


class ConferenceIDFilter:
    # Namings of the ACL collections: (check `acl-anthology/data/xml/*.xml`)
    conf_top3_abbr = ['acl', 'emnlp', 'naacl']
    conf_abbr2A = {
        'coling': 'C',
        'emnlp': 'D',
        'eacl': 'E',
        'cljournal': 'J',
        'conll': 'K',
        'lrec': 'L',
        'naacl': 'N',
        'acl': 'P',
        'tacl': 'Q',
        'semeval': 'S',
    }

    @staticmethod
    def get_recent_years(num_years=3):
        from datetime import datetime
        dt = datetime.now()
        this_year = dt.year

        recent_years = list(range(this_year - num_years + 1, this_year + 1))
        recent_years = list(map(str, recent_years))
        return recent_years

    def _get_regex_matcher_recent_confs(self, recent_years):
        import re
        recent_years_yy = [i[-2:] for i in recent_years]

        # patt1 example: "2020.acl"
        patt1 = '({YYYY})\.*'.format(YYYY='|'.join(recent_years))
        # patt2 example: "P18" which stands for ACL 2018
        patt2 = '[A-Z]({yy})$'.format(yy='|'.join(recent_years_yy))

        patt = r'^((({patt2})|({patt1})))'.format(patt1=patt1, patt2=patt2)

        matcher = lambda i: bool(re.match(patt, i))

        # TEST CASES
        #
        # os.system('pip install efficiency')
        # from efficiency.log import show_var
        # for a in ['P19', 'J19', 'J25', 'J08', 'P21..', '000J19', '2019.acl', '2019.eacl', '2019.aclxx',
        #           '2017.acl']:
        #     show_var(['a','matcher(a)'])
        # import pdb;
        # pdb.set_trace()
        return matcher

    def _get_regex_matcher_recent_top3_confs(self, recent_years):
        import re

        # bool(re.match(r'^(2019|2020|2021)\.(acl|emnlp|naacl)$', a))
        patt1 = '({YYYY})\.({conf_abbr})'.format(
            YYYY='|'.join(recent_years),
            conf_abbr='|'.join(self.conf_top3_abbr))

        recent_years_yy = [i[-2:] for i in recent_years]
        conf_A = [self.conf_abbr2A[i] for i in self.conf_top3_abbr]
        # bool(re.match(r'^(N|P|D)(19|20|21)$', a))
        patt2 = '({conf_A})({yy})'.format(yy='|'.join(recent_years_yy),
                                          conf_A='|'.join(conf_A))

        # bool(re.match(r'^((((N|P|D)(19|20|21))|((2019|2020|2021)\.(acl|emnlp|naacl))))$', a))
        patt = r'^((({patt2})|({patt1})))$'.format(patt1=patt1, patt2=patt2)

        matcher = lambda i: bool(re.match(patt, i))

        # TEST CASES
        #
        # os.system('pip install efficiency')
        # from efficiency.log import show_var
        #
        # regex_top3 = r'^((((P|D|N)(19|20|21))|((2019|2020|2021)\.(acl|emnlp|naacl))))$'
        # if patt != regex_top3:
        #     show_var(['patt', 'regex_top3'])
        #     import pdb;
        #     pdb.set_trace()
        # for a in ['P19', 'J19', '2019.acl', '2019.eacl',  '2019.aclxx', 'P21..', '2017.acl']:
        #     show_var(['a','matcher(a)'])
        # import pdb;
        # pdb.set_trace()

        return matcher

    def get_conf_ids(self, anth_dir, recent_num_years=3):
        xml_suffix = '.xml'
        conf_ids = [i[:-len(xml_suffix)] for i in os.listdir(anth_dir + '/xml/')
                    if i.endswith(xml_suffix)]

        years = self.get_recent_years(num_years=recent_num_years)
        matcher_recent_confs = self._get_regex_matcher_recent_confs(years)
        matcher_recent_top3 = self._get_regex_matcher_recent_top3_confs(years)

        recent_confs = list(filter(matcher_recent_confs, conf_ids))
        recent_confs_top3 = set(filter(matcher_recent_top3, conf_ids))
        recent_confs_non_top3 = set(recent_confs) - set(recent_confs_top3)

        return recent_confs_top3, recent_confs_non_top3


class PaperLookup:
    def __init__(self, anthology):
        from collections import defaultdict

        self.paper_id2year = defaultdict(str)
        self.paper_id2url = defaultdict(str)
        for id_, paper in anthology.papers.items():
            year = paper.attrib.get('year', '')
            url = paper.attrib.get('url', '')
            self.paper_id2url[id_] = url
            self.paper_id2year[id_] = year

    def get_year(self, paper_id):
        return self.paper_id2year[paper_id]

    def get_url(self, paper_id):
        return self.paper_id2url[paper_id]

class Author2Paper:
    @staticmethod
    def get_papers_of_author(author, anthology):
        nested_paper_list = list(
            anthology.people.name_to_papers[author[0]].values())
        # nested_paper_list is a nested list, so we flatten it
        paper_list = nested_paper_list[0] + nested_paper_list[1]

        return paper_list

def get_junior_authors(args, verbose=False):
    this_python_file = sys.argv[0]
    anth_dir = os.path.join(os.path.dirname(this_python_file), "..", "data")

    # Step 1. Get conference IDs, e.g., "2020.acl", "P18", etc.
    conf_ids_top3, conf_ids_non_top3 = ConferenceIDFilter(). \
        get_conf_ids(anth_dir, recent_num_years=args.recent_num_years)

    # Step 2. Parse all anthology entries in `acl-anthology/data/`
    anthology = Anthology(importdir=anth_dir)

    # Step 3. "Include" authors who have published in recent 3 years
    # (1) a non-first-author paper at *ACL conferences
    # (2) Or a paper at non-*ACL conferences
    #
    # "Exclude" authors who have been
    # (1) at least once in recent 3 years a first author at *ACL conferences
    include = []
    exclude = []
    for id_, paper in anthology.papers.items():
        collection_id, volume_name, paper_id = deconstruct_anthology_id(id_)
        authors = paper.attrib.get("author", [])
        if not len(authors):
            continue
        if collection_id in conf_ids_top3:
            # "authors" is a list of ("last name || first name", name-id or None) tuples
            # e.g., [(Frank K. || Soong, None), (Eng-Fong || Huang, None)]
            first_author = authors[0]
            exclude.append(first_author)

            include.extend(authors[1:])

            # print(first_author.full, id_, paper.get_title('text'), sep="\t")
        elif collection_id in conf_ids_non_top3:
            include.extend(authors)

    exclude = set(exclude)
    include = set(include) - exclude

    # Step 4. Finally, "Exclude" authors
    # (2) whose earliest paper is more than 3 years ago
    # (3) OR whohave more than 3 papers in the anthology
    paper_lookup = PaperLookup(anthology)
    for author in include:
        paper_list = Author2Paper.get_papers_of_author(author, anthology)

        years = [paper_lookup.get_year(i) for i in paper_list]
        earliest = min(i for i in years if i)
        recent_years = ConferenceIDFilter.get_recent_years(
            num_years=args.years_since_oldest_paper)
        if (earliest not in recent_years) \
                or (len(paper_list) > args.max_num_papers):
            exclude.add(author)

    junior_authors = list(include - exclude)
    print()
    print('------------------')
    print('# Possible Junior Authors:', len(junior_authors))

    all_names = [i[0].full
                 for i in sorted(junior_authors, key=lambda i: i[0].last)]
    with open(args.output_file, 'w') as f:
        f.write('\n'.join(all_names))
        print('[Info] Saved {} author names to {}'.format(len(all_names), args.output_file))

    dict_list = []
    for author in junior_authors:
        paper_list = Author2Paper.get_papers_of_author(author, anthology)
        paper_list = sorted(paper_list)
        dict_item = {'id': author[0].id_, 'name': author[0].full}
        dict_item.update({'paper_{}'.format(i): paper_lookup.get_url(paper)
                          for i, paper in enumerate(paper_list)})
        dict_list.append(dict_item)
    # from efficiency.log import write_dict_to_csv
    write_dict_to_csv(dict_list, args.file_author2papers, verbose=True)

    if verbose:
        import random

        random.shuffle(junior_authors)
        sample = junior_authors[:20]
        sample_names = [i[0].full for i in sample]
        print('[Info] A random set of (possible) junior authors:')
        print('\n'.join(sample_names))

    return all_names


def write_dict_to_csv(data, file, verbose=False):
    if verbose:
        print('[Info] Writing {} lines into {}'.format(len(data), file))

    import csv

    if not len(data): return

    fieldnames = ['id', 'name', 'paper_0', 'paper_1', 'paper_2', 'paper_3']
    with open(file, mode='w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def main():
    import argparse

    parser = argparse.ArgumentParser('Specs about how to extract the junior author names from ACL anthology')
    parser.add_argument("-output_file", default='junior_authors.txt')
    parser.add_argument("-file_author2papers", default='junior_authors_n_papers.csv')
    parser.add_argument("-max_num_papers", type=int, default=3)
    parser.add_argument("-years_since_oldest_paper", type=int, default=3)
    parser.add_argument("-recent_num_years", type=int, default=3)
    args = parser.parse_args()

    print('[Info] Extracting junior authors from ACL Anthology in recent {} years'.format(args.recent_num_years))
    print('[Info] Author list will be saved to', args.output_file)
    print('[Info] Author-to-papers list will be saved to', args.file_author2papers)
    print('... ...')

    junior_author_names = get_junior_authors(args, verbose=False)


if __name__ == "__main__":
    main()
