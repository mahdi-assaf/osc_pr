from drivers.juniper.driver import JuniperIla
from drivers.yokogawa.osa import YokogawaOsa
from drivers.jds.switch import JDSSwitch
from drivers.hp.voa import HPVoa
from drivers.cisco.driver import CiscoEDFA17, CiscoEDFA35

DRIVER_DICT = {
    "amplifier": {
        "edfa": {
            "juniper": JuniperIla,
            "cisco35": CiscoEDFA35,
            "cisco17": CiscoEDFA17
        }
    },
    "instrument": {
        "osa": {
            "yokogawa": YokogawaOsa
        },
        "switch": {
            "jds": JDSSwitch
        },
        "voa": {
            "hp": HPVoa
        }
    }
}
