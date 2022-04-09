# -*- coding: utf-8 -*-

import argparse
import os
import time
import urllib

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from slacker import Slacker


USERNO = os.environ.get("DR_USERNO")
USERNAME = os.environ.get("DR_USERNAME")
PASSWORD = os.environ.get("DR_PASSWORD")

ARN = os.environ.get("DR_ARN", "arn")
TARGET = os.environ.get("DR_TARGET", "tt")
LEAGUE = os.environ.get("DR_LEAGUE", "league")
SEASON = os.environ.get("DR_SEASON", "season")
MODEL = os.environ.get("DR_MODEL", "model")

SLACK_TOKEN = os.environ.get("DR_SLACK_TOKEN", "")
SLACK_CHANNEL = os.environ.get("DR_SLACK_CHANNEL", "#sandbox")


def parse_args():
    p = argparse.ArgumentParser(description="deepracer submit")
    p.add_argument("--userno", default=USERNO, help="userno")
    p.add_argument("--username", default=USERNAME, help="username")
    p.add_argument("--password", default=PASSWORD, help="password")
    p.add_argument("-a", "--arn", default=ARN, help="arn")
    p.add_argument("-t", "--target", default=TARGET, help="target")
    p.add_argument("-l", "--league", default=LEAGUE, help="league")
    p.add_argument("-s", "--season", default=SEASON, help="season")
    p.add_argument("-m", "--model", default=MODEL, help="model")
    p.add_argument("--slack-token", default=SLACK_TOKEN, help="slack token")
    p.add_argument("--slack-channel", default=SLACK_CHANNEL, help="slack channel")
    return p.parse_args()


def open_browser(args):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    # options.add_argument("--no-sandbox")
    # options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")

    browser = webdriver.Chrome(options=options)

    # browser = webdriver.Chrome("/usr/local/bin/chromedriver")

    browser.set_window_size(1600, 1700)

    return browser


def colse_browser(args, browser):
    try:
        browser.close()
    except Exception as ex:
        print("Error", ex)


def login_aws(args, browser):
    print("login_aws", args.username)

    url = "https://{}.signin.aws.amazon.com/console".format(args.userno)

    browser.get(url)

    time.sleep(5)

    browser.save_screenshot("build/login-{}.png".format(args.target))

    browser.find_element(By.ID, "username").send_keys(args.username)
    browser.find_element(By.ID, "password").send_keys(args.password)

    browser.find_element(By.ID, "signin_button").click()

    time.sleep(5)

    browser.save_screenshot("build/login-{}.png".format(args.target))


def submit_model(args, browser):
    print("submit_model", args.model)

    # #league/arn%3Aaws%3Adeepracer%3Aus-east-1%3A%3Aleaderboard%2Fvirtual-season-2020-05-tt/submitModel

    # #league/arn%3Aaws%3Adeepracer%3A%3A%3Aleaderboard%2F55234c74-2c48-466d-9e66-242ddf05e04d/submitModel

    # #competition/arn%3Aaws%3Adeepracer%3A%3A082867736673%3Aleaderboard%2Fe9fbfc93-ed99-494c-8b61-ac13a2274859/submitModel

    arn = urllib.parse.quote_plus(args.arn)

    url = "https://console.aws.amazon.com/deepracer/home?region=us-east-1#{}/{}{}/submitModel".format(
        args.league, arn, args.season
    )

    try:
        browser.get(url)

        time.sleep(5)

        browser.save_screenshot("build/submit-{}.png".format(args.target))

        browser.find_element(By.CLASS_NAME, "awsui-dropdown-trigger").click()

        path = '//*[@title="{}"]'.format(args.model)
        browser.find_element(By.XPATH, path).click()

        browser.find_element(By.CLASS_NAME, "awsui-button-variant-primary").click()

        time.sleep(10)

        browser.save_screenshot("build/submit-{}.png".format(args.target))
    except Exception as ex:
        print("Error", ex)

    post_slack(args, "submit")


def post_slack(args, step):
    print("post_slack")

    if args.slack_token == "":
        return

    millis = int(round(time.time() * 1000))

    file = "{}/build/{}-{}.png".format(os.getcwd(), step, args.target)
    text = "{} : {} : {} : {}".format(args.target, args.model, step, millis)

    try:
        slack = Slacker(args.slack_token)

        slack.files.upload(file, channels=[args.slack_channel], title=text)

    except KeyError as ex:
        print("Environment variable %s not set." % str(ex))


def main():
    args = parse_args()

    if args.userno == "":
        return

    browser = open_browser(args)

    login_aws(args, browser)

    submit_model(args, browser)

    colse_browser(args, browser)


if __name__ == "__main__":
    main()
