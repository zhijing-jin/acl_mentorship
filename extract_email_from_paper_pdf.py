'''
Author: Yiwen Ding <dyiwen@umich.edu>
Date: May 2, 2021
'''

import csv
import os
from io import StringIO
from pdfminer3.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer3.converter import TextConverter
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage


def retrieve_url(remote_url: str, local_path: str):
    """
    Saves a URL to a local path. Can handle cookies, e.g., those
    used downloading PDFs from MIT Press (TACL, CL).

    :param remote_url: The URL to download from. Currently supports http only.
    :param local_path: Where to save the file to.
    """
    outdir = os.path.dirname(local_path)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    if remote_url.startswith("http"):
        import ssl
        import urllib.request

        cookieProcessor = urllib.request.HTTPCookieProcessor()
        opener = urllib.request.build_opener(cookieProcessor)
        request = urllib.request.Request(
            remote_url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A'}
        )
        try:
            with opener.open(request, timeout=1000) as url, open(local_path, mode="wb") as input_file_fh:
                try:
                    input_file_fh.write(url.read())
                except ConnectionResetError:
                    return False
            return True
        except urllib.error.HTTPError:
            return False
    else:
        shutil.copyfile(remote_url, local_path)

    return True


def getOverlappingLink(annotationList, element):
    for (x0, y0, x1, y1), url in annotationList:
        if x0 > element.x1 or element.x0 > x1:
            continue
        if y0 > element.y1 or element.y0 > y1:
            continue
        return url
    else:
        return None


def get_pdf_email(pdf_path, author_name):
    pagenums = set()
    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)
    infile = open(pdf_path, 'rb')
    email_address = ""
    for page in PDFPage.get_pages(infile, pagenums):
        try:
            interpreter.process_page(page)
            break
        except AttributeError:
            return email_address
    infile.close()
    converter.close()
    text = output.getvalue()
    output.close()
    keywords = ['@']
    possible_emails = []
    for each_line in text.split('\n'):
        if '@' in each_line:
            possible_emails.append(each_line)
    keywords = author_name.split(' ')

    for email_addr in possible_emails:
        if any(x in email_addr for x in keywords):
            email_address = email_addr
        elif "firstname" in email_addr.lower():
            email_address = email_addr.lower().replace("firstname", keywords[0])
        if "lastname" in email_address:
            email_address = email_address.replace("lastname", keywords[-1])

    if "}" in email_address:
        prefix = email_address.split('}')[0]
        service = email_address.split('}')[1]
        if "," in service:
            temp = service.split(",")[0]
            email_list = service.split(",")[1:-1]
            service = temp
        elif ";" in service:
            temp = service.split(";")[0]
            email_list = service.split(";")[1:-1]
            service = temp
        else:
            email_list = service
        if "{" in prefix:
            prefix = prefix.replace('{', ' ')
        if "," in prefix:
            for each_prefix in prefix.split(','):
                # if "{" in each_prefix:
                #   each_prefix = each_prefix.replace('{','')
                if any(x in each_prefix for x in keywords):
                    email_address = each_prefix + service
                    return email_address
        elif "|" in prefix:
            for each_prefix in prefix.split('|'):
                # if "{" in each_prefix:
                #   each_prefix = each_prefix.replace('{','')
                if any(x in each_prefix for x in keywords):
                    email_address = each_prefix + service
                    return email_address
        else:
            if any(x in prefix for x in keywords):
                email_address = prefix + service
                return email_address
        for each_one in email_list:
            if any(x in each_one for x in keywords):
                email_address = each_one
                return email_address
    if ',' in email_address:
        for each_one in email_address.split(','):
            if any(x in each_one for x in keywords):
                email_address = each_one

    return email_address


def retrieve_email():
    info_list = []
    with open('junior_authors_n_papers.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count != 0:
                author_info = {}
                author_info['id'] = row[0]
                author_info['name'] = row[1]
                author_info['url'] = [row[2], row[3], row[4]]
                info_list.append(author_info)
            line_count += 1
            if line_count > 3600:
                break

    output_list = []
    for each_author in info_list:
        author_name = each_author['name'].lower()
        count = 0
        for each_link in each_author['url']:
            if each_link:
                output_dict = {}
                output_dict["email address"] = []
                output_dict["id"] = each_author["id"]
                output_dict["name"] = author_name
                print(each_link)
                try:
                    have_pdf = retrieve_url(each_link + '.pdf', os.getcwd() + '/' + author_name + str(count) + ".pdf")

                    if have_pdf:
                        # try:
                        email_addr = get_pdf_email(author_name + str(count) + '.pdf', author_name)
                        output_dict["email address"].append(email_addr)
                        # except TypeError or AttributeError:
                        #   pass
                except:
                    output_dict["email address"].append(" ")
            count += 1
        output_list.append(output_dict)

    with open('junior_authors_n_email.csv', mode='w') as csv_file:
        fieldnames = ['id', 'name', 'email address']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        for each_one in output_list:
            if not each_one["email address"]:
                writer.writerow({'id': each_one["id"], 'name': each_one["name"], 'email address': ' '})
            else:
                if "@" in each_one["email address"][-1] and ":" not in each_one["email address"][-1]:
                    writer.writerow({'id': each_one["id"], 'name': each_one["name"],
                                     'email address': each_one["email address"][-1]})
                else:
                    writer.writerow({'id': each_one["id"], 'name': each_one["name"], 'email address': " "})


retrieve_email()

# retrieve_url('https://www.aclweb.org/anthology/2020.acl-main.487.pdf', os.getcwd()+'/' + "Stephen Denuyl" + "0" +".pdf")
# print("email is: ")
# print(get_pdf_email("Stephen Denuyl0.pdf", "Stephen Denuyl"))

# AttributeError: https://www.aclweb.org/anthology/2020.semeval-1.118
# ConnectionResetError: https://www.aclweb.org/anthology/2020.nlp4if-1.4

# pdfminer3.psparser.PSEOF: Unexpected EOF: https://www.aclweb.org/anthology/2020.computerm-1.14
# pdfminer3.pdfparser.PDFSyntaxError: No /Root object! - Is this really a PDF?: https://www.aclweb.org/anthology/W19-4023