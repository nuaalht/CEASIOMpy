"""
CEASIOMpy: Conceptual Aircraft Design Software.

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This module contains the tools used for data creation and manipulation of the
Optimisation and PredictiveTool modules.

Python version: >=3.6

| Author : Vivien Riolo
| Creation: 2020-05-26
| Last modification: 2020-05-26

TODO
----
    * Solve the accronym problematic

"""

#==============================================================================
#   IMPORTS
#==============================================================================
import numpy as np
import openmdao.api as om
import matplotlib.pyplot as plt
import pandas as pd
import tigl3.configuration

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

#==============================================================================
#   GLOBALS
#==============================================================================

#==============================================================================
#   CLASSES
#==============================================================================

#==============================================================================
#   FUNCTIONS
#==============================================================================

### --------------- MISCELANEOUS --------------- ###
# -------------------------------------------------#

def get_aeromap_path(module_list):
    """Return xpath of selected aeromap.

    Check the modules that will be run in the optimisation routine to specify
    the path to the correct aeromap in the CPACS file.

    Args:
        module_list (lst) : list of the modules that are run in the routin

    Returns:
        xpath (str) : Xpath to the aeromap that is used for the routine
    """

    PYTORNADO_XPATH = '/cpacs/toolspecific/pytornado'

    SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

    xpath = 'None'

    for module in module_list:
        if module == 'SU2Run':
            log.info('Found SU2 analysis')
            xpath = SU2_XPATH
        elif module == 'PyTornado':
            log.info('Found PyTornado analysis')
            xpath = PYTORNADO_XPATH
    return xpath


def estimate_volume(tigl):
    """Estimate aircraft volume.

    First approximation of the aircraft fuselage volume. Temporary solution
    to the unsolved issue of calling fuselageGetVolume multiple times.
    Update : For the moment the get_width/get_height functions also encounter
    this isssue, another solution has to be found.

    Args:
        tigl (tigl3 handle) : Handle of the current CPACS

    Returns:
        volume (float) : Estimated value of the volume for the current
        aircraft

    """
    mgr =  tigl3.configuration.CCPACSConfigurationManager_get_instance()

    aircraft = mgr.get_configuration(tigl._handle.value)
    fuselage = aircraft.get_fuselages().get_fuselage(1)

    # Retrieve ctigl element from the middle of the plane
    snb = round(fuselage.get_section_count()/2)
    sec = fuselage.get_section(snb)
    el = sec.get_section_element(1)
    cel = el.get_ctigl_section_element()

    volume = (cel.get_width()+cel.get_height())**2*fuselage.get_length()/16*3.14
    return volume


### --------------- FUNCTIONS FOR POST-PROCESSING --------------- ###
# ------------------------------------------------------------------#


def display_results(prob, optim_var_dict, Rt):
    """Display variable history on terminal.

    All the variables that were used in the routine and that saved in
    optim_var_dict are displayed on terminal with their bounds and their value
    history.

    Args:
        Rt (class) : Routine parameters
        prob (class) : OpenMDAO problem object
        optim_var_dict (dict) : Variable dictionnary

    Returns:
        None.

    """
    log.info('=========================================')
    log.info('min = ' + str(prob['objective.{}'.format(Rt.objective)]))

    for name, (val_type, listval, minval, maxval, getcommand, setcommand) in optim_var_dict.items():
        if val_type == 'des':
            log.info(name + ' = ' + str(prob['indeps.'+name]) + '\n Min :' + str(minval) + ' Max : ' + str(maxval))

    log.info('Variable history :')

    for name, (val_type, listval, minval, maxval, getcommand, setcommand) in optim_var_dict.items():
        if val_type == 'des':
            log.info(name + ' => ' + str(listval))
    log.info('=========================================')


def read_results(optim_dir_path):
    """Read sql file and converts data to dataframe.

    This is mainly to facilitate data manipulation by avoiding dealing with
    the pre-implemented CaseReader dictionnary whose architecture is not
    convenient.

    Args:
        optim_dir_path (str) : Path to the SQL file directory.

    Returns:
        df (DataFrame) : Contains all parameters of the routine

    """
    # Read recorded options
    cr = om.CaseReader(optim_dir_path + '/Driver_recorder.sql')
    # driver_cases = cr.list_cases('driver') (If  multiple recorders)

    cases = cr.get_cases()

    # Initiates dictionnaries
    case1 = cr.get_case(0)
    obj = {}
    des = {}
    const = {}

    # Rename keys
    for k, v in dict(case1.get_objectives()).items():
        obj[k.replace('objective.','')] = v
    for k, v in dict(case1.get_design_vars()).items():
        des[k.replace('indeps.','')] = v
    for k, v in dict(case1.get_constraints()).items():
        if 'const' in k:
            const[k.replace('const.','')] = v

    # Retrieve data from SQL file
    for case in cases:
        for key, val in case.get_objectives().items():
            key = key.replace('objective.','')
            obj[key] = np.append(obj[key], val)

        for key, val in case.get_design_vars().items():
            key = key.replace('indeps.','')
            des[key] = np.append(des[key], val)

        for key, val in case.get_constraints().items():
            if 'const' in key:
                key = key.replace('const.','')
                const[key] = np.append(const[key], val)


    df_o = pd.DataFrame(obj).transpose()
    df_d = pd.DataFrame(des).transpose()
    df_c = pd.DataFrame(const).transpose()

    df_o.insert(0, 'type', 'obj')
    df_d.insert(0, 'type', 'des')
    df_c.insert(0, 'type', 'const')

    return pd.concat([df_o,df_d,df_c], axis=0)


