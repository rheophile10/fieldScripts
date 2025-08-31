from pathlib import Path
import xml.etree.ElementTree as ET
import argparse
import datetime
from typing import List, Tuple, Dict, Optional
import sys

GPX_NS: Dict[str, str] = {'gpx': 'http://www.topografix.com/GPX/1/1'}
ET.register_namespace('', 'http://www.topografix.com/GPX/1/1')
ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
ET.register_namespace('gpxx', 'http://www.garmin.com/xmlschemas/GpxExtensions/v3')
ET.register_namespace('wptx1', 'http://www.garmin.com/xmlschemas/WaypointExtension/v1')
ET.register_namespace('gpxtpx', 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1')

def generate_unique_track_name(original_name: Optional[str], filter_date: Optional[datetime.date], base_filename: str, unique_names: Dict[str, int]) -> Tuple[str, Dict[str, int]]:
    if filter_date:
        date_str = filter_date.strftime("%b%d")
        # if original_name:
        #     base_name = f"{base_filename}_{date_str}_{original_name}"
        # else:
        #     base_name = f"{base_filename}_{date_str}"
        base_name = f"{base_filename}_{date_str}"
    else:
        base_name = original_name
    if base_name in unique_names:
        counter = unique_names[base_name] + 1
        unique_names[base_name] = counter
        unique_name = f"{base_name}_{counter}"
    else:
        unique_names[base_name] = 1
        unique_name = base_name    
    return unique_name, unique_names

def generate_unique_name(original_name: Optional[str], filter_date: Optional[datetime.date], base_filename: str, unique_names: Dict[str, int]) -> Tuple[str, Dict[str, int]]:
    if filter_date:
        date_str = filter_date.strftime("%b%d")
        if original_name:
            base_name = f"{base_filename}_{date_str}_{original_name}"
        else:
            base_name = f"{base_filename}_{date_str}"
        base_name = f"{base_filename}_{date_str}"
    else: 
        base_name = original_name
    if base_name in unique_names:
        counter = unique_names[base_name] + 1
        unique_names[base_name] = counter
        unique_name = f"{base_name}_{counter}"
    else:
        unique_names[base_name] = 1
        unique_name = base_name    
    return unique_name, unique_names

def get_element_name(element: ET.Element) -> Optional[str]:
    name_elem = element.find('./gpx:name', GPX_NS)
    if name_elem is not None and name_elem.text:
        return name_elem.text.strip()
    return None

def get_waypoint_datetime(waypoint: ET.Element) -> Optional[datetime.datetime]:
    time_elem = waypoint.find('./gpx:time', GPX_NS)
    if time_elem is None or not time_elem.text:
        return None
    try:
        waypoint_time = datetime.datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))
        return waypoint_time
    except (ValueError, TypeError):
        return None

def process_waypoint(waypoint: ET.Element, filter_date: Optional[datetime.date] = None, start_time: Optional[datetime.time] = None, end_time: Optional[datetime.time] = None) -> Optional[ET.Element]:
    waypoint_datetime = get_waypoint_datetime(waypoint)
    if filter_date and waypoint_datetime.date() != filter_date:
        return None
    if start_time and end_time:
        waypoint_time = waypoint_datetime.time()
        if waypoint_time < start_time or waypoint_time > end_time:
            return None
    return waypoint

def process_track(track: ET.Element,
                  name: str, 
                filter_date: Optional[datetime.date]=None, 
                start_time: Optional[datetime.time]=None, 
                end_time: Optional[datetime.time]=None) -> Optional[ET.Element]:
    
    filtered_track = ET.Element('trk', track.attrib)
    filtered_track_name = ET.SubElement(filtered_track, 'name')
    filtered_track_name.text = name
    
    segments = track.findall('.//gpx:trkseg', GPX_NS)
    
    for segment in segments:
        points = segment.findall('./gpx:trkpt', GPX_NS)
        new_segment = ET.Element('trkseg', segment.attrib)
        
        for point in points:
            time_elem = point.find('./gpx:time', GPX_NS)
            if time_elem is None or not time_elem.text:
                continue
                
            point_time = datetime.datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))
            point_time = point_time.astimezone()

            if filter_date is not None and point_time.date() != filter_date:
                continue
            
            if start_time is not None and end_time is not None:
                point_time_only = point_time.time()
                if point_time_only < start_time or point_time_only > end_time:
                    continue
                
            new_segment.append(point)
        
        if len(new_segment.findall('./gpx:trkpt', GPX_NS)) > 0:
            filtered_track.append(new_segment)
        
    return filtered_track

