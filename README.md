# DTA Unit & Structure Stats Dashboard

A comprehensive, interactive web-based dashboard for viewing detailed statistics of all units, structures, and vehicles in **Dawn of the Tiberium Age (DTA)**.

## Features

### 🎮 **Complete Game Data Coverage**
- **56 Infantry Units** - All soldier types with their stats
- **287 Vehicles** - Including tanks, APCs, harvesters, and special units  
- **20 Aircraft** - All air units with specifications
- **457 Buildings** - Every structure in the game

### 🔍 **Powerful Search & Filter System**
- Search by unit/building name or ID
- Filter by entity type (Infantry, Vehicle, Aircraft, Building)
- Quick tab navigation between entity categories
- Real-time search results

### 📊 **Detailed Statistics Display**
Organized into intuitive categories:
- **General Stats** - Name, Cost, Strength, Tech Level
- **Movement & Defense** - Speed, Sight Range, Armor
- **Weapons** - Primary and Secondary weapons, Elite upgrades
- **Abilities** - Veterancy, trainability, special abilities
- **Special Properties** - Owner restrictions, power requirements, etc.

### 🎯 **Dual Game Mode Support**
- **Classic Mode** - Original game balance
- **Enhanced Mode** - Rebalanced statistics with improvements
- Switch between modes instantly to compare stats

## Getting Started

### Requirements
- Python 3.6+
- A modern web browser (Chrome, Firefox, Edge, Safari)
- The DTA game files (Rules.ini and Enhance.ini)

### Quick Start

