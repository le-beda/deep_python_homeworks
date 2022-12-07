import scrapy
from urllib.parse import urlencode
from urllib.parse import urljoin
import re
import json

from spider_steam.items import SpiderSteamItem

queries = ["horror", "dating simulator", "non competitive"]


class SteamSpider(scrapy.Spider):
    name = 'SteamSpider'

    def start_requests(self):
        for query in queries:
            for page in range(1, 3):
                url = "https://store.steampowered.com/search/?term={0}&page={1}".format(re.sub(" ", "+", query), page)
                yield scrapy.Request(url=url, callback=self.parse_keyword_response)

    def parse_keyword_response(self, response):
        products = response.xpath('//div[@id="search_resultsRows"]/a/@href').extract()

        for product_url in products:
            yield scrapy.Request(url=product_url, callback=self.parse_product_page)

    def parse_product_page(self, response):
        items = SpiderSteamItem()

        title = response.xpath('//head/title/text()').extract()
        category = response.xpath(
            '//div[@class = "page_title_area game_title_area page_content"]/div[@class = "breadcrumbs"]/div[@class = "blockbg"]/a//text()').extract()

        review_count = response.xpath(
            '//div[@id = "userReviews"]/div[@class = "user_reviews_summary_row"]/div[@class = "summary column"]/span[@class = "responsive_hidden"]//text()').extract()
        review_score = response.xpath(
            '//div[@id = "userReviews"]/div[@class = "user_reviews_summary_row"]/div[@class = "summary column"]/span[@class = "nonresponsive_hidden responsive_reviewdesc"]//text()').extract()
        release_date = response.xpath('//div[@class = "release_date"]/div[@class = "date"]//text()').extract()
        developer = response.xpath('//div[@class = "dev_row"]/div[@class = "summary column"]/a//text()').extract()
        tags = response.xpath(
            '//div[@class = "glance_tags_ctn popular_tags_ctn"]/div[@class = "glance_tags popular_tags"]//text()').extract()
        price = response.xpath(
            '//div[@class = "game_purchase_action_bg"]/div[@class = "game_purchase_price price"]//text()').extract()
        available_platforms = response.xpath('//div[@class = "game_area_purchase_platform"]/span/@class').extract()

        items['title'] = title[0].strip()
        items['category'] = '/'.join(map(lambda x: x.strip(), category[:-1]))
        items['review_count'] = review_count[0].strip()[1:-1]
        items['review_score'] = review_score[0].strip()[2:]
        items['release_date'] = release_date[0].strip()
        items['developer'] = developer[0].strip()
        items['tags'] = ', '.join(map(lambda x: x.strip(), tags[1:-1]))
        items['price'] = ' or '.join(map(lambda x: x.strip(), price))
        items['available_platforms'] = ' '.join(set(map(lambda x: x.strip().split()[-1], available_platforms)))

        yield items
