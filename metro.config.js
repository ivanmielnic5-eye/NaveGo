const { getDefaultConfig } = require('expo/metro-config');
const config = getDefaultConfig(__dirname);
config.resolver.assetExts.push('mbtiles', 'sqlite', 'db', 'pmtiles', 'pbf', 'jsonl');
module.exports = config;
