package cn.fudan.libpecker.main;

import cn.fudan.analysis.tree.PackageNode;
import cn.fudan.common.Apk;
import cn.fudan.common.LibPeckerConfig;
import cn.fudan.common.Lib;
import cn.fudan.common.Sdk;
import cn.fudan.common.util.PackageNameUtil;
import cn.fudan.libpecker.core.LibApkMapper;
import cn.fudan.libpecker.core.PackageMapEnumerator;
import cn.fudan.libpecker.core.PackagePairCandidate;
import cn.fudan.libpecker.model.*;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.*;


/**
 * Created by yuanxzhang on 27/04/2017.
 */
public class ProfileBasedLibPecker {

    Set<String> targetSdkClassNameSet;
//    LibProfile libProfile;
    ApkProfile apkProfileOld;
    ApkProfile apkProfileNew;
    public Map<String, ApkPackageProfile> apkPackageProfileOldMap;//pkg name -> ApkPackageProfile
    public Map<String, ApkPackageProfile> apkPackageProfileNewMap;//pkg name -> ApkPackageProfile
//    public Map<String, LibPackageProfile> libPackageProfileMap;//pkg name -> LibPackageProfile

    public ProfileBasedLibPecker(ApkProfile apkProfileOld, ApkProfile apkProfileNew, Set<String> targetSdkClassNameSet) {
        this.targetSdkClassNameSet = targetSdkClassNameSet;
        this.apkProfileOld = apkProfileOld;
        this.apkProfileNew = apkProfileNew;
        this.apkPackageProfileOldMap = apkProfileOld.packageProfileMap;
        this.apkPackageProfileNewMap = apkProfileNew.packageProfileMap;
    }

    public double calculateMaxProbability() {
        /* APP Privacy Compliance
        Calculate every class similarity of package in apk
        */
        int diffClass = 0;
        int totalClass = 0;
        for (ApkPackageProfile apkPackageProfile_ : apkPackageProfileOldMap.values()) {
            totalClass += apkPackageProfile_.classProfileMap.size();
            LibPackageProfile libPkg = LibPackageProfile.apk2libPackage(apkPackageProfile_);

            PackagePairCandidate candidatePackages = new PackagePairCandidate(libPkg, apkPackageProfileNewMap.values());

            /* APP Privacy Compliance
             * for a package, output its class pair and similarity with an APK
             */
            Map<String, String> classPair = candidatePackages.getMaxClassPairMap();
            Map<String, Double> classSimilarityPair = candidatePackages.getMaxClassSimilarityMap();

            String fileName = "classPairOutput.txt";
            String diffClassName = "diffClassName.txt";
            try {
                FileWriter fileWriter = new FileWriter(fileName, true);
                PrintWriter output = new PrintWriter(fileWriter);

                FileWriter diffFileWriter = new FileWriter(diffClassName, true);
                PrintWriter diffOutput = new PrintWriter(diffFileWriter);

                for (String className: classPair.keySet()) {
                    output.print(className + ":" + classPair.get(className) + ":");
                    output.println(classSimilarityPair.get(className));
                    System.out.println(className + ":" + classPair.get(className) + ":" + classSimilarityPair.get(className));
                    if (!className.equals(classPair.get(className))) {
                        diffOutput.print(className + ":" +classPair.get(className) + ":");
                        diffOutput.println(classSimilarityPair.get(className));
                        diffClass++;
                    }
                }
                output.close();
                diffOutput.close();
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
        }
        System.out.println("Total class count: " + totalClass);
        System.out.println("Diff class name pair count: " + diffClass);
        return 1;
    }

    private LibApkMapper maxPartition = null;
    public LibApkMapper getMaxPartition(){
        if (maxPartition == null) {
            calculateMaxProbability();
        }
        return maxPartition;
    }

    private static void fail(String message) {
        System.err.println(message);
        System.exit(0);
    }

    public static double singleMain(String apkPathOld, String apkPathNew) {
        Apk apkOld = Apk.loadFromFile(apkPathOld);
        if (apkOld == null) {
            fail("old apk not parsed");
        }
        Apk apkNew = Apk.loadFromFile(apkPathNew);
        if (apkNew == null) {
            fail("new apk not parse");
        }
        Sdk sdk = Sdk.loadDefaultSdk();
        if (sdk == null) {
            fail("default sdk not parsed");
        }
        Set<String> targetSdkClassNameSet = sdk.getTargetSdkClassNameSet();

        ApkProfile apkProfileOld = ApkProfile.create(apkOld, targetSdkClassNameSet);
        ApkProfile apkProfileNew = ApkProfile.create(apkNew, targetSdkClassNameSet);

        double similarity = 0;

        ProfileBasedLibPecker pecker = new ProfileBasedLibPecker(apkProfileOld, apkProfileNew, targetSdkClassNameSet);
        similarity = pecker.calculateMaxProbability();

        return similarity;
    }

    public static void main(String[] args) {
        String apkPathOld = null;
        String apkPathNew = null;

        if (args == null || args.length == 2) {
            apkPathOld = args[0];
            apkPathNew = args[1];
        }
        else {
            fail("Usage: <old_apk_path> <new_apk_path>");
        }

        long current = System.currentTimeMillis();
        double similarity = singleMain(apkPathOld, apkPathNew);

//        System.out.println("similarity: " + similarity);
        System.out.println("Class Pair Generator Complete!");
        System.out.println("time: " + (System.currentTimeMillis() - current));

    }

}
