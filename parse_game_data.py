#!/usr/bin/env python3
"""
Parse DTA game INI files and generate JSON data for the dashboard.
Extracts units, buildings, and their stats from Rules.ini and Enhance.ini.
"""

import os
import json
import re
from pathlib import Path
from collections import defaultdict

class INIParser:
    def __init__(self):
        self.data = {}
        self.sections = {}
        self.current_section = None
        
    def parse_file(self, filepath):
        """Parse a single INI file."""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith(';'):
                    continue
                
                # Section header (handle comments after bracket: [SECTION]    ;comment)
                if line.startswith('['):
                    # Extract section name, handling comments after the closing bracket
                    bracket_end = line.find(']')
                    if bracket_end != -1:
                        self.current_section = line[1:bracket_end]
                        if self.current_section not in self.sections:
                            self.sections[self.current_section] = {}
                        continue
                
                # Key-value pair
                if '=' in line and self.current_section:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.split(';')[0].strip()  # Remove inline comments
                    self.sections[self.current_section][key] = value

def resolve_entity_with_base(entity_id, sections, visited=None):
    """
    Resolve an entity's data including $Inherits inheritance.
    $Inherits allows entities to inherit from other entities.
    """
    if visited is None:
        visited = set()
    
    if entity_id in visited:
        return {}  # Prevent infinite recursion
    visited.add(entity_id)
    
    if entity_id not in sections:
        return {}
    
    entity_data = sections[entity_id].copy()
    
    # Check for $Inherits and resolve recursively
    if '$Inherits' in entity_data:
        base_id = entity_data['$Inherits']
        base_data = resolve_entity_with_base(base_id, sections, visited)
        # Base data goes first, entity data overrides it
        resolved = base_data.copy()
        resolved.update(entity_data)
        return resolved
    
    return entity_data

def separate_naval_vehicles(vehicles):
    """Separate vehicles into Naval (Naval=yes) and regular vehicles."""
    naval = {}
    regular = {}
    for entity_id, entity_data in vehicles.items():
        if entity_data.get('Naval', '').lower() == 'yes':
            naval[entity_id] = entity_data
        else:
            regular[entity_id] = entity_data
    return regular, naval

def extract_entities(parser, entity_type):
    """
    Extract entities of a specific type from parsed INI data.
    entity_type: 'InfantryTypes', 'VehicleTypes', 'AircraftTypes', 'BuildingTypes'
    """
    if entity_type not in parser.sections:
        return {}
    
    entity_list = parser.sections[entity_type]
    entities = {}
    
    # Sort by trying to parse as int, fallback to string
    def sort_key(item):
        key = item[0]
        try:
            return (0, int(key))
        except ValueError:
            return (1, key)
    
    for idx, entity_id in sorted(entity_list.items(), key=sort_key):
        if entity_id in parser.sections:
            # Resolve BaseSection inheritance
            resolved = resolve_entity_with_base(entity_id, parser.sections)
            if resolved.get('InvisibleInGame', '').lower() != 'yes':
                entities[entity_id] = resolved
    
    return entities

def get_entity_type(entity_id, infantry, vehicles, naval, aircraft, buildings):
    """Determine the type of entity."""
    if entity_id in infantry:
        return 'Infantry'
    elif entity_id in naval:
        return 'Naval'
    elif entity_id in vehicles:
        return 'Vehicle'
    elif entity_id in aircraft:
        return 'Aircraft'
    elif entity_id in buildings:
        return 'Building'
    else:
        return 'Unknown'

    return 'Unknown'

def normalize_value(value):
    """Normalize yes/no/true/false to Yes/No and format comma-separated lists."""
    if isinstance(value, str):
        if value.lower() in ('yes', 'true'):
            return 'Yes'
        elif value.lower() in ('no', 'false'):
            return 'No'
        # Add spaces after commas in comma-separated lists
        if ',' in value:
            return ', '.join(part.strip() for part in value.split(','))
    return value

def format_armor_type(value):
    """Format armor type by capitalizing and replacing underscores with spaces."""
    if isinstance(value, str):
        # Replace underscores with spaces
        value = value.replace('_', ' ')
        # Capitalize each word
        value = ' '.join(word.capitalize() for word in value.split())
    return value

