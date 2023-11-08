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
    click.echo(f'\x1b[31;1mInvalid book: "{url}". Must match regex "{url_regex}"\x1b[0m')
    sys.exit(1)
  return url

def _real_main(url: str, UserAgent = None):
  data = {}
  request = requests.get(
    url,
    headers={
      "User-Agent": "" if UserAgent is None else UserAgent
    })
  if 400<=request.status_code<=599:
    raise ValueError(f"{url} is invalid. Got HTTP {request.status_code} {request.reason}.")
  tree = html.fromstring(request.text)
  main_data = json.loads([td.text for td in tree.xpath("//script[@id=\"__NEXT_DATA__\"][@type=\"application/json\"]")][0])
  page_data = json.loads([td.text for td in tree.xpath("//script[@type=\"application/ld+json\"]")][0])

  data['raw'] = {"main": main_data, "page": page_data}
  data['name'] = page_data['main']
  data['image'] = page_data['image']
  data['format'] = page_data['bookFormat']
  data['pages'] = page_data['numberOfPages']
  data['lang'] = page_data['inLanguage']
  data['isbn'] = page_data['isbn']
  data['rating'] = page_data['ratingValue']
  data['ratings'] = page_data['ratingCount']
  data['reviews'] = page_data['reviewCount']
  return data


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("book", type=str)
def main(book: str):
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