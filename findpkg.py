#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 11 17:20:18 2017

@author: paja
"""
import json
from urllib.request import urlopen
from terminaltables import AsciiTable
import argparse
import sys
import pprint
pp = pprint.PrettyPrinter(width=41, compact=True)


class Packages:
    def __init__(self, branch="omnia-nightly", enable_print=True):
        self.__branch = branch
        self.__enable_print = enable_print
        self.__repo_url_turris = 'http://repo.turris.cz/%s/packages/%s/Packages'
        self.__repo_url_lede = 'https://downloads.lede-project.org/snapshots/packages/x86_64/%s/Packages'
        self.__repo_url_openwrt_master = 'https://downloads.openwrt.org/snapshots/targets/x86/64/%s/Packages'
        self.__repo_url_openwrt_stable = 'https://downloads.openwrt.org/releases/18.06.2/packages/x86_64/%s/Packages'
        self.__repo_url_mox = 'https://repo.turris.cz/hbd/packages/mox/%s/Packages'
        self.__repo_url_mox_dragons = 'https://repo.turris.cz/hbd/packages/mox/%s/Packages'
        self.__repo_url_mox_kittens = 'https://repo.turris.cz/hbk/packages/mox/%s/Packages'
        self._pkg_list = []
        self.__feeds_turris = ["base", "hardware", "lucics", "management",
                               "openwisp", "packages", "php", "printing",
                               "routing", "telephony", "turrispackages"]
        self.__feeds_lede = ["base", "luci", "packages",
                             "routing", "telephony"]
        self.__feeds_mox = ["base", "luci", "openwisp", "packages", "routing",
                            "sidn", "telephony",	 "turrispackages"]

    def dprint(self,newline=True, *args):
        if self.__enable_print:
            print(*args, end=" ")
            if newline:
                print()

    def search_by_name(self, name, case_sensitive=True):
        ret = []
        for item in self._pkg_list:
            if case_sensitive is True:
                pkg_name = item["Package"]
            else:
                pkg_name = item["Package"].lower()
                name = name.lower()
            if pkg_name.find(name) >= 0:
                ret.append(item)
        return ret

    def search_by_depends(self, name, case_sensitive=False, full_depends=False):
        ret = []
        for item in self._pkg_list:
            if "Depends" in item:
                if case_sensitive is True:
                    pkg_name = item["Depends"]
                else:
                    pkg_name = item["Depends"].lower()
                    name = name.lower()
                if pkg_name.find(name) >= 0:
                    ret.append(item)
        return ret

    def search_by_sha256(self, sha256):
        pass

    def clean_pkg_list(self):
        self._pkg_list = []

    def get_pkg_list(self, project):
        if project == "turris":
            feeds = self.__feeds_turris
            self.dprint(True ,"Branch", self.__branch, ":")
        elif project == "lede" or project == "openwrt_master" or project == "openwrt_stable":
            feeds = self.__feeds_lede
            self.dprint(True, "%s repo:" % project)
        elif project == "mox_kittens" or project == "mox_dragons":
            feeds = self.__feeds_mox
            self.dprint(True, "%s repo:" % project)
        else:
            self.dprint(True ,"Unknow feed %s" % project)
            exit
        self.dprint(False, "Downloading feeds :")
        for feed in feeds:
            try:
                feed_list = self._download_list(feed, project)
                self.dprint(False, feed + ", ")
                self._pkg_list = self._pkg_list + self._parse_packages(feed_list)
            except:
                self.dprint(False, feed+"(not found),")
        print()

    def _get_gitlab_url(self, pkg_source, branch="test"):
        ret = ""
        if pkg_source.startswith("feeds"):
            if pkg_source.startswith("feeds/turrispackages"):
                ret = pkg_source.replace("feeds/turrispackages/",
                                         "https://gitlab.labs.nic.cz/turris/turris-os-packages/tree/%s/" % branch)
            elif pkg_source.startswith("feeds/lucics"):
                ret = pkg_source.replace("feeds/lucics/",
                                         "https://gitlab.labs.nic.cz/turris/luci-cs/tree/master/")
            return ret
        elif pkg_source.startswith("package"):
            ret = pkg_source.replace("package/",
                                     "https://gitlab.labs.nic.cz/turris/openwrt/tree/%s/" % branch)
            return ret
        else:
            return ""

    def _download_list(self, feed, project="turris"):
        """ Download package feed list for project (lede,turris ) """
        if project == "turris":
            url_full = self.__repo_url_turris % (self.__branch, feed)
        elif project == "lede":
            url_full = self.__repo_url_lede % feed
        elif project == "mox_kittens":
            url_full = self.__repo_url_mox_kittens % feed
        elif project == "mox_dragons":
            url_full = self.__repo_url_mox_dragons % feed
        elif project == "openwrt_master":
            url_full = self.__repo_url_openwrt_master % feed
        elif project == "openwrt_stable":
            url_full = self.__repo_url_openwrt_stable % feed
        else:
            self.dprint(True, "Unknown project!")
            exit
        #response = urllib2.urlopen(url_full)
        response = urlopen(url_full)
        return response.read().decode('utf-8')

    def _parse_signle_package(self, package):
        ret = []
        tmp = []
        tmp_pkg_dict={}
        #print(package)
        for item in package.splitlines():
            if item.find(":") >= 0:
                #tmp.append(map(str.strip, item.split(":", 1)))
                name, value = item.split(":", 1)
                name = name.strip()
                value = value.strip()
                #tmp.append()
                tmp_pkg_dict.update({name:value})

        #print(tmp)
        #for item in tmp:
        #    if item != [""]:
        #        ret.append(item)
        #tmp_dict = dict(ret)
        #if "Source" in tmp_dict:
        #    ret.append(["GitlabURL", self._get_gitlab_url(tmp_dict["Source"])])
        #print(ret)
        #return dict(ret)
        return tmp_pkg_dict

    def _parse_packages(self, packages):
        ret = []
        #print(len(packages.split("\n\n")))
        for item in packages.split("\n\n"):
            single_package = self._parse_signle_package(item)
            if single_package != {}:
                ret.append(single_package)
        return ret


def parse_package_version():
    pass


def print_pkg(packages, header=["Package", "Version", "Filename"]):
    ret_tbl = []
    if len(packages) == 0:
        return [["No packages found"]]
    ret_tbl.append(header)
    for pkg in packages:
        tbl_line = []
        for val_name in header:
            tbl_line.append(pkg[val_name])
        ret_tbl.append(tbl_line)
    return ret_tbl

def print_json(packages, header):
    return json.dumps(packages, indent=4, sort_keys=True)


def find_pkg(pkg_dict,pkg_name):
    empty_line={'Architecture': '',
             'Depends':'',
             'Description':'',
             'Filename': '',
             'Installed-Size': '',
             'License': '',
             'MD5Sum': '',
             'Maintainer': '',
             'Package': '',
             'Require-User': '',
             'SHA256sum': '',
             'Section': '',
             'Size': '',
             'Source': '',
             'Version':''}
    for item in pkg_dict:
        if item["Package"]==pkg_name:
            return item
    return empty_line


def main_cli(argv):
    global abc
    header = ["Package", "Version", "Filename"]
    parser = argparse.ArgumentParser(description='Omnia')
    parser.add_argument('-fp', '--find-package', nargs='+',
                        help='find package')
    parser.add_argument('-fd', '--find-depends', help='find depend packages')
    parser.add_argument('-b', '--branch', action="store",
                        default="omnia-nightly", help='set omnia branch')
    parser.add_argument('-pl', '--project-lede', action="store_true",
                        help='Search in lede project')
    parser.add_argument('-pmk', '--project-mox-kittens', action="store_true",
                        help='Search in mox kittens project')
    parser.add_argument('-pmd', '--project-mox-dragons', action="store_true",
                        help='Search in mox dragosn project')
    parser.add_argument('-pd', '--print-description', action="store_const",
                        const="Description", help='Print description',
                        default=None)
    parser.add_argument('-pc', '--print-comparsion', action="store_const",
                        const="Comparsion", help='Print comparsion for 3.x,lede and hbd,hbk',
                        default=None)
    parser.add_argument('-ps', '--print-section', action="store_const",
                        const="Section", help='Print section', default=None)
    parser.add_argument('-pss', '--print-source', action="store_const",
                        const="Source", help='Print print source',
                        default=None)
    parser.add_argument('-ppd', '--print-package-depends', action="store_const",
                        const="Depends", help='Print depends source',
                        default=None)
    parser.add_argument('-pu', '--print-url', action="store_const",
                        const="GitlabURL", help='Print gitlab url',
                        default=None)
    parser.add_argument('-js', '--json', action="store_true",
                        help='Print output in json format')

    args = parser.parse_args(argv)
    if args.print_description:
        header.append(args.print_description)
    if args.print_section:
        header.append(args.print_section)
    if args.print_source:
        header.append(args.print_source)
    if args.print_package_depends:
        header.append(args.print_package_depends)
    if args.print_url:
        header.append(args.print_url)
    if args.find_package and args.print_comparsion:
        abc = Packages(args.branch, enable_print=not(args.json))
        repo_list=["turris","lede","mox_kittens","mox_dragons","openwrt_stable","openwrt_master"]
        ccc = dict([(item,[]) for item in repo_list])
        #ccc = {"turris":[],"lede":[],"mox_kittens":[],"mox_dragons":[]}
        out=[]
        for pkg_name in args.find_package:
            abc = Packages(args.branch, enable_print=not(args.json))
            #print(pkg_name)
            for project_name in repo_list: # ["turris","lede","mox_kittens","mox_dragons"]:
                abc.clean_pkg_list()
                abc.get_pkg_list(project_name)
                ccc[project_name] += abc.search_by_name(pkg_name, False)
            #pp.pprint(ccc)
        for item in ccc["turris"]:
            #print(item["Package"])
            pkg_lede=find_pkg(ccc["lede"],item["Package"])
            pkg_mox_kittens=find_pkg(ccc["mox_kittens"],item["Package"])
            pkg_mox_dragons=find_pkg(ccc["mox_dragons"],item["Package"])
            pkg_openwrt_stable=find_pkg(ccc["openwrt_stable"],item["Package"])
            pkg_openwrt_master=find_pkg(ccc["openwrt_master"],item["Package"])
            out.append([item["Package"],
                        item["Version"],
                        pkg_mox_kittens["Version"],
                        pkg_mox_dragons["Version"],
                        pkg_openwrt_stable["Version"],
                        pkg_lede["Version"]
                        ])
        out.insert(0,["Package","Turris","Kittens","Dragons","Up stable","Upstream"])
        table = AsciiTable(out)
        print(table.table)
    elif args.find_package:
        # disable debug print in case of json output
        abc = Packages(args.branch, enable_print=not(args.json))
        if args.project_lede:
            abc.get_pkg_list("lede")
        elif args.project_mox_kittens:
            abc.get_pkg_list("mox_kittens")
        elif args.project_mox_dragons:
            abc.get_pkg_list("mox_dragons")
        else:
            abc.get_pkg_list("turris")
        ccc = []
        for pkg_name in args.find_package:
            ccc += abc.search_by_name(pkg_name, False)
        if args.json:
            json_data=print_json(ccc, header)
            print(json_data)
        else:
            table = AsciiTable(print_pkg(ccc, header))
            print("Find ", args.find_package, "in branch ", args.branch)
            print()
            print(table.table)
    if args.find_depends:
        abc = Packages(args.branch, enable_print=not(args.json))
        if args.project_lede:
            abc.get_pkg_list("lede")
        elif args.project_mox:
            abc.get_pkg_list("mox")
        else:
            abc.get_pkg_list("turris")
        ccc = abc.search_by_depends(args.find_depends, False)
        if args.json:
            json_data=print_json(ccc, header)
            print(json_data)
        else:
            table = AsciiTable(print_pkg(ccc, header))
            print("Find ", args.find_depends, "in branch ", args.branch)
            print()
            print(table.table)


main_cli(sys.argv[1:])
