#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import re
import click
import socket
import sys
import requests
import json
from requests import ConnectionError
from lxml import html
from datetime import datetime


def internet_connection(server: str = "www.google.com", port: int = 80):
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.settimeout(5)
  try:
    sock.connect((server, port))
    return True
  except socket.error:
    return False
  finally:
    sock.close()

def validate(url: str):
  url_regex="^(https?://)?(www\.)?goodreads\.com(/[^/]{2}(-[^/]{2})?)?/book/show/\d+$"
  if not re.match(url_regex, url):
    click.echo(f'\x1b[31;1mInvalid  "{url}". Must match regex "{url_regex}"\x1b[0m')
    sys.exit(1)
  return url

def _real_main(url: str, UserAgent = None):
  data = {}
  request = requests.get(
    url,
    headers={
      "User-Agent": "" if UserAgent is None else UserAgent
    })
  if not request.ok:
    raise ValueError(f"{url} is invalid. Got HTTP {request.status_code} {request.reason}.")
  tree = html.fromstring(request.text)
  main_data = json.loads([td.text for td in tree.xpath("//script[@id=\"__NEXT_DATA__\"][@type=\"application/json\"]")][0])
  page_data = json.loads([td.text for td in tree.xpath("//script[@type=\"application/ld+json\"]")][0])

  data['raw'] = {"main": main_data, "page": page_data}
  data['legacy_id'] = main_data['props']['pageProps']['params']['book_id']
  data['book_id'] = main_data['props']['pageProps']['apolloState']['ROOT_QUERY'][f'getBookByLegacyId({{"legacyId":"{data["legacy_id"]}"}})']['__ref']
  data['work_id'] = main_data['props']['pageProps']['apolloState'][f"{data['book_id']}"]['work']['__ref']
  data['title'] = main_data['props']['pageProps']['apolloState'][f"{data['book_id']}"]['titleComplete']
  data['title_short'] = main_data['props']['pageProps']['apolloState'][f"{data['book_id']}"]['title']
  data['description'] = main_data['props']['pageProps']['apolloState'][f"{data['book_id']}"]['description']
  data['image'] = main_data['props']['pageProps']['apolloState'][f"{data['book_id']}"]['imageUrl']
  data['publisher'] = main_data['props']['pageProps']['apolloState'][f"{data['book_id']}"]['details']['publisher']
  date_published = datetime.utcfromtimestamp(main_data['props']['pageProps']['apolloState'][f"{data['book_id']}"]['details']['publicationTime']/1000)
  data['publication_date'] = {
    "day": date_published.day,
    "month": date_published.month,
    "year": date_published.year
  }
  data['format'] = main_data['props']['pageProps']['apolloState'][f"{data['book_id']}"]['details']['format']
  data['pages'] = main_data['props']['pageProps']['apolloState'][f"{data['book_id']}"]['details']['numPages']
  data['lang'] = main_data['props']['pageProps']['apolloState'][f"{data['book_id']}"]['details']['language']['name']
  data['asin'] = main_data['props']['pageProps']['apolloState'][f"{data['book_id']}"]['details']['asin']
  data['isbn'] = main_data['props']['pageProps']['apolloState'][f"{data['book_id']}"]['details']['isbn']
  data['isbn13'] = main_data['props']['pageProps']['apolloState'][f"{data['book_id']}"]['details']['isbn13']
  data['rating'] = main_data['props']['pageProps']['apolloState'][f"{data['work_id']}"]['stats']['averageRating']
  data['ratings'] = main_data['props']['pageProps']['apolloState'][f"{data['work_id']}"]['stats']['ratingsCount']
  data['reviews'] = main_data['props']['pageProps']['apolloState'][f"{data['work_id']}"]['stats']['textReviewsCount']
  """
  To be done:
    series
    generes
    ratings/star
    reviews/star
  """
  return data


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("book", type=str)
def main( str):
  """
  Get information on over 1,000,000+ books right from the terminal.
  """
  
  book = validate(book)

  # Check if the user is connected to the internet
  if not internet_connection():
    click.echo("Please connect to the internet to use the Goodreads-Scrapper.")
    raise
  
  print(_real_main(book))



if __name__ == "__main__":
  sys.exit(main())