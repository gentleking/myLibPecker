package cn.fudan.libpecker.model;

import cn.fudan.analysis.dep.DepAnalysis;
import cn.fudan.analysis.tree.PackageNode;
import cn.fudan.analysis.tree.TreeAnalysis;
import cn.fudan.common.Apk;
import cn.fudan.libpecker.analysis.ClassWeightAnalysis;

import java.util.*;

/**
 * Created by yuanxzhang on 19/05/2017.
 */
public class ApkProfile {
    public Map<String, ApkPackageProfile> packageProfileMap;//pkg name -> [LibPackageProfile, ...]

    private ApkProfile(){}

    public static ApkProfile create(Apk apk, Set<String> targetSdkClassNameSet) {
        ApkProfile apkProfile = new ApkProfile();

        apkProfile.packageProfileMap = new HashMap<>();
        Set<PackageNode> apkPackages = TreeAnalysis.analyze(apk);
        List<ApkPackageProfile> apkProfiles = new ArrayList<>();


        /*
        * Change initializing ApkPackageProfile
        */
//        Map<String, Integer> classBBWeightMap = ClassWeightAnalysis.getClassBBWeight(apk);
//        DepAnalysis depAnalysis = new DepAnalysis(apk, (HashSet)targetSdkClassNameSet);
//        Map<String, Integer> classDepWeightMap = ClassWeightAnalysis.getClassDepWeight(depAnalysis);

        for (PackageNode packageNode : apkPackages) {
            apkProfiles.add(new ApkPackageProfile(packageNode,/* classBBWeightMap, classDepWeightMap,*/ targetSdkClassNameSet));
        }
        for (ApkPackageProfile profile : apkProfiles) {
            apkProfile.packageProfileMap.put(profile.packageName, profile);
        }

        apkPackages.clear();
        apkProfiles.clear();

        return apkProfile;

    }
}