def rename_weapon_modifiers(weapon_data):
    """Rename Modifier.* keys to descriptive names like 'Damage VS Heavy Armor'."""
    renamed_data = {}
    for key, value in weapon_data.items():
        if key.startswith('Modifier.'):
            # Extract the modifier type (the part after the dot)
            modifier_type = key[9:]  # Remove 'Modifier.' prefix
            if modifier_type.lower() == 'none':
                new_key = 'Damage VS No Armor'
            else:
                # Capitalize the modifier type and format it
                formatted_type = ' '.join(word.capitalize() for word in modifier_type.split('_'))
                new_key = f'Damage VS {formatted_type} Armor'
            renamed_data[new_key] = value
        else:
            renamed_data[key] = value
    return renamed_data

def get_weapon_data(weapon_id, all_sections):
    """Fetch weapon data including projectile and warhead references with full details."""
    if weapon_id not in all_sections:
        return None
    
    weapon_data = resolve_entity_with_base(weapon_id, all_sections)
    
    # Rename Modifier.* keys to descriptive names
    weapon_data = rename_weapon_modifiers(weapon_data)
    
    weapon_info = {
        'ID': weapon_id,
        'Name': weapon_data.get('Name', weapon_id),
        'Damage': normalize_value(weapon_data.get('Damage', '—')),
        'ROF': normalize_value(weapon_data.get('ROF', '—')),
        'Range': normalize_value(weapon_data.get('Range', '—')),
        'Projectile': normalize_value(weapon_data.get('Projectile', '—')),
        'Warhead': normalize_value(weapon_data.get('Warhead', '—')),
        'Speed': normalize_value(weapon_data.get('Speed', '—')),
    }
    
    # Expand Projectile details
    if weapon_info['Projectile'] and weapon_info['Projectile'] != '—':
        projectile_id = weapon_data.get('Projectile')
        if projectile_id in all_sections:
            proj_data = resolve_entity_with_base(projectile_id, all_sections)
            # Normalize projectile properties
            normalized_proj_props = {k: normalize_value(v) for k, v in proj_data.items() 
                                     if k not in ['ID', 'Name', '$Inherits'] and v}
            weapon_info['ProjectileDetails'] = {
                'ID': projectile_id,
                'Name': proj_data.get('Name', projectile_id),
                'Properties': normalized_proj_props
            }
    
    # Expand Warhead details
    if weapon_info['Warhead'] and weapon_info['Warhead'] != '—':
        warhead_id = weapon_data.get('Warhead')
        if warhead_id in all_sections:
            wh_data = resolve_entity_with_base(warhead_id, all_sections)
            # First apply modifier renaming, then normalize
            wh_data_renamed = rename_weapon_modifiers(wh_data)
            # Normalize warhead properties
            normalized_wh_props = {k: normalize_value(v) for k, v in wh_data_renamed.items() 
                                   if k not in ['ID', 'Name', '$Inherits'] and v}
            weapon_info['WarheadDetails'] = {
                'ID': warhead_id,
                'Name': wh_data.get('Name', warhead_id),
                'Properties': normalized_wh_props
            }
    
    # Add all modifier properties (Damage VS * Armor)
    for key, value in weapon_data.items():
        if key.startswith('Damage VS'):
            weapon_info[key] = normalize_value(value)
    
    return weapon_info

def convert_prerequisite_to_names(prerequisite_str, all_sections):
    """Convert prerequisite IDs to building names."""
    if not prerequisite_str or prerequisite_str.lower() == 'none':
        return 'None'
    
    # Handle comma-separated or slash-separated lists
    building_ids = re.split(r'[,/]', prerequisite_str)
    names = []
    for bid in building_ids:
        bid = bid.strip()
        if bid and bid in all_sections:
            building_data = all_sections[bid].get('Name', bid)
            names.append(building_data)
        elif bid:
            names.append(bid)
    
    return ' / '.join(names) if names else 'None'

