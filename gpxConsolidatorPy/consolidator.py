import os
import glob
from pathlib import Path
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import argparse
from collections import defaultdict
import datetime
import copy
from typing import List, Tuple, Dict, Optional

GPX_NS: Dict[str, str] = {'gpx': 'http://www.topografix.com/GPX/1/1'}

def filter_track_by_time(track: ET.Element, 
                         filter_date: datetime.date, 
                         start_time: datetime.time, 
                         end_time: datetime.time) -> Optional[ET.Element]:
    """
    Filter a track to only include track points within the specified date and time range.
    
    Args:
        track: Track element from GPX file
        filter_date: Date to filter by
        start_time: Start time for the time range
        end_time: End time for the time range
        
    Returns:
        Filtered track or None if no points remain
    """
    filtered_track = copy.deepcopy(track)
    
    segments = filtered_track.findall('.//gpx:trkseg', GPX_NS)
    segments_to_remove = []
    
    for segment in segments:
        points = segment.findall('./gpx:trkpt', GPX_NS)
        points_to_remove = []
        
        for point in points:
            time_elem = point.find('./gpx:time', GPX_NS)
            if time_elem is None or not time_elem.text:
                points_to_remove.append(point)
                continue
                
            try:
                point_time = datetime.datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))

                point_time = point_time.astimezone()

                if point_time.date() != filter_date:
                    points_to_remove.append(point)
                    continue

                point_time_only = point_time.time()
                if point_time_only < start_time or point_time_only > end_time:
                    points_to_remove.append(point)
            except (ValueError, TypeError) as e:
                print(f"Warning: Failed to parse time {time_elem.text}: {e}")
                points_to_remove.append(point)
        
        for point in points_to_remove:
            segment.remove(point)
            
        if len(segment.findall('./gpx:trkpt', GPX_NS)) == 0:
            segments_to_remove.append(segment)
    
    for segment in segments_to_remove:
        filtered_track.remove(segment)
    
    if len(filtered_track.findall('.//gpx:trkseg', GPX_NS)) == 0:
        return None
        
    return filtered_track

def parse_gpx_file(file_path: str, 
                filter_date: Optional[datetime.date] = None, 
                start_time: Optional[datetime.time] = None, 
                end_time: Optional[datetime.time] = None) -> Tuple[List[Tuple[ET.Element, str]], List[Tuple[ET.Element, str]]]:
    """
    Parse a GPX file and extract all tracks and waypoints.
    
    Args:
        file_path: Path to GPX file
        filter_date: Date to filter tracks by
        start_time: Start time for time range filtering
        end_time: End time for time range filtering
        
    Returns:
        Tuple containing (tracks_list, waypoints_list) where each element is a list of (element, source_filename) tuples
    """
    try:
        base_filename = os.path.basename(file_path)
        base_name = os.path.splitext(base_filename)[0]
        
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        tracks = root.findall('.//gpx:trk', GPX_NS)
        track_results = []
        
        if filter_date and start_time and end_time:
            for track in tracks:
                filtered_track = filter_track_by_time(track, filter_date, start_time, end_time)
                if filtered_track is not None:
                    track_results.append((filtered_track, base_name))
        else:
            track_results = [(track, base_name) for track in tracks]
        
        waypoints = root.findall('.//gpx:wpt', GPX_NS)
        waypoint_results = [(waypoint, base_name) for waypoint in waypoints]
        
        filtered_msg = " (time-filtered)" if filter_date else ""
        print(f"Extracted {len(track_results)} tracks{filtered_msg} and {len(waypoints)} waypoints from {file_path}")
        return (track_results, waypoint_results)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return ([], [])

def create_consolidated_gpx(output_file, track_data, waypoint_data, always_rename):
    """
    Create a new GPX file with all tracks and waypoints, handling name conflicts.
    
    Args:
        output_file (str): Path to output file
        track_data (list): List of (track, source_filename) tuples
        waypoint_data (list): List of (waypoint, source_filename) tuples
        always_rename (bool): Whether to always rename elements with source filename
        
    Returns:
        tuple: (number of tracks, number of waypoints) added to output file
    """
    root = ET.Element('gpx')
    root.set('version', '1.1')
    root.set('creator', 'GPX Track and Waypoint Consolidator')
    
    root.set('xmlns', 'http://www.topografix.com/GPX/1/1')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xsi:schemaLocation', 'http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd')
    
    metadata = ET.SubElement(root, 'metadata')
    name = ET.SubElement(metadata, 'name')
    name.text = 'Consolidated GPX Tracks and Waypoints'
    
    track_names = defaultdict(int)
    waypoint_names = defaultdict(int)

    for waypoint, source_file in waypoint_data:
        name_element = waypoint.find('./gpx:name', GPX_NS)
        original_name = name_element.text if name_element is not None else "Unnamed Waypoint"
        
        waypoint_names[original_name] += 1
        
        if waypoint_names[original_name] > 1 or always_rename:
            if name_element is None:
                name_element = ET.SubElement(waypoint, 'name')
            
            if always_rename:
                name_element.text = f"{original_name} ({source_file})"
            else:
                name_element.text = f"{original_name} ({source_file}_{waypoint_names[original_name]})"
        
        root.append(waypoint)

    for track, source_file in track_data:
        name_element = track.find('./gpx:name', GPX_NS)
        original_name = name_element.text if name_element is not None else "Unnamed Track"
        
        track_names[original_name] += 1
        
        if track_names[original_name] > 1 or always_rename:
            if name_element is None:
                name_element = ET.SubElement(track, 'name')
            
            if always_rename:
                name_element.text = f"{original_name} ({source_file})"
            else:
                name_element.text = f"{original_name} ({source_file}_{track_names[original_name]})"
        
        root.append(track)
    
    tree = ET.ElementTree(root)
    
    ET.indent(tree, space="  ")
        
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    print(f"Successfully created consolidated file with {len(track_data)} tracks and {len(waypoint_data)} waypoints: {output_file}")
    return (len(track_data), len(waypoint_data))

