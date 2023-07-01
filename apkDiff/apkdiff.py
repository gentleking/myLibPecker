#!/usr/bin/python

import sys
import os
import zipfile
from filecmp import *
from subprocess import call, STDOUT
import shutil
import glob
import re
import argparse
import difflib
import tempfile
# import lxml.etree as ET
# from xml.dom.minidom import  parseString
from androguard.core.bytecodes import apk
from fuzzy_match import match
from fuzzy_match import algorithims

# ignoring files
ignore = ".*(align|apktool.yml|pak|MF|RSA|SF|bin|so)"

# ignoring third packages
thirdpackage = ["android", "androidx", "huawei", "vivo", "oppo", "xiaomi", "umeng"]

count = 0
args = None
d = difflib.Differ()
diffratios = []


class bcolors:
    OKBLUE = ''
    OKGREEN = ''
    OKORANGE = ''
    FAIL = ''


def format(string, col):
    return col + string + ''


def main():
    print("")
    print("\t\t\t apktool")
    print("")

    parser = argparse.ArgumentParser(description='Diff two versions of an APK file.')
    parser.add_argument('apk1', metavar='apk1', help='Location of the first APK.')
    parser.add_argument('apk2', metavar='apk2', help='Location of the second APK.')
    parser.add_argument('-c', '--cleanup', action='store_true', help='Remove all extracted files after computation.')
    parser.add_argument('-m', '--meld', action='store_true', help='Open meld to compare directories after.')
    parser.add_argument('-o', '--output', default=os.path.join(tempfile.gettempdir(), 'apkdiff'),
                        help='The location to output the extracted files to.')
    parser.add_argument('-u', '--unique', action='store_true',
                        help='By default, only differences in common files are printed. If -u is enabled, unique files are printed too')

    global args
    args = parser.parse_args()

    # print(args)

    # Make sure the APKs exist.
    exists(args.apk1)
    exists(args.apk2)

    # Check the temporary folder exists & clear it.
    folderExists(args.output, True)

    # get package name
    package1 = getPackageName(args.apk1)
    package2 = getPackageName(args.apk2)

    # get apk name
    apk1 = getApkName(args.apk1)
    apk2 = getApkName(args.apk2)

    # Individual folders for each APK.
    temp1 = os.path.join(args.output, '1/')
    temp2 = os.path.join(args.output, '2/')

    print("apk folders: ", temp1, temp2)

    folderExists(temp1, True)
    folderExists(temp2, True)

    apktoolit(args.apk1, temp1)
    apktoolit(args.apk2, temp2)

    mergesmalifolders(temp1)
    mergesmalifolders(temp2)

    # package1 = getPackageName(temp1 + "AndroidManifest.xml")
    # package2 = getPackageName(temp2 + "AndroidManifest.xml")

    compare(os.path.join(temp1, "smali/", package1), os.path.join(temp2, "smali/", package2), args.unique)

    # Remove all the stuff we have created.
    if args.cleanup and os.path.exists(temp1):
        shutil.rmtree(temp1)

    if args.cleanup and os.path.exists(temp2):
        shutil.rmtree(temp2)

    if args.meld:
        call(["meld", temp1, temp2])


# get apk name
def getApkName(apkname):
    apkn = apkname.split("/")[-1]
    apkn = apkn.split(".")[0]
    return apkn


# get package name
def getPackageName(filepath):
    a = apk.APK(filepath)
    packageName = a.get_package()
    packageName = packageName.replace('.', '/')
    print("package name: " + packageName)
    return packageName


# use apktool to disassemble apk files
def apktoolit(file, dir):
    print("Running apktool against '" + format(file, bcolors.OKBLUE) + "'")
    call(["apktool", "d", "-r", "-f", "-o", dir, file], stdout=open(os.devnull, 'w'), stderr=STDOUT)
    print("[" + format("OK", bcolors.OKGREEN) + "]")


def mergesmalifolders(folder):
    print("Merging additional smali folders")
    target = os.path.join(folder, "smali")
    for name in glob.glob(folder + "smali_classes*"):
        print("\t" + name + " > " + target)
        mergefolders(name, target)
    print("[" + format("OK", bcolors.OKGREEN) + "]")


