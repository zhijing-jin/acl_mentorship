The script is to extract a list of **junior researchers in NLP** based on [ACL anthology](https://www.aclweb.org/anthology/). The repo is curated and maintained by [Zhijing Jin](http://zhijing-jin.com) (an enthusiastic PhD student in NLP).

We use a tentative **filter** to extract authors who

1. have not published *ACL papers as first authors,
1. BUT have published at non-*ACL venues but also recorded on ACL anthology (e.g., workshops, LREC, etc), OR as non-first authors on *ACL papers,
1. AND have at least 1 ACL anthology entry within 3 years,
1. AND earliest publication date is within 3 years, AND total number of papers <= 3.


Feel free to make [pull requests](pulls/) if you have suggestions to improve the code.

#### Configure the Environment

```bash
git clone https://github.com/zhijing-jin/acl_mentorship.git
cd acl_mentorship

git clone https://github.com/acl-org/acl-anthology
pip -r install acl-anthology/bin/requirements.txt
mv extract_junior_authors.py acl-anthology/bin/extract_junior_authors.py
```

#### How to Run

```bash
python acl-anthology/bin/extract_junior_authors.py
```

#### Quality Check

We manually inspected the quality of a random sample. Among our extracted researcher names:

- Total Number (by Mar 2021): 11,021 authors 
- 45%: Students / Recent graduates
- 30%: Non-academia scientists beginning to publish
- 25%: Interdisciplinary/Other senior researchers beginning to publish at NLP venues


#### Credits

- Thanks a lot for the [Gist code](https://gist.github.com/mjpost/c1984462bacfb4012a57520c13a08e26) of Prof [Matt Post](https://matt.waypost.net/) (Johns Hopkins University)