def format_entity_data(entity_id, entity_data, entity_type, enhanced=False, all_sections=None):
    """Format entity data with all properties included, weapon references resolved."""
    if all_sections is None:
        all_sections = {}
    
    editor_name = entity_data.get('EditorName', '')
    name = editor_name if editor_name.startswith('AI ') else entity_data.get('Name', entity_id)
    
    # Normalize yes/no values in a copy of entity_data
    normalized_data = {}
    for key, value in entity_data.items():
        normalized_value = normalize_value(value)
        # Special handling for Armor type - capitalize and replace underscores
        if key == 'Armor':
            normalized_value = format_armor_type(normalized_value)
        normalized_data[key] = normalized_value
    
    # Remove Locomotor from display
    normalized_data_display = {k: v for k, v in normalized_data.items() if k != 'Locomotor'}
    
    result = {
        'ID': entity_id,
        'Name': name,
        'Type': entity_type,
        'IsEnhanced': enhanced,
        'AllProperties': normalized_data_display,  # Normalized, Locomotor removed
        'Weapons': {},  # Will be populated below
    }
    
    # Resolve weapon references
    for weapon_slot in ['Primary', 'Secondary', 'Elite']:
        if weapon_slot in entity_data and entity_data[weapon_slot]:
            weapon_id = entity_data[weapon_slot]
            weapon_data = get_weapon_data(weapon_id, all_sections)
            if weapon_data:
                result['Weapons'][weapon_slot] = weapon_data
    
    # Convert Prerequisite to building names
    if 'Prerequisite' in normalized_data_display:
        result['AllProperties']['Prerequisite'] = convert_prerequisite_to_names(
            entity_data.get('Prerequisite', ''), all_sections
        )
    
    return result

