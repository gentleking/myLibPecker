#!/usr/bin/python

import difflib
import os

from fuzzy_match import algorithims

diff_ratios = []


def main():
    class_compare()


def class_compare():
    os_path1 = "/tmp/apkdiff/1/smali/"
    os_path2 = "/tmp/apkdiff/2/smali/"
    file = open("classPairOutput.txt")
    lines = file.readlines()
    left_class = ""
    right_class = ""
    similarity = 0
    count = 0
    diff_count = 0
    for line in lines:
        left_class = line.split(":")[0].replace(".", "/") + ".smali"
        right_class = line.split(":")[1].replace(".", "/") + ".smali"
        similarity = line.split(":")[-1]
        file_path1 = os_path1 + left_class
        file_path2 = os_path2 + right_class
        if exists(file_path1) and exists(file_path2):
            count += 1
            
            content1 = reader(file_path1).splitlines(1)
            content2 = reader(file_path2).splitlines(1)
            diff = difflib.unified_diff(content1, content2, file_path1, file_path2)
            filter(list(diff))


            # if len(list(diff)):
            #     diff_count += 1
            #     print("similarity: " + similarity)
    file.close()
    print("count of existing files: ", count)
    print("count of diff files: ", diff_count)


def filter(lines):
    line1 = ""
    line2 = ""
    all_line = ""

    # print(lines)
    for line in lines:
        if line[:1] == "+":
            line1 += line
            all_line += line
        elif line[:1] == "-":
            line2 += line
            all_line += line

    for line in lines:
        if line:
            print(line)
    # print(all_line)
    # print(lines)

def reader(file):
    f = open(file, 'r', encoding='utf8', errors='ignore')

    data = f.read()
    f.close()
    return data


def exists(file):
    if not os.path.exists(file):
        # print("'{}' does not exist.".format(file))
        print("No existing file: ", file)
        return False
    return True


if __name__ == "__main__":
    main()
