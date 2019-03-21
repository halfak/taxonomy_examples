import json
import re

import mwapi
import mwparserfromhell

MW_HOST = "https://en.wikipedia.org"
VITAL_1000_PAGE = "Wikipedia:Vital_articles"
HEADER_RE = re.compile(r"(\w+) \([0-9]+ articles?\)")


session = mwapi.Session(
    MW_HOST,
    user_agent="ahalfaker@wikimedia.org -- vital articles scan")


def get_page_text(page_name):
    response_doc = session.get(action="query", prop="revisions",
                               rvprop="content", rvslots="main",
                               titles=page_name, formatversion=2)
    page_doc = response_doc['query']['pages'][0]
    return page_doc['revisions'][0]['slots']['main']['content']


def normalize_section_name(name):
    return " ".join(str(name).split(" ")[:-2])


# Create the taxonomy from the vital articles page.
vital_text = get_page_text(VITAL_1000_PAGE)
parsed_text = mwparserfromhell.parse(vital_text)
taxonomy = {}
for main_section in parsed_text.get_sections(levels=[2]):
    section_name = str(main_section.get(0).title)
    base_name = normalize_section_name(section_name)
    taxonomy[base_name] = {}
    for sub_section in main_section.get_sections(levels=[3]):
        sub_name = str(sub_section.get(0).title)
        sub_base_name = normalize_section_name(sub_name)
        taxonomy[base_name][sub_base_name] = []
        for link in sub_section.ifilter_wikilinks():
            if "Vital articles" not in str(link.title):
                page_name = str(link.title)
                # Wikitext to the page
                text = get_page_text(page_name)
                taxonomy[base_name][sub_base_name].append(
                    {'page_name': page_name, 'text': text})


print(json.dumps(taxonomy, indent=2))
