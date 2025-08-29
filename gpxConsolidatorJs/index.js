const fs = require('fs');
const path = require('path');
const { DOMParser, XMLSerializer } = require('@xmldom/xmldom');

const createGpxProcessor = () => {
    const GPX_NS = 'http://www.topografix.com/GPX/1/1';
    
    const generateUniqueTrackName = (originalName, filterDate, baseFilename, uniqueNames) => {
        const dateStr = filterDate ? 
            filterDate.toLocaleDateString('en-US', { month: 'short', day: '2-digit' }).replace(' ', '') :
            'NoDate';
        const baseName = `${baseFilename}_${dateStr}`;
        
        if (uniqueNames[baseName]) {
            const counter = uniqueNames[baseName] + 1;
            uniqueNames[baseName] = counter;
            return [`${baseName}_${counter}`, uniqueNames];
        } else {
            uniqueNames[baseName] = 1;
            return [baseName, uniqueNames];
        }
    };

    const generateUniqueWaypointName = (originalName, filterDate, baseFilename, uniqueNames) => {
        const dateStr = filterDate ? 
            filterDate.toLocaleDateString('en-US', { month: 'short', day: '2-digit' }).replace(' ', '') :
            'NoDate';
        const baseName = `${baseFilename}_${dateStr}`;
        
        if (uniqueNames[baseName]) {
            const counter = uniqueNames[baseName] + 1;
            uniqueNames[baseName] = counter;
            return [`${baseName}_${counter}`, uniqueNames];
        } else {
            uniqueNames[baseName] = 1;
            return [baseName, uniqueNames];
        }
    };

    const getElementName = (element) => {
        const nameElem = element.getElementsByTagNameNS(GPX_NS, 'name')[0];
        return nameElem && nameElem.textContent ? nameElem.textContent.trim() : null;
    };

    const getWaypointDateTime = (waypoint) => {
        const timeElem = waypoint.getElementsByTagNameNS(GPX_NS, 'time')[0];
        if (!timeElem || !timeElem.textContent) return null;
        
        try {
            return new Date(timeElem.textContent);
        } catch (error) {
            return null;
        }
    };

    const processWaypoint = (waypoint, filterDate = null, startTime = null, endTime = null) => {
        const waypointDateTime = getWaypointDateTime(waypoint);
        
        if (filterDate && waypointDateTime) {
            const waypointDate = new Date(waypointDateTime.getFullYear(), waypointDateTime.getMonth(), waypointDateTime.getDate());
            if (waypointDate.getTime() !== filterDate.getTime()) {
                return null;
            }
        }
        
        if (startTime && endTime && waypointDateTime) {
            const waypointTime = waypointDateTime.getHours() * 60 + waypointDateTime.getMinutes();
            const startMinutes = startTime.getHours() * 60 + startTime.getMinutes();
            const endMinutes = endTime.getHours() * 60 + endTime.getMinutes();
            
            if (waypointTime < startMinutes || waypointTime > endMinutes) {
                return null;
            }
        }
        
        return waypoint.cloneNode(true);
    };

    const processTrack = (track, name, filterDate = null, startTime = null, endTime = null, document) => {
        const filteredTrack = document.createElementNS(GPX_NS, 'trk');
        
        for (let i = 0; i < track.attributes.length; i++) {
            const attr = track.attributes[i];
            filteredTrack.setAttribute(attr.name, attr.value);
        }
        
        const filteredTrackName = document.createElementNS(GPX_NS, 'name');
        filteredTrackName.textContent = name;
        filteredTrack.appendChild(filteredTrackName);
        
        const segments = track.getElementsByTagNameNS(GPX_NS, 'trkseg');
        
        for (let i = 0; i < segments.length; i++) {
            const segment = segments[i];
            const points = segment.getElementsByTagNameNS(GPX_NS, 'trkpt');
            const newSegment = document.createElementNS(GPX_NS, 'trkseg');
            
            for (let j = 0; j < segment.attributes.length; j++) {
                const attr = segment.attributes[j];
                newSegment.setAttribute(attr.name, attr.value);
            }
            
            for (let j = 0; j < points.length; j++) {
                const point = points[j];
                const timeElem = point.getElementsByTagNameNS(GPX_NS, 'time')[0];
                
                if (!timeElem || !timeElem.textContent) continue;
                
                const pointTime = new Date(timeElem.textContent);
                
                if (filterDate) {
                    const pointDate = new Date(pointTime.getFullYear(), pointTime.getMonth(), pointTime.getDate());
                    if (pointDate.getTime() !== filterDate.getTime()) continue;
                }
                
                if (startTime && endTime) {
                    const pointMinutes = pointTime.getHours() * 60 + pointTime.getMinutes();
                    const startMinutes = startTime.getHours() * 60 + startTime.getMinutes();
                    const endMinutes = endTime.getHours() * 60 + endTime.getMinutes();
                    
                    if (pointMinutes < startMinutes || pointMinutes > endMinutes) continue;
                }
                
                newSegment.appendChild(point.cloneNode(true));
            }
            
            if (newSegment.getElementsByTagNameNS(GPX_NS, 'trkpt').length > 0) {
                filteredTrack.appendChild(newSegment);
            }
        }
        
        return filteredTrack;
    };

    const parseGpxContent = (baseName, xmlContent, newGpxRoot, uniqueTrackNames, uniqueWaypointNames, 
                            filterDate = null, startTime = null, endTime = null) => {
        const parser = new DOMParser();
        const gpxDoc = parser.parseFromString(xmlContent, 'text/xml');
        const gpxRoot = gpxDoc.documentElement;

        const tracks = gpxRoot.getElementsByTagNameNS(GPX_NS, 'trk');
        const waypoints = gpxRoot.getElementsByTagNameNS(GPX_NS, 'wpt');

        for (let i = 0; i < tracks.length; i++) {
            const track = tracks[i];
            const originalTrackName = getElementName(track);
            const [trackName, updatedTrackNames] = generateUniqueTrackName(
                originalTrackName, filterDate, baseName, uniqueTrackNames
            );
            uniqueTrackNames = updatedTrackNames;
            
            const filteredTrack = processTrack(track, trackName, filterDate, startTime, endTime, newGpxRoot.ownerDocument);
            if (filteredTrack && filteredTrack.getElementsByTagNameNS(GPX_NS, 'trkpt').length > 0) {
                newGpxRoot.appendChild(filteredTrack);
            }
        }

        for (let i = 0; i < waypoints.length; i++) {
            const waypoint = waypoints[i];
            const filteredWaypoint = processWaypoint(waypoint, filterDate, startTime, endTime);
            
            if (filteredWaypoint) {
                const originalWaypointName = getElementName(waypoint);
                const [waypointName, updatedWaypointNames] = generateUniqueWaypointName(
                    originalWaypointName, filterDate, baseName, uniqueWaypointNames
                );
                uniqueWaypointNames = updatedWaypointNames;
                
                let nameElem = filteredWaypoint.getElementsByTagNameNS(GPX_NS, 'name')[0];
                if (!nameElem) {
                    nameElem = filteredWaypoint.ownerDocument.createElementNS(GPX_NS, 'name');
                    filteredWaypoint.appendChild(nameElem);
                }
                nameElem.textContent = waypointName;
                
                newGpxRoot.appendChild(filteredWaypoint);
            }
        }

        return [newGpxRoot, uniqueTrackNames, uniqueWaypointNames];
    };

    // Node.js file system wrapper
    const parseGpxFile = (filePath, newGpxRoot, uniqueTrackNames, uniqueWaypointNames, 
                         filterDate = null, startTime = null, endTime = null) => {
        const baseName = path.parse(filePath).name;
        const xmlContent = fs.readFileSync(filePath, 'utf8');
        return parseGpxContent(baseName, xmlContent, newGpxRoot, uniqueTrackNames, uniqueWaypointNames, 
                              filterDate, startTime, endTime);
    };

    // Browser File API wrapper
    const parseGpxFileFromUpload = async (file, newGpxRoot, uniqueTrackNames, uniqueWaypointNames, 
                                         filterDate = null, startTime = null, endTime = null) => {
        const baseName = file.name.replace(/\.[^/.]+$/, "");
        const xmlContent = await file.text();
        return parseGpxContent(baseName, xmlContent, newGpxRoot, uniqueTrackNames, uniqueWaypointNames, 
                              filterDate, startTime, endTime);
    };

    const createNewGpx = (name = 'Consolidated GPX Tracks and Waypoints') => {
        const parser = new DOMParser();
        const doc = parser.parseFromString('<gpx></gpx>', 'text/xml');
        const root = doc.documentElement;
        
        root.setAttribute('xmlns', 'http://www.topografix.com/GPX/1/1');
        root.setAttribute('xmlns:gpxx', 'http://www.garmin.com/xmlschemas/GpxExtensions/v3');
        root.setAttribute('xmlns:gpxtrkx', 'http://www.garmin.com/xmlschemas/TrackStatsExtension/v1');
        root.setAttribute('xmlns:wptx1', 'http://www.garmin.com/xmlschemas/WaypointExtension/v1');
        root.setAttribute('xmlns:gpxtpx', 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1');
        root.setAttribute('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance');
        
        root.setAttribute('creator', 'GPSMAP 64st');
        root.setAttribute('version', '1.1');
        
        const schemaLocation = [
            'http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd',
            'http://www.garmin.com/xmlschemas/GpxExtensions/v3 http://www8.garmin.com/xmlschemas/GpxExtensionsv3.xsd',
            'http://www.garmin.com/xmlschemas/TrackStatsExtension/v1 http://www8.garmin.com/xmlschemas/TrackStatsExtension.xsd',
            'http://www.garmin.com/xmlschemas/WaypointExtension/v1 http://www8.garmin.com/xmlschemas/WaypointExtensionv1.xsd',
            'http://www.garmin.com/xmlschemas/TrackPointExtension/v1 http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd'
        ].join(' ');
        root.setAttribute('xsi:schemaLocation', schemaLocation);
        
        const metadata = doc.createElementNS(GPX_NS, 'metadata');
        root.appendChild(metadata);
        
        if (name) {
            const nameTag = doc.createElementNS(GPX_NS, 'name');
            nameTag.textContent = name;
            metadata.appendChild(nameTag);
        }
        
        const link = doc.createElementNS(GPX_NS, 'link');
        link.setAttribute('href', 'http://www.garmin.com');
        const textTag = doc.createElementNS(GPX_NS, 'text');
        textTag.textContent = 'Garmin International';
        link.appendChild(textTag);
        metadata.appendChild(link);
        
        const timeTag = doc.createElementNS(GPX_NS, 'time');
        timeTag.textContent = new Date().toISOString();
        metadata.appendChild(timeTag);
        
        return root;
    };

    const createConsolidatedGpx = (gpxFiles, outputFile, filterDate, startTime, endTime) => {
        const newGpxRoot = createNewGpx();
        let uniqueTrackNames = {};
        let uniqueWaypointNames = {};

        gpxFiles.forEach(gpxFile => {
            const result = parseGpxFile(gpxFile, newGpxRoot, uniqueTrackNames, uniqueWaypointNames, 
                                      filterDate, startTime, endTime);
            uniqueTrackNames = result[1];
            uniqueWaypointNames = result[2];
        });

        const serializer = new XMLSerializer();
        const xmlString = serializer.serializeToString(newGpxRoot.ownerDocument);
        
        const finalXml = '<?xml version="1.0" encoding="UTF-8"?>\n' + xmlString;
        
        fs.writeFileSync(outputFile, finalXml, 'utf8');
        console.log(`Successfully created consolidated file: ${outputFile}`);
    };

    return {
        parseGpxContent,
        parseGpxFile,          // Node.js
        parseGpxFileFromUpload, // Browser
        createConsolidatedGpx
    };
};

const parseArgs = () => {
    const args = process.argv.slice(2);
    const options = {};
    
    for (let i = 0; i < args.length; i += 2) {
        const key = args[i].replace('--', '');
        const value = args[i + 1];
        options[key] = value;
    }
    
    const filterDate = options['filter-date'] ? new Date(options['filter-date']) : null;
    
    const parseTime = (timeStr) => {
        if (!timeStr) return null;
        const [hours, minutes] = timeStr.split(':').map(Number);
        const date = new Date();
        date.setHours(hours, minutes, 0, 0);
        return date;
    };
    
    const startTime = parseTime(options['start-time']);
    const endTime = parseTime(options['end-time']);
    
    const inputDirectory = options.input || './gpx_files';
    if (!fs.existsSync(inputDirectory) || !fs.statSync(inputDirectory).isDirectory()) {
        console.error(`Input directory ${inputDirectory} does not exist or is not a directory.`);
        process.exit(1);
    }
    
    // Find GPX files
    const gpxFiles = fs.readdirSync(inputDirectory)
        .filter(file => file.endsWith('.gpx'))
        .map(file => path.join(inputDirectory, file));
    
    if (gpxFiles.length === 0) {
        console.error(`No GPX files found in ${inputDirectory}`);
        process.exit(1);
    }
    console.log(`Found ${gpxFiles.length} GPX files to process`);
    
    const outputFile = options.output || './consolidated.gpx';
    if (fs.existsSync(outputFile)) {
        console.error(`Output file ${outputFile} already exists.`);
        process.exit(1);
    }
    
    if (filterDate) {
        console.log(`Filtering tracks to only include data from ${filterDate.toDateString()}`);
    }
    if (startTime && endTime) {
        console.log(`between ${startTime.toTimeString().substr(0, 5)} and ${endTime.toTimeString().substr(0, 5)}`);
    }
    
    return { filterDate, startTime, endTime, gpxFiles, outputFile };
};


const main = () => {
    const gpxProcessor = createGpxProcessor();
    
    const { filterDate, startTime, endTime, gpxFiles, outputFile } = parseArgs();
    gpxProcessor.createConsolidatedGpx(gpxFiles, outputFile, filterDate, startTime, endTime);
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { createGpxProcessor, createCliParser };
    if (require.main === module) {
        main();
    }
}