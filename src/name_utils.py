# -*- coding: utf-8 -*-
import re
import string

# Map target aliases to canonical names
targettab = {
    # MPF
    'B._Bill': 'Barnacle_Bill',
    'Bakers_Bench': "Baker's_Bench",
    'Bambam': 'Bam_Bam',
    'Bamm_Bamm': 'Bam_Bam',
    'Fat_Top': 'Flat_Top',
    'Garak': 'Garrak',
    'Ga_Rrak': 'Garrak',
    'H._Dome': 'Half_Dome',
    'Hobbs': 'Hobbes',
    'Mini-Matterhorn': 'Mini_Matterhorn',
    'Mm': 'Mini_Matterhorn',
    'Poohbear': 'Pooh_Bear',
    'Scooby': 'Scooby_Doo',
    'Souffl': 'Soufflé',
    'Souffle': 'Soufflé',
    "Souffle'": 'Soufflé',
    'Soufle': 'Soufflé',
    # PHX
    'Bb': 'Baby_Bear',
    'Bc': 'Burning_Coals',
    'Bears_Lodge': "Bear's_Lodge",
    'Dg': 'Dodo_Goldilocks',
    'D_G': 'Dodo_Goldilocks',
    'Dodo': 'Dodo_Goldilocks',
    'Dodogoldilocks': 'Dodo_Goldilocks',
    'Dodo-goldilocks': 'Dodo_Goldilocks',
    'Dodogoldilocks_Trench': 'Dodo_Goldilocks_Trench',
    'Dodo-goldilocks_Trench': 'Dodo_Goldilocks_Trench',
    'Dodo-Goldilocks_Trench': 'Dodo_Goldilocks_Trench',
    'Dodo_Trench': 'Dodo_Goldilocks_Trench',
    'Lamancha': 'La_Mancha',
    'Mamma_Bear': 'Mama_Bear',
    'Mancha': 'La_Mancha',
    'Rr': 'Rosy_Red',
    'Rr1': 'Rosy_Red',
    'Rr2': 'Rosy_Red',
    'Ww': 'Wicked_Witch'
    }

# Elements symbol table
symtab = {
    'Ac': 'Actinium',
    'Ag': 'Silver',
    'Al': 'Aluminum',
    'Am': 'Americium',
    'Ar': 'Argon',
    'As': 'Arsenic',
    'At': 'Astatine',
    'Au': 'Gold',
    'B': 'Boron',
    'Ba': 'Barium',
    'Be': 'Beryllium',
    'Bh': 'Bohrium',
    'Bi': 'Bismuth',
    'Bk': 'Berkelium',
    'Br': 'Bromine',
    'C': 'Carbon',
    'Ca': 'Calcium',
    'Cd': 'Cadmium',
    'Ce': 'Cerium',
    'Cf': 'Californium',
    'Cl': 'Chlorine',
    'Cm': 'Curium',
    'Cn': 'Copernicium',
    'Co': 'Cobalt',
    'Cr': 'Chromium',
    'Cs': 'Cesium',
    'Cu': 'Copper',
    'Db': 'Dubnium',
    'Ds': 'Darmstadtium',
    'Dy': 'Dysprosium',
    'Er': 'Erbium',
    'Es': 'Einsteinium',
    'Eu': 'Europium',
    'F': 'Fluorine',
    'Fe': 'Iron',
    'Fl': 'Flerovium',
    'Fm': 'Fermium',
    'Fr': 'Francium',
    'Ga': 'Gallium',
    'Gd': 'Gadolinium',
    'Ge': 'Germanium',
    'H': 'Hydrogen',
    'He': 'Helium',
    'Hf': 'Hafnium',
    'Hg': 'Mercury',
    'Ho': 'Holmium',
    'Hs': 'Hassium',
    'I': 'Iodine',
    'In': 'Indium',
    'Ir': 'Iridium',
    'K': 'Potassium',
    'Kr': 'Krypton',
    'La': 'Lanthanum',
    'Li': 'Lithium',
    'Lr': 'Lawrencium',
    'Lu': 'Lutetium',
    'Lv': 'Livermorium',
    'Md': 'Mendelevium',
    'Mg': 'Magnesium',
    'Mn': 'Manganese',
    'Mo': 'Molybdenum',
    'Mt': 'Meitnerium',
    'N': 'Nitrogen',
    'Na': 'Sodium',
    'Nb': 'Niobium',
    'Nd': 'Neodymium',
    'Ne': 'Neon',
    'Ni': 'Nickel',
    'No': 'Nobelium',
    'Np': 'Neptunium',
    'O': 'Oxygen',
    'Os': 'Osmium',
    'P': 'Phosphorus',
    'Pa': 'Protactinium',
    'Pb': 'Lead',
    'Pd': 'Palladium',
    'Pm': 'Promethium',
    'Po': 'Polonium',
    'Pr': 'Praseodymium',
    'Pt': 'Platinum',
    'Pu': 'Plutonium',
    'Ra': 'Radium',
    'Rb': 'Rubidium',
    'Re': 'Rhenium',
    'Rf': 'Rutherfordium',
    'Rg': 'Roentgenium',
    'Rh': 'Rhodium',
    'Rn': 'Radon',
    'Ru': 'Ruthenium',
    'S': 'Sulfur',
    'Sb': 'Antimony',
    'Sc': 'Scandium',
    'Se': 'Selenium',
    'Sg': 'Seaborgium',
    'Si': 'Silicon',
    'Sm': 'Samarium',
    'Sn': 'Tin',
    'Sr': 'Strontium',
    'Ta': 'Tantalum',
    'Tb': 'Terbium',
    'Tc': 'Technetium',
    'Te': 'Tellurium',
    'Th': 'Thorium',
    'Ti': 'Titanium',
    'Tl': 'Thallium',
    'Tm': 'Thulium',
    'U': 'Uranium',
    'Uuo': 'Ununoctium',
    'Uup': 'Ununpentium',
    'Uus': 'Ununseptium',
    'Uut': 'Ununtrium',
    'V': 'Vanadium',
    'W': 'Tungsten',
    'Xe': 'Xenon',
    'Y': 'Yttrium',
    'Yb': 'Ytterbium',
    'Zn': 'Zinc',
    'Zr': 'Zirconium'
}

def canonical_name(name):
    """
    Gets canonical name: title case
    :param name - name whose canonical name is to be looked up
    :return canonical name
    """
    name = name.strip()
    if len(name) <= 3 and name.title() in symtab:
        return symtab[name.title()]
    else:
        return string.capwords(name)

def canonical_target_name(name):
    """
    Gets canonical target name: title case, replace spaces and dashes
    with underscore.  Aliases are expanded using targettab.
    :param name - name whose canonical name is to be looked up
    :return canonical name
    """
    name = name.strip()
    # Remove whitespace, dashes, and underscores
    strip_ws = re.sub(r'[\s_-]+', ' ', name)
    # Use capwords so e.g. Bear's Lodge does not become Bear'S Lodge
    # and replace spaces with underscores in final version
    name = string.capwords(strip_ws).replace(' ', '_')
    
    if name in targettab:
        return targettab[name].decode('utf8')
    else:
        return name

def canonical_property_name(name):
    """
    Gets canonical name for a property: lower-case.
    :param name - name whose canonical name is to be looked up
    :return canonical name
    """
    name = name.strip()
    return name.lower()