1. **Generate the Data File** (if `game_data.json` doesn't exist)
   ```bash
   cd "c:\DTA\Dawn of the Tiberium Age"
   python parse_game_data.py
   ```

2. **Start the Web Server**
   ```bash
   python -m http.server 8000
   ```

3. **Open the Dashboard**
   - Open your browser and navigate to: `http://localhost:8000`
   - You should see the dashboard load with all game entities

4. **Explore the Data**
   - Use the search bar to find any unit or structure
   - Click on cards to view detailed stats
   - Toggle between Classic and Enhanced modes
   - Use tabs to filter by entity type

## File Structure

```
c:\DTA\Dawn of the Tiberium Age\
├── index.html                 # Main dashboard UI
├── game_data.json            # Parsed game data (auto-generated)
├── parse_game_data.py        # Script to generate game_data.json
├── verify_data.py            # Data verification utility
└── INI/
    └── Base/
        ├── Rules.ini         # Classic game rules
        └── Enhance.ini       # Enhanced mode overrides
```

## How It Works

### Data Parsing
The `parse_game_data.py` script:
1. Reads `Rules.ini` to extract all game entities and their base stats
2. Reads `Enhance.ini` to get enhanced mode overrides
3. Extracts specific properties: weapons, armor, abilities, etc.
4. Organizes data into JSON format for the web dashboard
5. Creates separate entries for both Classic and Enhanced modes

### Stats Organization
Each entity displays stats in these categories:

| Category | Includes |
|----------|----------|
| **General** | Name, Cost, Strength (HP), Tech Level required |
| **Movement & Defense** | Speed, Sight range, Armor type |
| **Weapons** | Primary weapon, Secondary weapon, Elite upgrade |
| **Abilities** | Veterancy abilities, trainability, special features |
| **Special** | Owner restrictions, building type, power drain/output |

## Usage Examples

### Finding a Specific Unit
1. Type the unit name (e.g., "Apache") or ID (e.g., "E1") in the search box
2. Results appear immediately
3. Click on the unit card to see full details

### Comparing Classic vs Enhanced Stats
1. Select any unit
2. Two buttons appear: "Classic Stats" and "Enhanced Stats"
3. Click to instantly switch between modes
4. Stats will update to show the differences

### Filtering by Type
1. Use the "Entity Type" dropdown to filter
2. Choose from: Infantry, Vehicles, Aircraft, Buildings
3. Results update in real-time

### Viewing by Category
1. Use the tabs at the top to quickly jump to specific types
2. "All Entities" shows everything
3. Each tab shows stats for that category only

## Stats Legend

### Unit Stats

**Cost** - Credits required to build/train
- **Infantry**: Usually 100-600
- **Vehicles**: Usually 300-2500
- **Aircraft**: Usually 1200-2000

**Strength** - Hit points (HP) the unit has
- **Infantry soldiers**: 250-2000 HP
- **Tanks**: 1000-7600 HP
- **Aircraft**: 1000-1300 HP

**Speed** - How fast the unit moves
- **Infantry**: 4-14 cells/time
- **Vehicles**: 3-14 cells/time
- **Aircraft**: 20 cells/time

**Sight** - How far the unit can see on the map
- **Infantry**: 3-6 cells
- **Vehicles**: 3-6 cells
- **Aircraft**: Varies

**Armor** - Damage resistance type
- **None** - No resistance
- **Light** - 75% damage taken
- **Medium** - 60% damage taken
- **Heavy** - 50% damage taken
- **Wood** - Low resistance
- **Steel** - High resistance

**Trainable** - Can the unit gain veterancy?
- **Yes** - Unit levels up with experience
- **No** - Unit stat locked at current level

### Weapons

**Primary=XXX** - Main weapon, always equipped
**Secondary=XXX** - Secondary weapon for multi-purpose units
**Elite=XXX** - Upgraded primary weapon when reaching Elite status

### Special Abilities

**Veteran Abilities** - Gained at first veterancy level
- Examples: STRONGER, SIGHT, FASTER, FIREPOWER

**Elite Abilities** - Gained at elite level (cumulative with veteran)
- Examples: SELF_HEAL, TIBERIUM_PROOF, RADAR_INVISIBLE

## Customization

### Modifying the Parse Script
To change how data is extracted or formatted:

```python
# In parse_game_data.py, customize the format_entity_data() function
# Add new categories or properties as needed
```

### Styling the Dashboard
The dashboard uses CSS variables for easy customization. Edit the `:root` section in `index.html`:

```css
:root {
    --color-primary: #1a1a2e;
    --color-accent: #e94560;
    --color-text: #eaeaea;
    /* etc... */
}
```

## Troubleshooting

### "No entities found" or blank page
- Ensure `game_data.json` exists in the same directory as `index.html`
- Run `python parse_game_data.py` to regenerate the data
- Check browser console (F12) for errors

### Web server won't start
```bash
# Try a different port
python -m http.server 8080

# Or use Python's built-in server module
python -m http.server --directory . 8000
```

### Data not updating after INI changes
- Delete `game_data.json`
- Run `python parse_game_data.py` again
- Refresh the browser

## Technical Details

### JSON Data Structure
```json
{
  "game": "Dawn of the Tiberium Age",
  "modes": {
    "classic": {
      "infantry": { "E1": {...}, "E2": {...} },
      "vehicles": { "JEEP": {...}, ... },
      "aircraft": { "ORCA": {...}, ... },
      "buildings": { "PYLE": {...}, ... }
    },
    "enhanced": { /* same structure */ }
  }
}
```

### Entity Object Format
```json
{
  "ID": "E1",
  "Name": "Minigunner",
  "Type": "Infantry",
  "IsEnhanced": false,
  "General": { "Name": "...", "Cost": "...", ... },
  "Movement & Defense": { "Speed": "...", ... },
  "Weapons": { "Primary": "...", ... },
  "Abilities": { "Trainable": "yes", ... },
  "Special": { ... },
  "RawData": { /* all original INI values */ }
}
```

## Known Limitations

- Some entries in entity lists may be placeholders or debug units
- Weapons are displayed by ID; full weapon stats would require parsing weapon.ini
- Vehicle count includes all entries; some may be internal/unused

## Future Enhancements

Potential improvements:
- Weapon statistics display
- Building production lists
- Unit veterancy progression charts
- Equipment and upgrades information
- Cost-efficiency calculations
- Build-time information
- Comparison tool for multiple units

## Credits

- **DTA Development Team** - For the game and INI file structure
- **Game Data** - Extracted from Rules.ini and Enhance.ini
- **Dashboard** - Created as a fan utility

## Support

For issues or questions:
1. Check this README
2. Verify all files are in the correct location
3. Run the data parser script again
4. Check browser console for JavaScript errors
5. Ensure Python and browser compatibility

---

**Last Updated**: February 2026  
**Games Covered**: Dawn of the Tiberium Age  
**Data Coverage**: 820 total entities across 4 categories