def mergefolders(root_src_dir, root_dst_dir):
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                os.remove(dst_file)
            shutil.move(src_file, dst_dir)


# print info in dir compared
def print_cmp(dcmp):
    print("\n\n--------------------------- print cmp files ---------------------------")
    print(dcmp.report())
    print("num of diff files: " + str(len(dcmp.diff_files)))
    print("\n")


def compare(folder1, folder2, printunique):
    print("")
    compared = dircmp(folder1, folder2)

    uniqueleft, uniqueright = report_full_closure(compared)
    print("\n\t" + format(str(count), bcolors.OKBLUE) + " files are different.\n")

    diff_num = 0
    print(*diffratios, sep="\n")
    print("num of diff files: " + str(len(diffratios)))

    for dr in diffratios:
        if dr < 0.8:
            diff_num = diff_num + 1
    print("num of diff files which is less than 0.8: " + str(diff_num))

    if printunique:
        if uniqueleft:
            print("[" + format("Only in apk1", bcolors.OKORANGE) + "] ")
            for uniquefolder in uniqueleft:
                print("\t" + uniquefolder)
            print("[" + format("{} unique files in apk1".format(len(uniqueleft)), bcolors.OKORANGE) + "] ")
        else:
            print("[" + format("No unique files in apk1", bcolors.OKORANGE) + "] ")
        if uniqueright:
            print("[" + format("Only in apk2", bcolors.OKORANGE) + "] ")
            for uniquefolder in uniqueright:
                print("\t" + uniquefolder)
            print("[" + format("{} unique files in apk2".format(len(uniqueright)), bcolors.OKORANGE) + "] ")
        else:
            print("[" + format("No unique files in apk2", bcolors.OKORANGE) + "] ")


def getfiles(base, folders, root):
    f = []

    for folder in folders:
        for localroot, subdirs, files in os.walk(os.path.join(base, folder)):
            for file in files:
                f.append(os.path.relpath(os.path.join(localroot, file), root))
    return f


def report_full_closure(self, uniqueleft=[], uniqueright=[], rootcmp=None):
    # print diff files
    if self.diff_files:
        print_cmp(self)

    if not rootcmp:
        rootcmp = self

    uniqueleft += getfiles(self.left, self.left_only, rootcmp.left)
    uniqueright += getfiles(self.right, self.right_only, rootcmp.right)
    for name in self.diff_files:
        if not re.match(ignore, name):
            print("[" + format(name, bcolors.OKGREEN) + "] " +
                  format(self.left.replace(args.output + "1", ""), bcolors.OKBLUE))

            content1 = reader(os.path.join(self.left, name)).splitlines(1)
            content2 = reader(os.path.join(self.right, name)).splitlines(1)
            diff = difflib.unified_diff(content1, content2)

            # print(list(diff))

            filter(list(diff))

            global count
            count += 1

    for sd in self.subdirs.values():
        report_full_closure(sd, uniqueleft, uniqueright, rootcmp)

    return uniqueleft, uniqueright


# filter for generated diff 
def filter(lines):
    line1 = ""
    line2 = ""
    allline = ""
    # print(lines)
    for line in lines:
        allline += line
        if line[:1] == "+":
            line1 += line
        elif line[:1] == "-":
            line2 += line

    # print("compute diff ratio")
    # diffratio = difflib.SequenceMatcher(None, line1, line2).quick_ratio()

    if line1 == "" or line2 == "":
        diffratio = 0
    else:
        # diffratio = algorithims.jaro_winkler(line1, line2)
        # diffratio = algorithims.levenshtein(line1, line2)
        diffratio = algorithims.trigram(line1, line2)
        # diffratio = algorithims.cosine(line1, line2)
    diffratios.append(diffratio)

    # if diff ratio less than 0.8, print all diff lines
    if diffratio < 0.8:
        for line in lines:
            print(line)
        print("diff ratio: " + str(diffratio) + "\n\n")


def reader(file):
    f = open(file, 'r', encoding='utf8', errors='ignore')
    data = f.read()
    f.close()
    return data


def folderExists(path, clean=False):
    if clean and os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def exists(file):
    if not os.path.isfile(file):
        print(format("'{}' does not exist.".format(file), bcolors.FAIL))
        exit(0)


if __name__ == '__main__':
    main()
