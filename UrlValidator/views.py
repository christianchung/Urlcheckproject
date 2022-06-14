import hashlib
import os
import re
import time
from pathlib import Path

from bs4.dammit import EncodingDetector
from django.http import JsonResponse
from django.shortcuts import render
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse
from urllib.parse import urljoin
import multiprocessing as mp


def get_scrape(request):
    address = request.GET["address"]
    job_queue = mp.Queue()
    manager = mp.Manager()
    searched = manager.list()
    broken = manager.list()
    jobs = []
    job_queue.put({"url": address, "parent": address})
    for i in range(os.cpu_count() - 1):
        p = Worker(job_queue, urlparse(address).netloc, searched, broken)
        jobs.append(p)
        p.start()
    for j in jobs:
        j.join()
    return JsonResponse({"broken_links": list(broken)})


def index(request):
    return render(request, "urlvalidator/frontpage.html")


class Worker(mp.Process):

    def __init__(self, job_queue, domain, searched, broken):
        super().__init__()
        self.job_queue = job_queue
        self.searched = searched
        self.broken = broken
        self.domain = domain

    @classmethod
    def get_links_from_html(cls, html):
        def get_link(el):
            return el["href"]

        return list(map(get_link, BeautifulSoup(html, features="html.parser").select("a[href]")))

    @classmethod
    def link_to_obj(cls, check_url, parent_url, status_code):
        return {
            'url': check_url,
            'parent_url': parent_url,
            'status_code': status_code
        }

    def run(self):
        while True:
            if self.job_queue.empty():
                time.sleep(3)
                if self.job_queue.empty():
                    break
            queue = self.job_queue.get()
            url = queue["url"]
            parent = queue["parent"]
            if (not (url in self.searched)) and (not url.startswith("mailto:")) and (
                    not ("javascript:" in url)) and (
                    not url.endswith(".png")) and (not url.endswith(".jpg")) and (
                    not url.endswith(".jpeg")):
                self.searched.append(url)
                try:
                    page = requests.get(url, timeout=3, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'
                    })
                    if page.status_code > 299:
                        self.broken.append(self.link_to_obj(url, parent, page.status_code))
                    else:
                        if urlparse(url).netloc == self.domain:
                            for link in self.get_links_from_html(page.text):
                                self.job_queue.put({"url": urljoin(url, link), "parent": url})
                except requests.RequestException:
                    pass
        self.close()
