"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Function to evaluate the Oprating Empty Mass (OEM) from the maximum take of mass.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-09-27
| Last modifiction: 2019-02-20
"""


#=============================================================================
#   IMPORTS
#=============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])


#==============================================================================
#   CLASSES
#==============================================================================

"""
 InsideDimensions class, can be found on the InputClasses folder inside the
 weightconvclass.py script.
"""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def operating_empty_mass_estimation(mtom, fuse_length, fuse_width, wing_area,\
                                    wing_span, TURBOPROP):
    """ The function estimates the operating empty mass (OEM)

    Source: Raymer, D.P. "Aircraft design: a conceptual approach"
            AIAA educational Series, Fourth edition (2006).

    INPUT
    (float)     mtom            --Arg.: Maximum take off mass [kg].
    (float)     fuse_length     --Arg.: Fuselage length [m].
    (float)     fuse_width      --Arg.: Fuselage width [m].
    (float)     wing_area       --Arg.: Wing area [m^2].
    (float)     wing_span       --Arg.: Wing span [m].
    (boolean)   TURBOPROP       --Arg.: True if the the engines are turboprop
                                        False otherwise.
    OUTPUT
    (float)     oem             --Out.: Operating empty mass [kg].
    """
    G = 9.81     # [m/s^2] Acceleration of gravity.
    KC = 1.04    # [-] Wing with variable sweep (1.0 otherwhise).
    if TURBOPROP:
        C = -0.05 # [-] General aviation twin turboprop
        if fuse_length < 15.00:
            A = 0.96
        elif fuse_length < 30.00:
            A = 1.07
        else:
            A = 1.0
    else:
        C = -0.08 # [-] General aviation twin engines
        if fuse_length < 30.00:
            A = 1.45
        elif fuse_length < 35.00:
                A = 1.63
        elif fuse_length < 60.00:
            if wing_span > 61:
                A = 1.63
            else:
                A = 1.57
        else:
            A = 1.63
    oem = round((A * KC * (mtom*G)**(C)) * mtom,3)
    return oem


##=============================================================================
#   MAIN
#==============================================================================

if __name__ == '__main__':
    log.warning('###########################################################')
    log.warning('#### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ####')
    log.warning('###########################################################')
