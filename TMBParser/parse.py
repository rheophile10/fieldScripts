import struct
import json
from typing import Dict, List, Any, Optional, Tuple

def parse_tmb_to_dict(file_path: str) -> Dict[str, Any]:
    """
    Convert TM-7 .tmb file to structured Python dictionary.
    
    Returns:
        Dictionary with 'header' and 'readings' sections
    """
    
    with open(file_path, "rb") as f:
        raw_data = f.read()
    
    # Parse header section
    header = parse_header(raw_data)
    
    # Parse data blocks
    readings = parse_data_blocks(raw_data)
    
    return {
        'header': header,
        'readings': readings
    }

def parse_header(raw_data: bytes) -> Dict[str, str]:
    """Extract header information from TM-7 file"""
    header = {}
    lines = raw_data.split(b'\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith(b'#'):
            try:
                header_line = line.decode('utf-8', errors='replace')
                if '\t' in header_line:
                    key, value = header_line[1:].split('\t', 1)
                    header[key.strip()] = value.strip()
                else:
                    # Handle header lines without tabs
                    header[header_line[1:].strip()] = ""
            except:
                continue
        elif line.startswith(b'LogStart'):
            header['LogStart'] = line.decode('utf-8', errors='replace')
    
    return header

def convert_nmea_coordinate(coord_str: str, direction: str) -> Optional[float]:
    """Convert NMEA coordinate format to decimal degrees."""
    if not coord_str or not direction:
        return None
        
    try:
        # NMEA format: DDMM.MMMMM or DDDMM.MMMMM
        if len(coord_str.split('.')[0]) == 4:  # Latitude (DDMM)
            degrees = int(coord_str[:2])
            minutes = float(coord_str[2:])
        else:  # Longitude (DDDMM)
            degrees = int(coord_str[:3])
            minutes = float(coord_str[3:])
            
        decimal = degrees + (minutes / 60.0)
        
        # Apply direction
        if direction in ['S', 'W']:
            decimal = -decimal
            
        return decimal
    except (ValueError, IndexError):
        return None

def parse_rmc_sentence(parts: List[str]) -> Dict[str, Any]:
    """Parse RMC (Recommended Minimum Course) NMEA sentence."""
    try:
        return {
            'time_utc': parts[1] if len(parts) > 1 else None,
            'status': parts[2] if len(parts) > 2 else None,
            'latitude': convert_nmea_coordinate(parts[3], parts[4]) if len(parts) > 4 else None,
            'longitude': convert_nmea_coordinate(parts[5], parts[6]) if len(parts) > 6 else None,
            'speed_knots': float(parts[7]) if len(parts) > 7 and parts[7] else None,
            'course': float(parts[8]) if len(parts) > 8 and parts[8] else None,
            'date': parts[9] if len(parts) > 9 else None,
            'magnetic_variation': parts[10] if len(parts) > 10 else None,
        }
    except (ValueError, IndexError):
        return {}

def parse_gga_sentence(parts: List[str]) -> Dict[str, Any]:
    """Parse GGA (Global Positioning System Fix Data) NMEA sentence."""
    try:
        return {
            'time_utc': parts[1] if len(parts) > 1 else None,
            'latitude': convert_nmea_coordinate(parts[2], parts[3]) if len(parts) > 3 else None,
            'longitude': convert_nmea_coordinate(parts[4], parts[5]) if len(parts) > 5 else None,
            'fix_quality': int(parts[6]) if len(parts) > 6 and parts[6] else None,
            'num_satellites': int(parts[7]) if len(parts) > 7 and parts[7] else None,
            'hdop': float(parts[8]) if len(parts) > 8 and parts[8] else None,
            'altitude': float(parts[9]) if len(parts) > 9 and parts[9] else None,
            'altitude_units': parts[10] if len(parts) > 10 else None,
            'geoid_height': float(parts[11]) if len(parts) > 11 and parts[11] else None,
            'geoid_units': parts[12] if len(parts) > 12 else None,
        }
    except (ValueError, IndexError):
        return {}

def extract_position_updates(binary_data: bytes) -> Tuple[List[Dict[str, Any]], bytes]:
    """Extract position updates in chronological sequence"""
    
    position_updates = []
    used_positions = set()
    
    # Find all position markers and their positions
    markers_found = []
    
    for pos in range(len(binary_data) - 3):
        # Check for Y# marker
        if binary_data[pos:pos+2] == b'\x59\x23':
            if pos >= 2:
                y_val = struct.unpack('<H', binary_data[pos-2:pos])[0]
                markers_found.append((pos-2, 'Y', y_val))
        
        # Check for X# marker  
        elif binary_data[pos:pos+2] == b'\x58\x23':
            if pos >= 2:
                x_val = struct.unpack('<H', binary_data[pos-2:pos])[0]
                markers_found.append((pos-2, 'X', x_val))
    
    # Sort by byte position to maintain chronological order
    markers_found.sort(key=lambda x: x[0])
    
    # Convert to list of dicts and mark used positions
    for byte_pos, marker_type, value in markers_found:
        position_updates.append({'type': marker_type, 'value': value})
        # Mark these 4 bytes as used (2 bytes value + 2 bytes marker)
        used_positions.update([byte_pos, byte_pos+1, byte_pos+2, byte_pos+3])
    
    # Calculate remaining undefined data
    remaining_bytes = bytearray()
    for i in range(len(binary_data)):
        if i not in used_positions:
            remaining_bytes.append(binary_data[i])
    
    return position_updates, bytes(remaining_bytes)

def parse_data_blocks(raw_data: bytes) -> List[Dict[str, Any]]:
    """Parse data into blocks containing s, g, and m records"""
    lines = raw_data.split(b'\n')
    blocks = []
    current_block = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
            
        # Skip header lines
        if line.startswith(b'#') or line.startswith(b'LogStart'):
            i += 1
            continue
        
        # Sensor status line (s,) - starts a new block
        if line.startswith(b's,'):
            if current_block is not None:
                blocks.append(current_block)
            
            current_block = {
                'gps_data': {'GNRMC': None, 'GNGGA': None},
                'magnetometer_data': None,
                'position_updates': [],
                'undefined_bytes': 0
            }
        
        # GPS lines (g,)
        elif line.startswith(b'g,'):
            if current_block is None:
                # Create block if GPS comes first
                current_block = {
                    'gps_data': {'GNRMC': None, 'GNGGA': None},
                    'magnetometer_data': None,
                    'position_updates': [],
                    'undefined_bytes': 0
                }
            
            gps_data = parse_gps_line_enhanced(line)
            if gps_data:
                sentence_type = gps_data.get('sentence_type')
                if sentence_type in ['RMC', 'GGA']:
                    current_block['gps_data'][f'GN{sentence_type}'] = gps_data
        
        # Magnetometer lines (m,)
        elif line.startswith(b'm,'):
            if current_block is None:
                current_block = {
                    'gps_data': {'GNRMC': None, 'GNGGA': None},
                    'magnetometer_data': None,
                    'position_updates': [],
                    'undefined_bytes': 0
                }
            
            # Extract magnetometer data, position updates, and undefined bytes
            mag_data, position_updates, undefined_bytes = parse_magnetometer_with_position_block(lines, i)
            current_block['magnetometer_data'] = mag_data
            current_block['position_updates'] = position_updates
            current_block['undefined_bytes'] = len(undefined_bytes)
            
            # Skip the lines we processed
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if (next_line.startswith(b'g,') or 
                    next_line.startswith(b's,') or 
                    next_line.startswith(b'm,') or
                    next_line.startswith(b'#')):
                    break
                j += 1
            i = j - 1
        
        i += 1
    
    # Add the last block
    if current_block is not None:
        blocks.append(current_block)
    
    return blocks

def parse_gps_line_enhanced(line: bytes) -> Optional[Dict[str, Any]]:
    """Parse GPS line with enhanced NMEA parsing"""
    try:
        gps_line = line.decode('utf-8', errors='replace')
        if not gps_line.startswith('g,'):
            return None
            
        parts = gps_line.split(',', 2)
        if len(parts) < 3:
            return None
            
        timestamp = float(parts[1])
        nmea_sentence = parts[2].strip()
        
        gps_entry = {
            'timestamp': timestamp,
            'nmea_sentence': nmea_sentence,
            'sentence_type': None,
            'parsed_data': {}
        }
        
        # Parse NMEA sentence
        if nmea_sentence.startswith('$GN'):
            sentence_parts = nmea_sentence.split(',')
            sentence_type = sentence_parts[0][3:6]  # Extract GGA, RMC, etc.
            gps_entry['sentence_type'] = sentence_type
            
            # Parse specific NMEA sentences
            if sentence_type == 'RMC':
                gps_entry['parsed_data'] = parse_rmc_sentence(sentence_parts)
            elif sentence_type == 'GGA':
                gps_entry['parsed_data'] = parse_gga_sentence(sentence_parts)
                
        return gps_entry
    except:
        return None

def parse_magnetometer_with_position_block(lines: List[bytes], start_idx: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]], bytes]:
    """Parse magnetometer block and extract position updates and undefined bytes"""
    line = lines[start_idx].strip()
    
    # Extract timestamp
    parts = line.split(b' ', 1)
    timestamp = float(parts[0][2:].decode('utf-8', errors='replace'))
    
    # Collect all binary data for this block
    binary_data = parts[1] if len(parts) > 1 else b''
    
    j = start_idx + 1
    while j < len(lines):
        next_line = lines[j].strip()
        if (next_line.startswith(b'g,') or 
            next_line.startswith(b's,') or 
            next_line.startswith(b'm,') or
            next_line.startswith(b'#')):
            break
        
        if next_line:
            binary_data += next_line
        j += 1
    
    # Extract clean magnetometer readings (32-bit integers)
    clean_readings = []
    pos = 0
    
    # Read 32-bit readings until we hit bad data
    while pos + 4 <= len(binary_data):
        try:
            reading = struct.unpack('<I', binary_data[pos:pos+4])[0]
            if 590000000 <= reading <= 600000000:
                clean_readings.append(reading)
                pos += 4
            else:
                break  # Stop at first bad reading
        except:
            break
    
    # Extract position updates from remaining binary data
    position_binary = binary_data[pos:]
    position_updates, truly_undefined = extract_position_updates(position_binary)
    
    magnetometer_data = {
        'timestamp': timestamp,
        'readings': clean_readings
    }
    
    return magnetometer_data, position_updates, truly_undefined

