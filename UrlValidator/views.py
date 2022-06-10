from django.http import JsonResponse
from django.shortcuts import render
import requests
import sys
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import urljoin


def get_scrape(request):
    address = request.GET["address"]
    scrape = Scrape()
    scrape.find_broken_links(urlparse(address).netloc, address, "")
    return JsonResponse({"broken_links": scrape.broken_links})


def index(request):
    return render(request, "urlvalidator/frontpage.html")


class Scrape:

    def __init__(self):
        self.searched_links = []
        self.broken_links = []
        self.count = 0

    @classmethod
    def get_links_from_html(cls, html):
        def get_link(el):
            return el["href"]
        return list(map(get_link, BeautifulSoup(html, features="html.parser").select("a[href]")))

    @classmethod
    def link_to_obj(cls, check_url, parent_url,status_code):
        return {
            'url': check_url,
            'parent_url': parent_url,
            'status_code': status_code
        }

    def find_broken_links(self, domain_to_search, check_url, parent_url):
        if (not (check_url in self.searched_links)) and (not check_url.startswith("mailto:")) and (not ("javascript:" in check_url)) and (
                not check_url.endswith(".png")) and (not check_url.endswith(".jpg")) and (not check_url.endswith(".jpeg")):
            try:
                request_obj = requests.get(check_url, timeout=5)
                self.searched_links.append(check_url)
                if request_obj.status_code > 299:
                    self.broken_links.append(self.link_to_obj(check_url, parent_url, request_obj.status_code))
                    self.count += 1
                else:
                    if urlparse(check_url).netloc == domain_to_search:
                        for link in self.get_links_from_html(request_obj.text):
                            self.find_broken_links(domain_to_search, urljoin(check_url, link), check_url)
            except Exception as e:
                self.searched_links.append(domain_to_search)
