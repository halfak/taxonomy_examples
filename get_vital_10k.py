import json
import re
import sys

import mwapi
import mwparserfromhell

MW_HOST = "https://en.wikipedia.org"
VITAL_10K_BASE_PAGE = "Wikipedia:Vital articles/Level/4"
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
    span_name = " ".join(str(name).split(" ")[:-2])
    return span_name.split(">")[-1]


# Get a list of relevant sub-pages.
def get_main_topics(base_page_name):
    base_text = get_page_text(base_page_name)
    parsed_text = mwparserfromhell.parse(base_text)
    main_topics = []
    for link in parsed_text.ifilter_wikilinks():
        if link.title[:33] == VITAL_10K_BASE_PAGE + "/":
            main_topics.append(link.title[33:])

    return main_topics


def get_taxonomy(topic_page_name):
    taxonomy = {}
    base_text = get_page_text(topic_page_name)
    parsed_text = mwparserfromhell.parse(base_text)
    for main_section in parsed_text.get_sections(levels=[2]):
        section_name = str(main_section.get(0).title)
        base_name = normalize_section_name(section_name)
        taxonomy[base_name] = {}
        sub_sections = main_section.get_sections(levels=[3])
        if len(sub_sections) > 0:
            for sub_section in main_section.get_sections(levels=[3]):
                sub_name = str(sub_section.get(0).title)
                sub_base_name = normalize_section_name(sub_name)
                taxonomy[base_name][sub_base_name] = []
                for link in sub_section.ifilter_wikilinks():
                    if "Vital articles" not in str(link.title):
                        page_name = str(link.title)
                        # Wikitext to the page
                        taxonomy[base_name][sub_base_name].append(page_name)
        else:
            taxonomy[base_name]['*'] = []
            for link in main_section.ifilter_wikilinks():
                if "Vital articles" not in str(link.title):
                    page_name = str(link.title)
                    # Wikitext to the page
                    taxonomy[base_name]['*'].append(page_name)

    return taxonomy


main_taxonomy = {}
main_topics = get_main_topics(VITAL_10K_BASE_PAGE)
for topic_name in main_topics:
    topic_page_name = VITAL_10K_BASE_PAGE + "/" + topic_name
    topic_taxonomy = get_taxonomy(topic_page_name)

    main_taxonomy[topic_name] = topic_taxonomy

json.dump(main_taxonomy, sys.stdout, indent=2)
sys.stdout.write("\n")
