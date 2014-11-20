# Intro
Simple Point of Sale (POS) system based on Django. Not for production yet !

# Quickstart
On your terminal, run the following:-

    sudo apt-get install python-dev build-essential libmysqlclient-dev
    git clone https://github.com/k4ml/jazzpos.git
    cd jazzpos
    python bootstrap.py
    ./bin/buildout -v
    ./bin/manage syncdb
    ./bin/manage runserver

# Todos
Lot of things need to be polished up. This originally developed for very
specific client so parts need to be generalized further. Things that I'd
like to pursue:-

* Custom `Customer` model so specific customer data can be put here.
* PDF generation for invoice, receipt and report. Currently pretty rudimentary.
* Upgrade to Django 1.7. This was developed while 1.4 still hot and then left
  dormant in my repository.
* Proper l10n. Currently the main interface is in Malay.
* Add tests !

# Screenshot
## Dashboard
<a href="http://imgur.com/t4iaM9Y"><img src="http://i.imgur.com/t4iaM9Yl.png" title="source: imgur.com" /></a><br />

## Order page
<a href="http://imgur.com/QlOO16g"><img src="http://i.imgur.com/QlOO16gl.png" title="source: imgur.com" /></a>