def save_results(optim_dir_path):
    """Save routine results to CSV.

    Add the variable history to the CSV paramater file and save it to the
    corresponding working directory. This comes in handy for generating
    data for surrogate models.

    Args:
        optim_dir_path (str) : Path to the routine working directory.

    Returns:
        None.

    """
    log.info('Variables will be saved')

    # Get variable infos
    df = read_results(optim_dir_path)
    # df = df.transpose()

    # # Generate dictionary with variable history
    # values = {name:lv[1:] for name, (vt, lv, minv, maxv, gc, sc) in results.items()}
    # print(values)
    # df2 = pd.DataFrame.from_dict(values)

    # df = df.append(df2).transpose()

    df.to_csv(optim_dir_path+'/Variable_history.csv', index=True, na_rep='-')


### --------------- FUNCTIONS FOR PLOTTING --------------- ###
# -----------------------------------------------------------#

def plot_results(optim_dir_path, routine_type):
    """Generate plots of the routine.

    Draw plots to vizualize the data. The evolution of each problem parameter
    appears in a subplot.

    Args:
        optim_dir_path (str) : Path to the routine working directory.
        routine_type (str) : Type of the routine, can be DoE or Optim

    Returns:
        None.

    """
    df = read_results(optim_dir_path)

    obj = [i for i in df.index if df['type'][i] == 'obj']
    des = [i for i in df.index if df['type'][i] == 'des']
    const = [i for i in df.index if df['type'][i] == 'const']

    df.pop('type')
    df = df.transpose()
    nbC = min(len(des),5)
    df.plot(subplots=True, layout=(-1,nbC))
    plt.show()
    if routine_type.upper() == 'DOE':
        gen_plot(df, obj, des)
        gen_plot(df, obj, const)


def gen_plot(df, yvars, xvars):
    """Generate scatter plot

    Generate a scatter plot from a dataframe based on its column entries.

    Args:
        df (DataFrame) : Contains the data.
        yvars (lst) : Label of the functions in df.
        xvars (lst) : Label of the variables in df.

    Returns:
        None.

    """
    nbC = min(len(xvars),5)
    nbR = int(len(yvars) * np.ceil(len(xvars)/nbC))
    r = 0
    c = 1
    for o in yvars:
        for d in xvars:
            plt.subplot(nbR,nbC,c+r*nbC)
            plt.scatter(df[d],df[o])
            plt.xlabel(d)
            if c == 1:
                plt.ylabel(o)
            c += 1
            if c > nbC:
                r += 1
                c = 0
        r += 1
        c = 0
    plt.show()


### --------------- FUNCTIONS FOR OPTIMISATION PARAMETERS --------------- ###
# --------------------------------------------------------------------------#

def is_digit(value):
    """Check if a string value is a float.

    This function comes in as more flexible than the implementde isdigit()
    function, as it also enbales to check for floats and not just integers.

    Args:
        value (str) : Chain of character that may contain something else than
        a digit or a dot.

    Returns:
        Boolean.

    """
    if type(value) is list:
        return False
    else:
        try:
            float(value)
            return True
        except:
            return False


def accronym(name):
    """Return accronym of a name. (EXPERIMENTAL FEATURE)

    In order to detect the values specified by the user as accronyms, the
    complete name of a variable is decomposed and the first letter of
    each word is taken.

    Ex : 'maximal take off mass' -> 'mtom'

    Args:
        name (str) : Name of a variable.

    Returns:
        accro (str) : Accronym of the name.

    """
    full_name = name.split('_')
    accro = ''
    for word in full_name:
        if word.lower() in ['nb']:
            accro += word
        else:
            accro += word[0]
    log.info('Accronym : ' + accro)
    return accro


def add_type(entry, outputs, objective, var):
    """Add variable type to the dictionary.

    Verifies if the entry of a module is listed in its outputs. If it is the
    case it will be set as a constraint ('const') by default, except if
    the entry is found in the expression of the objective function where it is
    then labelled as 'obj'. Else it will be marked as a design variable as it
    belongs to the module input.

    Args:
        name (str) : Name of a variable
        outputs (lst) : List of the modules' output
        objective (str) : Objective function
        var (dct) : Variable dictionary

    Returns:
        None.

    """
    if entry in outputs:
        if type(entry) != str:
            entry = entry.var_name
        if entry in objective:
            var['type'].append('obj')
            log.info('Added type : obj')
        else:
            var['type'].append('const')
            log.info('Added type : const')
    else:
        var['type'].append('des')
        log.info('Added type : des')

def add_bounds(name, value, var):
    """Add upper and lower bound.

    20% of the initial value is added and substracted to create the
    boundaries.

    Args:
    name (str) : Name of a variable
    value (str) : Initial value of the variable
    var (dct) : Variable dictionary

    Returns:
        None.

    """
    if value in ['False', 'True']:
            lower = '-'
            upper = '-'
    elif value.isdigit():
        value = int(value)
        lower = round(value-abs(0.2*value))
        upper = round(value+abs(0.2*value))
        if lower == upper:
            lower -= 1
            upper += 1
    else:
        value = float(value)
        lower = round(value-abs(0.2*value))
        upper = round(value+abs(0.2*value))
        if lower == upper:
            lower -= 1.0
            upper += 1.0

    var['min'].append(lower)
    var['max'].append(upper)