def parse_gpx_file(file_path: Path, unique_track_names: Dict[str, int], unique_waypoint_names: Dict[str, int], unique_route_names: Dict[str, int],
                filter_date: Optional[datetime.date] = None, start_time: Optional[datetime.time] = None, end_time: Optional[datetime.time] = None) -> Tuple[List[ET.Element], List[ET.Element], List[ET.Element], Dict[str, int], Dict[str, int], Dict[str, int]]:
    base_name = file_path.stem
    gpx_root = ET.parse(file_path).getroot()

    tracks = gpx_root.findall('.//gpx:trk', GPX_NS)
    waypoints = gpx_root.findall('.//gpx:wpt', GPX_NS)
    routes = gpx_root.findall('.//gpx:rte', GPX_NS)
    new_waypoints = []
    new_tracks = []
    new_routes = []

    # note all the DRY violations :(

    # gpx isn't valid unless its waypoints and then tracks

    for waypoint in waypoints:
        filtered_waypoint = process_waypoint(waypoint, filter_date, start_time, end_time)
        original_waypoint_name = get_element_name(waypoint)
        waypoint_name, unique_waypoint_names = generate_unique_name(original_waypoint_name, filter_date, base_name, unique_waypoint_names)
        if filtered_waypoint is not None:
            name_elem = filtered_waypoint.find('./gpx:name', GPX_NS)
            if name_elem is not None:
                name_elem.text = waypoint_name
            else:
                name_elem = ET.SubElement(filtered_waypoint, 'name')
                name_elem.text = waypoint_name
            new_waypoints.append(filtered_waypoint)

    
    for route in routes:
        original_name = get_element_name(route)
        route_name, unique_route_names = generate_unique_name(original_name, filter_date, base_name, unique_route_names)

        name_elem = route.find('./gpx:name', GPX_NS)
        if name_elem is not None:
            name_elem.text = route_name
        else:
            name_elem = ET.SubElement(route, 'name')
            name_elem.text = route_name
        
        new_routes.append(route)

    for track in tracks:
        original_track_name = get_element_name(track)
        track_name, unique_track_names = generate_unique_track_name(original_track_name,filter_date, base_name, unique_track_names)
        filtered_track = process_track(track, track_name, filter_date, start_time, end_time)
        if filtered_track is not None:
            new_tracks.append(filtered_track)

    return new_tracks, new_waypoints, new_routes, unique_track_names, unique_waypoint_names, unique_route_names

def create_new_gpx(name: str = 'Consolidated GPX Tracks and Waypoints') -> ET.Element:
    root = ET.Element('gpx')
    
    root.set('creator', 'MapSource 6.16.3')
    root.set('version', '1.1')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xsi:schemaLocation', 'http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd')
    
    metadata = ET.SubElement(root, 'metadata')
    
    if name:
        name_tag = ET.SubElement(metadata, 'name')
        name_tag.text = name
    
    link = ET.SubElement(metadata, 'link')
    link.set('href', 'http://www.garmin.com')
    text_tag = ET.SubElement(link, 'text')
    text_tag.text = 'Garmin International'
    
    time_tag = ET.SubElement(metadata, 'time')
    time_tag.text = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    return root

def create_consolidated_gpx(gpx_files: List[Path], output_file:Path, filter_date: Optional[datetime.date], start_time: Optional[datetime.time], end_time: Optional[datetime.time]) -> None:
    new_gpx_root= create_new_gpx()

    unique_track_names: Dict[str, int] = {}
    unique_waypoint_names: Dict[str, int] = {}
    unique_route_names: Dict[str, int] = {}
    tracks = []
    waypoints = []
    routes = []

    for gpx_file in gpx_files:
        new_tracks, new_waypoints, new_routes, unique_track_names, unique_waypoint_names, unique_route_names = parse_gpx_file(gpx_file, unique_track_names, unique_waypoint_names, unique_route_names, filter_date, start_time, end_time)
        tracks.extend(new_tracks)
        waypoints.extend(new_waypoints)
        routes.extend(new_routes)

    # order of waypoints and tracks in the file actually matters (waypoints, routes, tracks) - if you do it wrong mapsource wont open it

    for waypoint in waypoints:
        new_gpx_root.append(waypoint)

    for route in routes:
        new_gpx_root.append(route)

    for track in tracks:
        new_gpx_root.append(track)

    tree = ET.ElementTree(new_gpx_root)

    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    print(f"Successfully created consolidated file: {output_file}")


def get_cli_args() -> Tuple[Optional[datetime.date], Optional[datetime.time], Optional[datetime.time], List[Path], Path]:
    parser = argparse.ArgumentParser(description='Consolidate tracks and waypoints from multiple GPX files into one.')
    parser.add_argument('--filter-date', type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d').date(), default=None,
                        help='Filter tracks to only include points from this date (YYYY-MM-DD, ex: 2025-08-20)')
    parser.add_argument('--start-time', type=lambda s: datetime.datetime.strptime(s, '%H:%M').time(), default=None,
                        help='Filter tracks to only include points after this time (HH:MM, ex: 06:00)')
    parser.add_argument('--end-time', type=lambda s: datetime.datetime.strptime(s, '%H:%M').time(), default=None,
                        help='Filter tracks to only include points before this time (HH:MM, ex: 20:00)')
    parser.add_argument('--input', default='./gpx_files',
                        help='Directory containing GPX files (default: ./gpx_files)')
    parser.add_argument('--output', default='./consolidated.gpx',
                        help='Output file path (default: ./consolidated.gpx)')
    args = parser.parse_args()
    #validate args
    
    filter_date: Optional[datetime.date] = args.filter_date
    start_time: Optional[datetime.time] = args.start_time
    end_time: Optional[datetime.time] = args.end_time
    if filter_date:
        print(f"Filtering tracks to only include data from {filter_date}")
    if start_time and end_time:
        print(f"between {start_time.strftime('%H:%M')} and {end_time.strftime('%H:%M')}")
    input_directory: Path = Path(args.input)
    if not input_directory.exists() or not input_directory.is_dir():
        print(f"Input directory {input_directory} does not exist or is not a directory.")
        sys.exit(1)
    
    gpx_files: List[Path] = list(input_directory.glob('*.gpx'))
    if not gpx_files:
        print(f"No GPX files found in {input_directory}")
        sys.exit(1)
    print(f"Found {len(gpx_files)} GPX files to process")
    
    output_file: Path = Path(args.output)
    if output_file.exists():
        print(f"Output file {output_file} already exists.")
        sys.exit(1)
    
    return filter_date, start_time, end_time, gpx_files, output_file

def main() -> None:
    filter_date, start_time, end_time, gpx_files, output_file = get_cli_args()
    create_consolidated_gpx(gpx_files, output_file, filter_date, start_time, end_time)

if __name__ == "__main__":
    main()