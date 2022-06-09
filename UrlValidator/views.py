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
    return render(request, "urlvalidator/urls.html", context={"broken_links": scrape.broken_links})


def index(request):
    return render(request, "urlvalidator/frontpage.html")


class Scrape:
    searched_links = []
    broken_links = []

    @staticmethod
    def get_links_from_html(html):
        def get_link(el):
            return el["href"]
        return list(map(get_link, BeautifulSoup(html, features="html.parser").select("a[href]")))

    def find_broken_links(self, domain_to_search, check_url, parent_url):
        if (not (check_url in self.searched_links)) and (not check_url.startswith("mailto:")) and (not ("javascript:" in check_url)) and (
                not check_url.endswith(".png")) and (not check_url.endswith(".jpg")) and (not check_url.endswith(".jpeg")):
            try:
                request_obj = requests.get(check_url)
                self.searched_links.append(check_url)
                if request_obj.status_code == 404:
                    self.broken_links.append("BROKEN: link " + check_url + " from " + parent_url)
                    # print(self.broken_links[-1])
                else:
                    # print("NOT BROKEN: link " + URL + " from " + parentURL)
                    if urlparse(check_url).netloc == domain_to_search:
                        for link in self.get_links_from_html(request_obj.text):
                            self.find_broken_links(domain_to_search, urljoin(check_url, link), check_url)
            except Exception as e:
                self.searched_links.append(domain_to_search)
