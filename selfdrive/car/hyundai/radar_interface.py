#!/usr/bin/env python
import time
from cereal import car
from selfdrive.can.parser import CANParser
from selfdrive.car.hyundai.values import DBC
from common.realtime import sec_since_boot

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
    self.updated_messages = set()
    self.trigger_msg = 0x420
    self.track_id = 0
    self.no_radar = False

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
  
  
  def _update(self, updated_messages):
    ret = car.RadarData.new_message()
    cpt = self.rcp.vl
    errors = []
    if not self.rcp.can_valid:
      errors.append("canError")
    ret.errors = errors

    valid = cpt["SCC11"]['ACC_ObjStatus']
    if valid:
      for ii in range(3):
        if ii not in self.pts:
          self.pts[ii] = car.RadarData.RadarPoint.new_message()
          self.pts[ii].trackId = self.track_id
          self.track_id += 1
        self.pts[ii].dRel = cpt["SCC11"]['ACC_ObjDist']  # from front of car
        self.pts[ii].yRel = -cpt["SCC11"]['ACC_ObjLatPos']  # in car frame's y axis, left is negative
        self.pts[ii].vRel = cpt["SCC11"]['ACC_ObjRelSpd']
        self.pts[ii].aRel = float('nan')
        self.pts[ii].yvRel = float('nan')
        self.pts[ii].measured = True

    ret.points = self.pts.values()
    return ret
