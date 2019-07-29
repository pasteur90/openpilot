#!/usr/bin/env python
from cereal import car
from selfdrive.can.parser import CANParser
from selfdrive.car.hyundai.values import DBC
import time

def get_radar_can_parser(CP):

  signals = [
    # sig_name, sig_address, default
    ("ACC_ObjStatus", "SCC11", 0),
    ("ACC_ObjLatPos", "SCC11", 0),
    ("ACC_ObjDist", "SCC11", 0),
    ("ACC_ObjRelSpd", "SCC11", 0),
  ]

  checks = [
    # address, frequency
    ("SCC11", 50),
  ]

  return CANParser(DBC[CP.carFingerprint]['pt'], signals, checks, 0)

class RadarInterface(object):
  def __init__(self, CP):
    # radar
    self.pts = {}
    self.delay = 0.1
    self.rcp = get_radar_can_parser(CP)
    self.trigger_msg = self.rcp.vl["SCC11"]['ACC_ObjStatus']
    self.updated_messages = set()

  def update(self, can_strings):
    if self.no_radar:
      ret = car.RadarData.new_message()
      time.sleep(0.05)  # radard runs on RI updates
      return ret

    tm = int(sec_since_boot() * 1e9)
    vls = self.rcp.update_strings(tm, can_strings)
    self.updated_messages.update(vls)

    if self.trigger_msg not in self.updated_messages:
      return None

    rr =  self._update(self.updated_messages)
    self.updated_messages.clear()

    return rr
