#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 18 12:54:02 2018

@author: cznic
"""
import json
import requests
from termcolor import colored, cprint
import argparse
import datetime
import os
import shutil
import configparser
from terminaltables import AsciiTable
import sys
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3.exceptions import SubjectAltNameWarning
import zipfile
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore")
    from gi.repository import Notify
import time


# Suppress warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(SubjectAltNameWarning)

tbl_prev = []  # global variable for contnuous checkinf of jenkins

# text = colored('Hello, World!', 'white', 'on_blue' ) #attrs=['reverse', 'blink'])


class JenkinsTurris:
    def __init__(self, user_id, token, cert_path, key_path, ca_path):
        self._build_uri = ""
        self._job_url_temp = "https://build.turris.cz/job/%s/lastBuild/api/json"
        self.user_id = user_id
        self.token = token
        self.cert_path = cert_path
        self.key_path = key_path
        self.ca_path = ca_path
        self._medata = None
        self._job_metadata = None

    def _get_metadata(self, url):
        resp = requests.get(url,
                            auth=(self.user_id, self.token),
                            cert=(self.cert_path, self.key_path),
                            verify=self.ca_path)
        # resp.status
        if is_json(resp.text):
            return json.loads(resp.text)
        else:
            return None

    def get_job_last_id(self, job_name):
        self._get_job_metadata(job_name)
        return self._job_metadata["id"]

    def _get_job_metadata(self, job_name):
        if self._job_metadata is None or self._job_metadata["fullDisplayName"].split()[0].strip() != job_name:
            url = self._job_url_temp % job_name
            self._job_metadata = self._get_metadata(url)
            return True

    def get_job_status(self, job_name):
        self._get_job_metadata(job_name)
        if self._job_metadata["building"] is True:
            return "BUILDING"
        else:
            return self._job_metadata["result"]

    def get_job_duration(self, job_name):
        self._get_job_metadata(job_name)
        return str(datetime.timedelta(milliseconds=self._job_metadata["duration"]))

    def get_job_estimated_duration(self, job_name):
        self._get_job_metadata(job_name)
        return str(datetime.timedelta(milliseconds=self._job_metadata["estimatedDuration"]))

    def get_job_logs_list(self, job_name, log_type):
        self._get_job_metadata(job_name)
        artifacts = self._job_metadata["artifacts"]
        for artifact in artifacts:
            if artifact["fileName"] == "build.log":
                if log_type == "all":
                    print(artifact["fileName"])
                    print(artifact)
                elif log_type == "nand":
                    if artifact["relativePath"].find("nand") >= 0:
                        print(artifact)
                elif log_type == "initram":
                    if artifact["relativePath"].find("initram") >= 0:
                        print(artifact)

    def _rm_dirs(self, path):
        if os.path.isfile(path):
            shutil.rmtree(path)

    def _rm_file(self, path):
        if os.path.isdir(path):
            shutil.rmtree(path)

    def down_job_logs(self, job_name, log_type):
        base_path = "/home/cznic/data/src/uci_doc/tmp/"
        artifacts = self._job_metadata["artifacts"]
        job_id = self._job_metadata["id"]
        self._rm_dirs(base_path)
        for artifact in artifacts:
            relative_path = artifact["relativePath"]
            self.down_job_file(job_name,
                               job_id,
                               relative_path,
                               base_path)

    def _build_path(self, base_path, relative_path):
        full_path = os.path.join(base_path, relative_path)
        if not os.path.isdir(full_path):
            os.makedirs(full_path)

    def down_job_file(self, job_name, job_id, relative_path, output_dir):
        url_tmp = "https://build.turris.cz/job/%s/%s/artifact/%s"
        full_path = os.path.join(output_dir, relative_path)
        url_full = url_tmp % (job_name, job_id, relative_path)
        resp = requests.get(url_full,
                            auth=(self.user_id, self.token),
                            cert=(self.cert_path, self.key_path),
                            verify=False)
        self._build_path(output_dir, os.path.dirname(relative_path))
        with open(full_path, "w") as fp:
            fp.write(resp.text)

    def down_job_log_arch(self, job_name, job_id, output_file):
        url_temp = "https://build.turris.cz/job/%s/%s/artifact/*zip*/archive.zip"
        url_full = url_temp % (job_name, job_id)
        resp = requests.get(url_full,
                            auth=(self.user_id, self.token),
                            cert=(self.cert_path, self.key_path),
                            verify=self.ca_path,
                            stream=True)
        full_path = output_file
        with open(full_path, "wb") as fp:
            for chunk in resp.iter_content(chunk_size=1024):
                if chunk:
                    fp.write(chunk)
        return full_path

    def extract_arch(self, input_file, output_dir):
        # shutil.unzip(input_file,"-d", output_dir)
        zip_ref = zipfile.ZipFile(input_file, 'r')
        zip_ref.extractall(output_dir)
        zip_ref.close()

    def get_active_builds(self):
        url = "https://build.turris.cz/computer/api/xml?tree=computer[executors[currentExecutable[url]],oneOffExecutors[currentExecutable[url]]]&xpath=//url&wrapper=builds"
        resp = requests.get(url,
                            auth=(self.user_id, self.token),
                            cert=(self.cert_path, self.key_path),
                            verify=self.ca_path)
        try:
            builds_raw = resp.text.replace("<builds>", "").replace("</builds>", "").replace("</url>", "").split("<url>")
            items = [x for x in builds_raw if x]
            ret = []
            for item in items:
                job_name, job_id, _ = item.replace("https://build.turris.cz/job/", "").split("/")
                ret.append({"job_id": job_id, "job_name": job_name})
            return ret
        except:
            return None


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except:
        return False
    return True


def strip_str(text):
    return text.replace("'", "").replace('"', "")


def load_config(config_path=".config"):
    config = configparser.ConfigParser()
    config.read(config_path)
    if "JENKINS" in config.sections():
        user_id = strip_str(config["JENKINS"]["user_id"])
        token = strip_str(config["JENKINS"]["token"])
        cert_path = strip_str(config["JENKINS"]["client_cert_path"])
        key_path = strip_str(config["JENKINS"]["client_key_path"])
        ca_path = strip_str(config["JENKINS"]["server_ca_path"])
        if not os.path.isfile(cert_path):
            raise ValueError('Cert file from config does not exists.',
                             cert_path)
        if not os.path.isfile(key_path):
            raise ValueError('Key file from config does not exists.',
                             key_path)
        if not os.path.isfile(ca_path):
            raise ValueError('CA file from config does not exists.',
                             ca_path)
    else:
        raise ValueError('Config does not have JENKINS section',
                         config_path)
    return {"user_id": user_id,
            "token": token,
            "cert_path": cert_path,
            "key_path": key_path,
            "ca_path": ca_path}


def download_logs(jenkins, job_name, output_dir):
    download_file = "/tmp/logarch/arch.zip"
    if os.path.isdir("/tmp/logarch"):
        shutil.rmtree("/tmp/logarch")
    os.makedirs("/tmp/logarch")
    shutil.rmtree(output_dir)
    job_id = jenkins.get_job_last_id(job_name)
    ret_path = jenkins.down_job_log_arch(job_name, job_id, download_file)
    jenkins.extract_arch(download_file, output_dir)
    tbl = [["Logs downloaded to ", output_dir]]
    table = AsciiTable(tbl)
    print(table.table)
    return ret_path


def print_active_builds(jenkins):
    tbl = [["job id", "job name", "job status", "job duration"]]
    builds = jenkins.get_active_builds()
    if builds:
        for item in builds:
            job_id = item["job_id"]
            job_name = item["job_name"]
            job_status = jenkins.get_job_status(job_name)
            job_estimated_duration = jenkins.get_job_estimated_duration(job_name)
            job_duration = jenkins.get_job_duration(job_name)
            if job_duration == "0:00:00":
                job_duration = job_estimated_duration
            tbl.append([job_id, job_name, job_status, job_duration])
        # colored('Hello, World!', 'white', 'on_blue' )
        table = AsciiTable(tbl)
        print(table.table)
    else:
        print("No active builds.")


def show_notification(head, text):
    Notify.init("Jenkins news!")
    msg = Notify.Notification.new(head, text, "dialog-information")
    msg.set_urgency(Notify.Urgency.CRITICAL)
    msg.show()


def check_build_changes(jenkins):
    global tbl_prev
    tbl_finished = []
    tbl = []
    builds = jenkins.get_active_builds()
    if builds:
        for item in builds:
            job_id = item["job_id"]
            job_name = item["job_name"]
            job_status = jenkins.get_job_status(job_name)
            tbl.append([job_id, job_name, job_status])
    for item_prev in tbl_prev:
        build_finished = True
        for item in tbl:
            if item[0] == item_prev[0]:  # check build id
                build_finished = False
                continue
        if build_finished is True:
            tbl_finished.append(item_prev)
    tbl_prev = tbl  # save state of our build
    return tbl_finished


def wait_build_change(user_id, token, cert_path, key_path, ca_path):
    for i in range(0, 10000):
        time.sleep(20)
        jt = JenkinsTurris(user_id, token, cert_path, key_path, ca_path)
        ret_finished = check_build_changes(jt)
        if ret_finished != []:
            table = AsciiTable(ret_finished)
            show_notification("Finished jenkins jobs.", str(table.table))


def print_job_info(jenkins, job_name):
    tbl = [["Job name", "Status", "Duration"]]
    job_duration = jenkins.get_job_duration(job_name)
    job_estimate_duration = jenkins.get_job_estimated_duration(job_name)
    job_status = jenkins.get_job_status(job_name)
    if job_duration == "0:00:00":
        job_duration = job_estimate_duration
    tbl.append([job_name, job_status, job_duration])
    table = AsciiTable(tbl)
    print(table.table)


def main_cli(argv):
    config = load_config()
    jt = JenkinsTurris(config["user_id"],
                       config["token"],
                       config["cert_path"],
                       config["key_path"],
                       config["ca_path"])
    parser = argparse.ArgumentParser(description='Jenkis info')
    parser.add_argument('-j', '--job-info', type=str, help='show job info')
    parser.add_argument('-pb', '--print-builds', action="store_const",
                        const="List", help='Print running builds', default=None)
    parser.add_argument('-nj', '--notify-jenkins', action="store_const",
                        const="List", help='Send notification if one of jenkins jobs ends', default=None)
    parser.add_argument('-dl', '--download-log', type=str, help='download build log')

    args = parser.parse_args(argv)
    if args.print_builds:
        print_active_builds(jt)
    if args.download_log:
        rundir = os.path.dirname(os.path.realpath(__file__))
        retpath = os.path.join(rundir, "tmp/arch")
        download_logs(jt, args.download_log, retpath)
    if args.job_info:
        try:
            print_job_info(jt, args.job_info)
        except:
            print("No job found...")
    if args.notify_jenkins:
        wait_build_change(config["user_id"],
                          config["token"],
                          config["cert_path"],
                          config["key_path"],
                          config["ca_path"])


main_cli(sys.argv[1:])