def main():
    project_path = Path(__file__).resolve().parent
    ini_path = project_path / 'INI'
    
    # Parse classic rules
    print("Parsing Rules.ini (Classic mode)...")
    parser_classic = INIParser()
    parser_classic.parse_file(str(ini_path / 'Rules.ini'))
    
    # Parse enhanced rules
    print("Parsing Enhance.ini (Enhanced mode)...")
    parser_enhanced = INIParser()
    parser_enhanced.parse_file(str(ini_path / 'Enhance.ini'))
    
    # Extract entities with BaseSection resolution
    print("Extracting entities...")
    infantry_classic = extract_entities(parser_classic, 'InfantryTypes')
    vehicles_all_classic = extract_entities(parser_classic, 'VehicleTypes')
    aircraft_classic = extract_entities(parser_classic, 'AircraftTypes')
    buildings_classic = extract_entities(parser_classic, 'BuildingTypes')
    
    # Separate naval vehicles from regular vehicles
    vehicles_classic, naval_classic = separate_naval_vehicles(vehicles_all_classic)
    
    # Prepare output structure
    output = {
        'game': 'Dawn of the Tiberium Age',
        'modes': {
            'classic': {
                'buildings': {},
                'infantry': {},
                'vehicles': {},
                'naval': {},
                'aircraft': {},
            },
            'enhanced': {
                'buildings': {},
                'infantry': {},
                'vehicles': {},
                'naval': {},
                'aircraft': {},
            }
        },
        'metadata': {
            'total_buildings': len(buildings_classic),
            'total_infantry': len(infantry_classic),
            'total_vehicles': len(vehicles_classic),
            'total_naval': len(naval_classic),
            'total_aircraft': len(aircraft_classic),
        }
    }
    
    # Process classic mode
    print("Processing classic mode...")
    for ent_id, ent_data in buildings_classic.items():
        formatted = format_entity_data(ent_id, ent_data, 'Building', False, parser_classic.sections)
        output['modes']['classic']['buildings'][ent_id] = formatted
    
    for ent_id, ent_data in infantry_classic.items():
        formatted = format_entity_data(ent_id, ent_data, 'Infantry', False, parser_classic.sections)
        output['modes']['classic']['infantry'][ent_id] = formatted
    
    for ent_id, ent_data in vehicles_classic.items():
        formatted = format_entity_data(ent_id, ent_data, 'Vehicle', False, parser_classic.sections)
        output['modes']['classic']['vehicles'][ent_id] = formatted
    
    for ent_id, ent_data in naval_classic.items():
        formatted = format_entity_data(ent_id, ent_data, 'Naval', False, parser_classic.sections)
        output['modes']['classic']['naval'][ent_id] = formatted
    
    for ent_id, ent_data in aircraft_classic.items():
        formatted = format_entity_data(ent_id, ent_data, 'Aircraft', False, parser_classic.sections)
        output['modes']['classic']['aircraft'][ent_id] = formatted
    
    # Process enhanced mode by merging enhanced overrides on top of classic
    print("Processing enhanced mode...")
    
    # Create merged sections: classic as base + enhanced as overrides
    def merge_sections_for_enhanced(classic_sections, enhanced_sections):
        """Merge enhanced overrides on top of classic sections."""
        merged = {}
        for section_id, section_data in classic_sections.items():
            merged[section_id] = section_data.copy()
        
        # Apply enhanced overrides
        for section_id, section_data in enhanced_sections.items():
            if section_id not in merged:
                merged[section_id] = {}
            merged[section_id].update(section_data)
        
        return merged
    
    merged_sections = merge_sections_for_enhanced(
        parser_classic.sections,
        parser_enhanced.sections
    )
    
    # Re-extract with merged sections for enhanced mode
    def extract_entities_from_merged(entity_list_classic, merged_sections):
        """Extract entities using the merged sections."""
        entities = {}
        for idx, entity_id in entity_list_classic:
            if entity_id in merged_sections:
                resolved = resolve_entity_with_base(entity_id, merged_sections)
                if resolved.get('InvisibleInGame', '').lower() != 'yes':
                    entities[entity_id] = resolved
        return entities
    
    # Get the entity lists from classic parser
    infantry_list = sorted(
        parser_classic.sections.get('InfantryTypes', {}).items(),
        key=lambda x: (0, int(x[0])) if x[0].isdigit() else (1, x[0])
    )
    vehicles_list = sorted(
        parser_classic.sections.get('VehicleTypes', {}).items(),
        key=lambda x: (0, int(x[0])) if x[0].isdigit() else (1, x[0])
    )
    aircraft_list = sorted(
        parser_classic.sections.get('AircraftTypes', {}).items(),
        key=lambda x: (0, int(x[0])) if x[0].isdigit() else (1, x[0])
    )
    buildings_list = sorted(
        parser_classic.sections.get('BuildingTypes', {}).items(),
        key=lambda x: (0, int(x[0])) if x[0].isdigit() else (1, x[0])
    )
    
    # Extract enhanced with merged sections
    infantry_enhanced = extract_entities_from_merged(infantry_list, merged_sections)
    vehicles_all_enhanced = extract_entities_from_merged(vehicles_list, merged_sections)
    aircraft_enhanced = extract_entities_from_merged(aircraft_list, merged_sections)
    buildings_enhanced = extract_entities_from_merged(buildings_list, merged_sections)
    
    # Separate naval vehicles in enhanced mode too
    vehicles_enhanced, naval_enhanced = separate_naval_vehicles(vehicles_all_enhanced)
    
    # Format enhanced entities
    for ent_id, ent_data in buildings_enhanced.items():
        formatted = format_entity_data(ent_id, ent_data, 'Building', True, merged_sections)
        output['modes']['enhanced']['buildings'][ent_id] = formatted
    
    for ent_id, ent_data in infantry_enhanced.items():
        formatted = format_entity_data(ent_id, ent_data, 'Infantry', True, merged_sections)
        output['modes']['enhanced']['infantry'][ent_id] = formatted
    
    for ent_id, ent_data in vehicles_enhanced.items():
        formatted = format_entity_data(ent_id, ent_data, 'Vehicle', True, merged_sections)
        output['modes']['enhanced']['vehicles'][ent_id] = formatted
    
    for ent_id, ent_data in naval_enhanced.items():
        formatted = format_entity_data(ent_id, ent_data, 'Naval', True, merged_sections)
        output['modes']['enhanced']['naval'][ent_id] = formatted
    
    for ent_id, ent_data in aircraft_enhanced.items():
        formatted = format_entity_data(ent_id, ent_data, 'Aircraft', True, merged_sections)
        output['modes']['enhanced']['aircraft'][ent_id] = formatted
    
    # Write output
    output_path = project_path / 'game_data.json'
    print(f"Writing output to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Successfully parsed and saved game data!")
    print(f"  Buildings: {len(buildings_classic)}")
    print(f"  Infantry: {len(infantry_classic)}")
    print(f"  Vehicles: {len(vehicles_classic)}")
    print(f"  Naval: {len(naval_classic)}")
    print(f"  Aircraft: {len(aircraft_classic)}")

if __name__ == '__main__':
    main()
