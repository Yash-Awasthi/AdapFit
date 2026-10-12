// Native settings that expo prebuild does not cover; android/ is generated, so they live here.
const fs = require('node:fs');
const path = require('node:path');
const {
  AndroidConfig,
  CodeGenerator,
  withAndroidManifest,
  withAppBuildGradle,
  withDangerousMod,
  withGradleProperties,
  withProjectBuildGradle,
} = require('expo/config-plugins');

const NETWORK_SECURITY_CONFIG = `<?xml version="1.0" encoding="utf-8"?>
<!-- HTTPS everywhere; plain HTTP only to the phone itself, which adb reverse forwards to a local server. -->
<network-security-config>
  <domain-config cleartextTrafficPermitted="true">
    <domain includeSubdomains="false">localhost</domain>
    <domain includeSubdomains="false">127.0.0.1</domain>
  </domain-config>
</network-security-config>
`;

const withNetworkSecurityConfig = (config) => {
  config = withDangerousMod(config, [
    'android',
    (cfg) => {
      const dir = path.join(cfg.modRequest.platformProjectRoot, 'app/src/main/res/xml');
      fs.mkdirSync(dir, { recursive: true });
      fs.writeFileSync(path.join(dir, 'network_security_config.xml'), NETWORK_SECURITY_CONFIG);
      return cfg;
    },
  ]);
  return withAndroidManifest(config, (cfg) => {
    const app = AndroidConfig.Manifest.getMainApplicationOrThrow(cfg.modResults);
    app.$['android:networkSecurityConfig'] = '@xml/network_security_config';
    return cfg;
  });
};

// Health Connect through Android 13 is a separate app the manifest must be allowed to see.
const withHealthConnectQuery = (config) =>
  withAndroidManifest(config, (cfg) => {
    const manifest = cfg.modResults.manifest;
    const pkg = 'com.google.android.apps.healthdata';
    manifest.queries ??= [];
    const queries = manifest.queries;
    const present = queries.some((q) => (q.package ?? []).some((p) => p.$['android:name'] === pkg));
    if (!present) queries.push({ package: [{ $: { 'android:name': pkg } }] });
    return cfg;
  });

// The release key and mobile/keystore.properties stay outside android/, which prebuild may delete.
const withReleaseSigning = (config) =>
  withAppBuildGradle(config, (cfg) => {
    let src = cfg.modResults.contents;
    src = CodeGenerator.mergeContents({
      tag: 'adapfit-keystore-properties',
      src,
      newSrc: [
        'def keystorePropertiesFile = new File(projectRoot, "keystore.properties")',
        'def keystoreProperties = new Properties()',
        'if (keystorePropertiesFile.exists()) {',
        '    keystoreProperties.load(new FileInputStream(keystorePropertiesFile))',
        '}',
      ].join('\n'),
      anchor: /^def projectRoot = /m,
      offset: 1,
      comment: '//',
    }).contents;
    src = CodeGenerator.mergeContents({
      tag: 'adapfit-release-signing',
      src,
      newSrc: [
        '        if (keystorePropertiesFile.exists()) {',
        '            release {',
        "                storeFile new File(projectRoot, keystoreProperties['storeFile'])",
        "                storePassword keystoreProperties['storePassword']",
        "                keyAlias keystoreProperties['keyAlias']",
        "                keyPassword keystoreProperties['keyPassword']",
        '            }',
        '        }',
      ].join('\n'),
      anchor: /^\s*signingConfigs \{/m,
      offset: 1,
      comment: '//',
    }).contents;
    // Without keystore.properties the release build comes out unsigned, never debug-signed.
    const releaseSigning = 'signingConfig keystorePropertiesFile.exists() ? signingConfigs.release : null';
    src = src.replace(
      /(release \{\n(?:\s*\/\/.*\n)*)\s*signingConfig signingConfigs\.debug/,
      `$1            ${releaseSigning}`,
    );
    if (!src.includes(releaseSigning)) {
      throw new Error('with-android-release: release signingConfig line not found in app/build.gradle');
    }
    cfg.modResults.contents = src;
    return cfg;
  });

// Windows keeps paths under 260 characters; a native module's CMake tree under
// node_modules/<long name>/android/.cxx/... can pass that, and ninja then loops.
const withShortCmakePaths = (config) =>
  withProjectBuildGradle(config, (cfg) => {
    cfg.modResults.contents = CodeGenerator.mergeContents({
      tag: 'adapfit-windows-cmake',
      src: cfg.modResults.contents,
      newSrc: [
        'if (System.getProperty("os.name").toLowerCase().contains("windows")) {',
        '  subprojects { p ->',
        '    p.plugins.withId("com.android.library") {',
        '      p.android.externalNativeBuild.cmake.buildStagingDirectory = new File(System.getenv("SystemDrive") + "/cxx/${p.name.hashCode().abs()}")',
        '    }',
        '  }',
        '}',
      ].join('\n'),
      anchor: /apply plugin: "com\.facebook\.react\.rootproject"/,
      offset: 1,
      comment: '//',
    }).contents;
    return cfg;
  });

const withReleaseHeap = (config) =>
  withGradleProperties(config, (cfg) => {
    const item = cfg.modResults.find((p) => p.type === 'property' && p.key === 'org.gradle.jvmargs');
    const value = '-Xmx4096m -XX:MaxMetaspaceSize=1024m';
    if (item) item.value = value;
    else cfg.modResults.push({ type: 'property', key: 'org.gradle.jvmargs', value });
    return cfg;
  });

module.exports = (config) =>
  [withNetworkSecurityConfig, withHealthConnectQuery, withReleaseSigning, withShortCmakePaths, withReleaseHeap].reduce(
    (cfg, plugin) => plugin(cfg),
    config,
  );