def main() -> None:
    today: datetime.date = datetime.date.today()
    default_start_time: datetime.time = datetime.time(6, 0)
    default_end_time: datetime.time = datetime.time(20, 0)
    
    parser = argparse.ArgumentParser(description='Consolidate tracks and waypoints from multiple GPX files into one.')
    parser.add_argument('-i', '--input', default='./gpx_files', 
                        help='Directory containing GPX files (default: ./gpx_files)')
    parser.add_argument('-o', '--output', default='./consolidated_gpx.gpx',
                        help='Output file path (default: ./consolidated_gpx.gpx)')
    parser.add_argument('--rename', action='store_true',
                        help='Always rename elements with source filename, even if no conflicts')
    parser.add_argument('--tracks-only', action='store_true',
                        help='Process only tracks, ignore waypoints')
    parser.add_argument('--waypoints-only', action='store_true',
                        help='Process only waypoints, ignore tracks')
    
    parser.add_argument('--filter-date', type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d').date(),
                        default=today,
                        help='Filter tracks to only include points from this date (YYYY-MM-DD, default: today)')
    parser.add_argument('--start-time', type=lambda s: datetime.datetime.strptime(s, '%H:%M').time(),
                        default=default_start_time,
                        help='Filter tracks to only include points after this time (HH:MM, default: 06:00)')
    parser.add_argument('--end-time', type=lambda s: datetime.datetime.strptime(s, '%H:%M').time(),
                        default=default_end_time,
                        help='Filter tracks to only include points before this time (HH:MM, default: 20:00)')
    parser.add_argument('--no-time-filter', action='store_true',
                        help='Disable time filtering of track points')
                        
    args = parser.parse_args()
    
    input_directory: str = args.input
    output_file: str = args.output
    always_rename: bool = args.rename
    
    filter_date: Optional[datetime.date] = None if args.no_time_filter else args.filter_date
    start_time: Optional[datetime.time] = None if args.no_time_filter else args.start_time
    end_time: Optional[datetime.time] = None if args.no_time_filter else args.end_time
    
    if filter_date:
        print(f"Filtering tracks to only include points from {filter_date} between {start_time.strftime('%H:%M')} and {end_time.strftime('%H:%M')}")
    
    Path(input_directory).mkdir(parents=True, exist_ok=True)
    
    gpx_files: List[str] = glob.glob(os.path.join(input_directory, '*.gpx'))
    
    if not gpx_files:
        print(f"No GPX files found in {input_directory}")
        return
    
    print(f"Found {len(gpx_files)} GPX files to process")
    
    all_track_data: List[Tuple[ET.Element, str]] = []
    all_waypoint_data: List[Tuple[ET.Element, str]] = []
    
    parse_params: List[Tuple[str, Optional[datetime.date], Optional[datetime.time], Optional[datetime.time]]] = [
        (file_path, filter_date, start_time, end_time) for file_path in gpx_files
    ]
    
    with ThreadPoolExecutor() as executor:
        results: List[Tuple[List[Tuple[ET.Element, str]], List[Tuple[ET.Element, str]]]] = list(
            executor.map(lambda p: parse_gpx_file(*p), parse_params)
        )
        
    for track_list, waypoint_list in results:
        if not args.waypoints_only:
            all_track_data.extend(track_list)
        if not args.tracks_only:
            all_waypoint_data.extend(waypoint_list)
    
    if not all_track_data and not all_waypoint_data:
        print("No tracks or waypoints found in any of the input files")
        return
    
    print(f"Total of {len(all_track_data)} tracks and {len(all_waypoint_data)} waypoints found across all files")
    
    num_tracks, num_waypoints = create_consolidated_gpx(output_file, all_track_data, all_waypoint_data, always_rename)
    
    if num_tracks > 0 or num_waypoints > 0:
        print(f"Success! Consolidated {num_tracks} tracks and {num_waypoints} waypoints into {output_file}")

if __name__ == "__main__":
    main()