# Example usage
if __name__ == "__main__":
    # Parse the TMB file
    data = parse_tmb_to_dict("example.TMB")
    
    print(f"Header contains {len(data['header'])} parameters")
    print(f"Found {len(data['readings'])} data blocks")
    
    # Show first block structure
    if data['readings']:
        block = data['readings'][0]
        print(f"\nFirst block:")
        print(f"  GPS GNRMC: {'Yes' if block['gps_data']['GNRMC'] else 'No'}")
        print(f"  GPS GNGGA: {'Yes' if block['gps_data']['GNGGA'] else 'No'}")
        print(f"  Magnetometer readings: {len(block['magnetometer_data']['readings']) if block['magnetometer_data'] else 0}")
        print(f"  Position updates: {len(block['position_updates'])}")
        print(f"  Undefined bytes: {block['undefined_bytes']}")
        
        if block['position_updates']:
            print(f"  First 5 position updates: {block['position_updates'][:5]}")
    
    # Export to JSON
    output_filename = "tm7_parsed_data.json"
    with open(output_filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"\nData exported to {output_filename}")
    
    # Summary statistics
    total_mag_readings = sum(len(block.get('magnetometer_data', {}).get('readings', [])) for block in data['readings'])
    total_position_updates = sum(len(block.get('position_updates', [])) for block in data['readings'])
    
    print(f"\nSummary:")
    print(f"  Total magnetometer readings: {total_mag_readings:,}")
    print(f"  Total position updates: {total_position_updates:,}")