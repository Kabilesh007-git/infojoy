from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
from processing_unit import rg
from downloader import MovieDownloader
import time
import os
from threading import Thread, Lock
import traceback
from downloader import MovieDownloader