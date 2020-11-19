import scrapy
import socket
import datetime

from scrapy_splash import SplashRequest
from scrapy.http import Request
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose
from ..items import ArticleItem

script = """
function main(splash, args)
  splash.private_mode_enabled = false
  assert(splash:go(splash.args.url))
  link_id = args
  local link = splash:select_all('#'..args.link_id)[1]
  link:mouse_click()
  assert(splash:wait(10))
  return {
    url = splash:url(),
    cookies = splash:get_cookies(),
    html = splash:html(),
  }
end
"""
scriptpage = """
function main(splash, args)
  splash.private_mode_enabled = false
  assert(splash:go(splash.args.url))
  link_id = args
  local link = splash:select_all('#'..args.link_id)[1]
  link:mouse_click()
  assert(splash:wait(10))
  return {
    url = splash:url(),
    cookies = splash:get_cookies(),
    html = splash:html(),
  }
end
"""
scriptview = """
function main(splash, args)
  splash.private_mode_enabled = false
  assert(splash:go(splash.args.url))
  local link = splash:select_all('input.view-poster')[1]
  link:mouse_click()
  assert(splash:wait(10))
  return {
    url = splash:url(),
    cookies = splash:get_cookies(),
    html = splash:html(),
  }
end
"""
class MNullSciSpider(scrapy.Spider):
    name = 'm_null_sci'
    allowed_domains = ['sciencedirect.com']
    start_urls = ['https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=1'
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=2',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=3',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=4',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=5',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=6',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=7',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=8',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=9',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=10',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=11',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=12',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=13',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=14',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=15',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=16',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=17',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=18',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=19',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=20',
                  # 'https://www.sciencedirect.com/journal/annals-of-oncology/vol/29/suppl/S8?page=21'
                  ]

    http_user = '2f8c2133bb4e4b62a84114d540197dfe'

    custom_settings = {
        # 'FILES_STORE': 'output/files',
        # 'IMAGES_STORE': 'output/images',
        # 'FEED_URI': 'output/feeds/%(name)s/%(time)s.json',
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter',
        'DOWNLOAD_DELAY': 3,
        'COOKIES_ENABLED': True,
        'CRAWLERA_ENABLED': False,
    }

    def start_requests(self):
        for i in range(0, len(self.start_urls)):
            url = self.start_urls[i]
            yield scrapy.Request(url=url,
                                 callback=self.parse,
                                 # meta={'mid': self.mid[i], 'eid': self.eid[i]}
                                 )

    def parse(self, response):
        self.log('parse')
        print(response.url)
        # mid = response.meta['mid']
        # eid = response.meta['eid']

        yield from self.parse_list(response)

        page_info = response.css('span.pagination-pages-label::text').re('\d+')
        if page_info:
            current_page = page_info[0]
            page_size = page_info[1]
            for page in range(2, int(page_size)):
                url = f'{response.url}?page={page}'
                print(url)
                yield Request(
                    url,
                    callback=self.parse_list,
                    # meta={'mid': mid, 'eid': eid}
                )

    def parse_list(self, response):
        self.log('parse_list')
        # mid = response.meta['mid']
        # eid = response.meta['eid']
        for url in response.css('a.anchor.article-content-title::attr(href)').extract():
            url = response.urljoin(url)
            yield Request(
                url,
                callback=self.parse_item,
                # meta={'mid': mid, 'eid': eid}
            )

    def parse_item(self, response):

        l = ItemLoader(item=ArticleItem(), response=response)

        # print(response.css('#body'))

        l.add_css('title', 'span.title-text::text', MapCompose(str.strip))
        l.add_css('authors', '.content > span ::text', MapCompose(str.strip))
        l.add_css('doi', '.doi::attr(href)')
        l.add_css('body', '#body', MapCompose(str.strip))
        l.add_css('affiliations', '#author-group > dl', MapCompose(str.strip))
        # doi = response.css('div#doi-link > a.doi::attr(href)').get()
        # l.add_value('doi', doi)

        l.add_value('detail_url', response.url)

        file_urls = [response.url]
        for pdf_url in response.css('a.link-button.u-margin-s-bottom.link-button-primary::attr(href)').extract():
            pdf_url = response.urljoin(pdf_url),
            file_urls.append(pdf_url)
        l.add_value('file_urls', file_urls)

        # image_urls = [response.urljoin(url) for url in
        #               response.css('#genesis-content > p:nth-child(n) > img::attr(src)').extract()]
        # l.add_value('image_urls', image_urls)

        l.add_value('sid', 9836)
        l.add_value('eid', 20929)
        l.add_value('mid', 20929)
        l.add_value('project', self.settings.get('BOT_NAME'))
        l.add_value('spider', self.name)
        l.add_value('server', socket.gethostname())
        l.add_value('date', datetime.datetime.utcnow())

        yield l.load_item()
